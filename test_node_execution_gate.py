import asyncio
import contextlib
import contextvars
import time
import unittest
from types import SimpleNamespace

import node_execution_gate
from node_execution_gate import install_comfy_scheduler_wait, serialize_registered_nodes


_test_context = contextvars.ContextVar("dapao_test_node_context", default=None)


@contextlib.contextmanager
def CurrentNodeContext(prompt_id, node_id, list_index):
    token = _test_context.set(SimpleNamespace(
        prompt_id=prompt_id,
        node_id=node_id,
        list_index=list_index,
    ))
    try:
        yield
    finally:
        _test_context.reset(token)


class _AsyncProbe:
    FUNCTION = "run"

    async def run(self, name, timeline, delay=0.04):
        timeline.append((name, "start", time.monotonic()))
        await asyncio.sleep(delay)
        timeline.append((name, "end", time.monotonic()))
        return (name,)


class _SyncProbe:
    FUNCTION = "run"

    def run(self, name, timeline, delay=0.04):
        timeline.append((name, "start", time.monotonic()))
        time.sleep(delay)
        timeline.append((name, "end", time.monotonic()))
        return (name,)


class NodeExecutionGateTests(unittest.TestCase):
    def setUp(self):
        node_execution_gate.get_executing_context = _test_context.get
        serialize_registered_nodes({"async": _AsyncProbe, "sync": _SyncProbe})

    def test_different_nodes_are_serialized(self):
        timeline = []
        probe = _AsyncProbe()

        async def scenario():
            async def invoke(node_id, name):
                with CurrentNodeContext("prompt", node_id, 0):
                    return await probe.run(name, timeline)

            return await asyncio.gather(invoke("node-a", "a"), invoke("node-b", "b"))

        self.assertEqual(asyncio.run(scenario()), [("a",), ("b",)])
        events = [(name, event) for name, event, _stamp in timeline]
        valid_orders = [
            [('a', 'start'), ('a', 'end'), ('b', 'start'), ('b', 'end')],
            [('b', 'start'), ('b', 'end'), ('a', 'start'), ('a', 'end')],
        ]
        self.assertIn(events, valid_orders)

    def test_same_node_list_items_still_overlap(self):
        timeline = []
        probe = _AsyncProbe()

        async def scenario():
            async def invoke(index):
                with CurrentNodeContext("prompt", "same-node", index):
                    return await probe.run(str(index), timeline, 0.06)

            started = time.monotonic()
            result = await asyncio.gather(invoke(0), invoke(1), invoke(2))
            return result, time.monotonic() - started

        result, elapsed = asyncio.run(scenario())
        self.assertEqual(result, [("0",), ("1",), ("2",)])
        self.assertLess(elapsed, 0.14)

    def test_sync_node_is_also_serialized_and_keeps_output(self):
        timeline = []
        async_probe = _AsyncProbe()
        sync_probe = _SyncProbe()

        async def scenario():
            async def invoke_async():
                with CurrentNodeContext("prompt", "async-node", 0):
                    return await async_probe.run("async", timeline)

            async def invoke_sync():
                with CurrentNodeContext("prompt", "sync-node", 0):
                    return await sync_probe.run("sync", timeline)

            return await asyncio.gather(invoke_async(), invoke_sync())

        self.assertEqual(asyncio.run(scenario()), [("async",), ("sync",)])
        events = [(name, event) for name, event, _stamp in timeline]
        self.assertEqual(events, [('async', 'start'), ('async', 'end'),
                                  ('sync', 'start'), ('sync', 'end')])

    def test_scheduler_waits_for_all_current_node_list_tasks(self):
        class RegisteredNode:
            FUNCTION = "run"

        async def original_get_output_data(*_args, **_kwargs):
            async def item(value):
                await asyncio.sleep(0.04)
                return (value,)

            return [asyncio.create_task(item(1)), asyncio.create_task(item(2))], {}, False, True

        async def resolve(results):
            return await asyncio.gather(*results)

        fake_execution = SimpleNamespace(
            get_output_data=original_get_output_data,
            resolve_map_node_over_list_results=resolve,
            get_output_from_returns=lambda results, _obj: ([item[0] for item in results], {}, False),
        )
        install_comfy_scheduler_wait({"registered": RegisteredNode}, fake_execution)

        async def scenario():
            started = time.monotonic()
            result = await fake_execution.get_output_data("prompt", "node", RegisteredNode(), {})
            return result, time.monotonic() - started

        result, elapsed = asyncio.run(scenario())
        self.assertEqual(result, ([1, 2], {}, False, False))
        self.assertGreaterEqual(elapsed, 0.035)
        self.assertLess(elapsed, 0.09)


if __name__ == "__main__":
    unittest.main()
