# `lookdev-frame` 填写模板

只在 `purpose: lookdev_frame` 时读取。首行是 `sources` 声明记录，之后每行一个候选风格帧规格；它投影已接受视觉方向，
不替普通人物、地点、道具规格增加字段。删除当前测试轴不需要的可选项。

## 首行：`sources` 声明

本文件用到的每个上游快照在这里声明一次，键取产物文件名，在本文件内唯一且稳定。视觉方向与
制作形态同出于 `short-drama.json`，共用一个键：

```json
{
  "record_type": "sources",
  "schema_version": "1.0.0",
  "sources": {
    "short-drama": {
      "owner": "creator",
      "artifact": "short-drama.json"
    },
    "<identity-owner>": {
      "owner": "short-drama-assets",
      "artifact": "设定集/<identity-owner-file>.jsonl"
    },
    "<variant-owner>": {
      "owner": "short-drama-assets",
      "artifact": "设定集/<variant-owner-file>.jsonl"
    },
    "screenplay-index": {
      "owner": "short-drama-write",
      "artifact": "剧集/<EP>/screenplay-index.jsonl"
    },
    "<reference>": {
      "owner": "<reference-owner>",
      "artifact": "<project-relative-reference-record>"
    }
  }
}
```

引用用 `src` 指向声明键，再写本条引用自己的 `record_id` 和 `field`。

## 规格行

```json
{
  "spec_id": "LOOKDEV-<stable-id>",
  "status": "candidate",
  "purpose": "lookdev_frame",
  "lookdev_axis": "character_expression | core_location | high_pressure_scene",
  "direction_ref": {
    "src": "short-drama",
    "field": "/creator_authority/visual_direction/choices/look_development"
  },
  "production_profile_ref": {
    "src": "short-drama",
    "field": "/creator_authority/production_profile"
  },
  "subject_bindings": [
    {
      "identity_ref": {
        "src": "<identity-owner>",
        "record_id": "CHAR/LOC/PROP-<id>"
      },
      "variant_ref": {
        "src": "<variant-owner>",
        "record_id": "LOOK/VIEW/PSTATE-<id>"
      },
      "role": "expression_subject | location | pressure_actor | evidence"
    }
  ],
  "story_context_refs": [
    {
      "src": "screenplay-index",
      "record_id": "BLK-<EP>-<SC>-<kind><nn>",
      "field": "/<exact-source-field-if-needed>",
      "role": "scene_heading | action | dialogue | information_permission | story_state"
    }
  ],
  "reference_bindings": [
    {
      "slot_id": "REF-<stable-slot>",
      "order": 1,
      "artifact_ref": {
        "src": "<reference>",
        "record_id": "<stable-record-id>"
      },
      "role": "style",
      "may_control": [
        "<色彩层级/材质处理/阴影边缘/景深倾向/画面密度>"
      ],
      "must_not_control": [
        "<角色身份/固定地理/剧情状态/人数/持物/道具文字>"
      ],
      "admission_status": "unverified | creator_described | visually_inspected",
      "reference_observation_ref": null,
      "unresolved_risks": []
    }
  ],
  "test_question": "<本帧要暴露哪一种视觉方向风险>",
  "stable_visual_rules": [
    "<跨测试轴必须保留的可观察规则>"
  ],
  "allowed_variation": [
    "<本场允许变化的光比/冷暖/留白/密度>"
  ],
  "composition_and_state": "<只写当前代表帧需要的构图、空间与剧情状态>",
  "appearance": {
    "materials": [
      "<材质处理>"
    ],
    "palette": "<色彩层级>",
    "lighting": "<光源逻辑与阴影边缘>",
    "depth_or_density": "<景深/画面密度>"
  },
  "constraints": [
    "<必须保持的身份、地理、文字与信息权限>"
  ],
  "generic_prompt": "<只含可被画出的自然表述，语言按 #/format/prompt_language，不含字段名/hash/审查话术>",
  "derivation": {
    "renderer": "generic-markdown"
  },
  "provenance": "creator_project"
}
```

人物与地点测试没有剧情职责时删除 `story_context_refs` 及其 `sources` 键；高压力场景必须保留真实 `BLK-…`
来源。单主体也使用一项 `subject_bindings[]`，不再与 `asset_binding` 二选一。无参考媒体时
`reference_bindings` 为空；多参考的 `slot_id` 稳定、`order` 唯一。
