# `image-prompt-specs.jsonl` 填写模板

首行是 `sources` 声明记录，之后每行一个候选规格对象，用于接受前预览；示例值不是默认答案。删除不适用字段，不要添加
媒体任务、供应商或接口字段。上游引用默认绑定准确的已接受快照；只有与本对象同次发布的目标才写
`authority:candidate`。对象接受状态由事务生命周期记录，不能靠改状态字样伪造。

## 首行：`sources` 声明

本文件用到的每个上游快照在这里声明一次，键取产物文件名（`characters`、`looks`、`props`），
在本文件内唯一且稳定：

```json
{
  "record_type": "sources",
  "schema_version": "1.0.0",
  "sources": {
    "<identity-owner>": {
      "owner": "short-drama-assets",
      "artifact": "设定集/<identity-owner-file>.jsonl"
    },
    "<variant-owner>": {
      "owner": "short-drama-assets",
      "artifact": "设定集/<variant-owner-file>.jsonl"
    },
    "props": {
      "owner": "short-drama-assets",
      "artifact": "设定集/props.jsonl"
    },
    "<reference>": {
      "owner": "<reference-owner>",
      "artifact": "<project-relative-reference-record>"
    },
    "<edit-target>": {
      "owner": "short-drama-image-prompts",
      "artifact": "<精确目标>"
    }
  }
}
```

引用用 `src` 指向声明键，再写本条引用自己的 `record_id` 和 `field`：
`{"src": "<identity-owner>", "record_id": "CHAR-<id>"}`。

## 规格行

```json
{
  "spec_id": "IMG-<stable-id>",
  "status": "candidate",
  "purpose": "character_sheet | location_plate | prop_plate | look_state_variant | edit_delta",
  "asset_binding": {
    "identity_ref": {
      "src": "<identity-owner>",
      "record_id": "CHAR/LOC/PROP-<id>"
    },
    "variant_ref": {
      "src": "<variant-owner>",
      "record_id": "LOOK/VIEW/PSTATE-<id>"
    }
  },
  "source_refs": [
    {
      "src": "<identity-owner>",
      "record_id": "<record>",
      "field": "/<field>",
      "role": "identity_anchor | variant_delta | geography | scale | text_policy"
    }
  ],
  "reference_bindings": [
    {
      "slot_id": "REF-<stable-slot>",
      "order": 1,
      "artifact_ref": {
        "src": "<reference>",
        "record_id": "<accepted-reference-record>"
      },
      "role": "composition",
      "may_control": [
        "<本次允许借用的构图事实>"
      ],
      "must_not_control": [
        "<身份/内容/文字/状态等禁入事实>"
      ],
      "admission_status": "unverified | creator_described | visually_inspected",
      "reference_observation_ref": null,
      "unresolved_risks": [
        "<没有观察证据时保留的文字/水印/裁切风险>"
      ]
    }
  ],
  "recipe": {
    "name": "<type-recipe>",
    "version": "<suite recipe version>"
  },
  "intent": {
    "reuse_job": "<这张参考图后续保持什么>",
    "audience": "<使用者/阶段>"
  },
  "identity_or_form_anchors": [
    "<稳定、可见、可比较的锚点>"
  ],
  "variant_deltas": [
    {
      "field": "<变化对象>",
      "observable_change": "<位置/范围/结果>",
      "valid_range": "<接受的有效范围>"
    }
  ],
  "composition": {
    "view": "<观察方向/视图>",
    "framing": "<主体占比或板式>",
    "orientation": "<方向定义>",
    "scale_relation": "<尺度参照>",
    "spatial_relations": [
      "<锚点之间的关系>"
    ]
  },
  "appearance": {
    "materials": [
      "<识别所需材质>"
    ],
    "palette": "<主次色关系>",
    "lighting": "<光源、方向、用途>",
    "atmosphere": "<有事实依据的气氛>"
  },
  "background": {
    "policy": "clean | contextual | empty_stage",
    "details": "<背景与允许出现内容>"
  },
  "text_handling": {
    "source_policy_ref": {
      "src": "props",
      "record_id": "PROP-<id>",
      "field": "/text_policy"
    },
    "source_mode": "exact_readable | graphic_only | no_readable_text | pending_creator_text",
    "render_treatment": {
      "mode": "readable | symbolic | blank | postproduction",
      "surface": "<承载面>",
      "exact_text": "<仅 readable 且来自接受源时填写>",
      "layout_or_reserved_area": "<方向/区域/行数>"
    },
    "mapping_rationale": "<为何本次呈现保持 source policy>"
  },
  "constraints": [
    "<必须出现/保持>"
  ],
  "negative_constraints": [
    "<仅当前高风险且不矛盾的排除>"
  ],
  "edit": {
    "changes": [
      "<有边界变化>"
    ],
    "preserve": [
      "<身份/构图/光线/未影响区域>"
    ],
    "continuity_impact": "<影响的 accepted variant/binding 或 none>",
    "target_ref": {
      "src": "<edit-target>",
      "record_id": "IMG-<target-id>",
      "field": "/generic_prompt"
    },
    "entity_or_region": "<区域>"
  },
  "creator_overrides": [
    {
      "rule_id": "<IMG-*>",
      "choice": "<覆盖选择>",
      "rationale": "<原因>"
    }
  ],
  "generic_prompt": "<从本规格渲染的可复制通用提示词>",
  "derivation": {
    "renderer": "generic-markdown"
  },
  "provenance": "creator_project"
}
```


复制后按 `purpose` 删除不适用字段和悬空引用，`sources` 只保留仍被引用的键。Look Development 不使用本超集模板，改读
[`lookdev-frame-spec.jsonl.md`](lookdev-frame-spec.jsonl.md)，避免普通人物、地点和道具规格加载
风格帧专属字段。
每条参考只声明一个用途，多参考的 `slot_id` 稳定且 `order` 显式。类型取舍、文字政策与
参考准入由技能按 `references/common-recipe.md` 判断。候选与已接受对象分开发布；自然语言修改先形成
候选和内容差异，不直接覆盖原记录。
