"""Serialize different dapao nodes without disabling per-node list mapping."""

from __future__ import annotations

import asyncio
import functools
import inspect
import threading
import weakref
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

try:
    from comfy_execution.utils import get_executing_context
except ImportError:  # Allows isolated unit tests outside a full ComfyUI install.
    get_executing_context = None


GroupKey = Tuple[str, str]


@dataclass
class _LoopGate:
    condition: asyncio.Condition = field(default_factory=asyncio.Condition)
    active_group: Optional[GroupKey] = None
    active_calls: int = 0

    async def enter(self, group: GroupKey) -> None:
        async with self.condition:
            await self.condition.wait_for(
                lambda: self.active_group is None or self.active_group == group
            )
            if self.active_group is None:
                self.active_group = group
            self.active_calls += 1

    async def leave(self, group: GroupKey) -> None:
        async with self.condition:
            if self.active_group != group:
                return
            self.active_calls -= 1
            if self.active_calls == 0:
                self.active_group = None
                self.condition.notify_all()


_loop_gates: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, _LoopGate]" = (
    weakref.WeakKeyDictionary()
)
_loop_gates_lock = threading.Lock()


def _gate_for_running_loop() -> _LoopGate:
    loop = asyncio.get_running_loop()
    with _loop_gates_lock:
        gate = _loop_gates.get(loop)
        if gate is None:
            gate = _LoopGate()
            _loop_gates[loop] = gate
        return gate


def _current_group(instance: Any) -> GroupKey:
    context = get_executing_context() if get_executing_context is not None else None
    if context is not None:
        # 不包含 list_index：同一节点映射出的全部列表项属于同一个并发组。
        return str(context.prompt_id), str(context.node_id)
    return "outside-comfy", str(id(instance))


async def _run_original(function, instance, args, kwargs):
    if inspect.iscoroutinefunction(function):
        return await function(instance, *args, **kwargs)
    return await asyncio.to_thread(function, instance, *args, **kwargs)


def serialize_registered_nodes(node_class_mappings: Dict[str, type]) -> None:
    """Serialize different node IDs while preserving concurrency inside one node."""

    for node_class in set(node_class_mappings.values()):
        function_name = getattr(node_class, "FUNCTION", None)
        if not function_name:
            continue
        original = getattr(node_class, function_name, None)
        if original is None or getattr(original, "_dapao_node_execution_gate", False):
            continue

        @functools.wraps(original)
        async def guarded(self, *args, __original=original, **kwargs):
            group = _current_group(self)
            gate = _gate_for_running_loop()
            await gate.enter(group)
            try:
                return await _run_original(__original, self, args, kwargs)
            finally:
                await gate.leave(group)

        guarded._dapao_node_execution_gate = True
        setattr(node_class, function_name, guarded)


def install_comfy_scheduler_wait(
    node_class_mappings: Dict[str, type], execution_module=None
) -> None:
    """Make ComfyUI finish one dapao node before staging the next node.

    ComfyUI normally returns from an async node as soon as its tasks are created,
    marks that node pending, and immediately lights up another ready node.  Waiting
    here lets all mapped calls of the current node run concurrently, but prevents
    the scheduler from staging another node until this whole node is complete.
    """

    for node_class in set(node_class_mappings.values()):
        node_class._DAPAO_WAIT_FOR_NODE_COMPLETION = True

    if execution_module is None:
        import execution as execution_module

    current = execution_module.get_output_data
    if getattr(current, "_dapao_scheduler_wait", False):
        return

    @functools.wraps(current)
    async def get_output_data_waiting(*args, **kwargs):
        result = await current(*args, **kwargs)
        obj = args[2] if len(args) > 2 else kwargs.get("obj")
        if not getattr(obj, "_DAPAO_WAIT_FOR_NODE_COMPLETION", False):
            return result

        return_values, _output_ui, _has_subgraph, has_pending_tasks = result
        if not has_pending_tasks:
            return result

        completed = await execution_module.resolve_map_node_over_list_results(return_values)
        output, ui, has_subgraph = execution_module.get_output_from_returns(completed, obj)
        return output, ui, has_subgraph, False

    get_output_data_waiting._dapao_scheduler_wait = True
    execution_module.get_output_data = get_output_data_waiting
