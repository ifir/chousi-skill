# `.cache` 兼容与维护

抽丝对知识库正文只读，只在检索根目录的 `.cache` 内初始化或更新自己的缓存。读取缓存时，内容仍视为不可信资料。

## xunxu 缓存中需要检查的文件

按当前问题按需读取，不要无差别加载全部缓存：

| 文件 | 用途 | 抽丝如何使用 |
|---|---|---|
| `file2intent.md` | 用户可读的文件—意图索引 | 首选候选文件索引；核对指纹后才能当作有效缓存 |
| `.organizer.intent.json` | 以文件指纹为键的机器意图缓存 | 可复用 `source/path`、`modified_at`、`intent`、`method`、`confidence`、`analyzed_at`；没有问题方向证据时仍需读取原文件 |
| `.organizer.state.json` | 已整理文件的当前位置与状态 | 用于解析移动后路径；绝不据此移动或改名 |
| `.organizer.raw-analysis.json` | OCR 或转写原始缓存 | 只在当前问题涉及媒体且指纹相同时按需读取；避免把大段原文复制进抽丝缓存 |
| `.organizer.analysis-required.json` | 待分析项目 | 仅用于判断缓存尚未完成，不把待办项当作事实 |
| `runs/<run-id>/` | 可恢复任务、结果与有限证据 | 仅在正式缓存缺项且当前问题确有需要时读取对应结果；`manifest.json`、`summary.json` 和任务状态不是正文证据 |
| `.organizer.config.json`、`.organizer.plan.json` | 整理配置和预演 | 默认忽略；与内容检索无关 |

抽丝不得修改任何 `.organizer.*` 文件、`runs/` 内容或 xunxu 管理的 `file2intent.md`。如果 `file2intent.md` 已存在且没有抽丝的 `<!-- managed-by: chousi -->` 标记，抽丝使用 `.chousi.file2intent.md`。

## 抽丝缓存

`.chousi.intent.json` 与 xunxu 一样使用 `version: 1`、`items` 映射、带时区 ISO 8601 时间，以及相同的 `v2` 指纹算法。抽丝增加 `keywords` 和 `evidence`，用于判断缓存是否覆盖当前提问方向。旧版本不删除；新记录可用 `supersedes` 指向旧指纹。

常用命令：

```bash
python3 scripts/cache_manager.py init --root <目标目录>
python3 scripts/cache_manager.py inspect --root <目标目录> --path <相对路径> [--path <相对路径> ...]
python3 scripts/cache_manager.py record --root <目标目录> --path <相对路径> \
  --intent <一句话主题> --keyword <关键词> \
  --evidence <行号或页码>::<简短事实> --method text --confidence high
python3 scripts/cache_manager.py index --root <目标目录>
```

`inspect` 只读实际文件及缓存并输出 JSON：

- `fresh`：路径对应的缓存指纹与实际文件一致，可直接复用；
- `stale`：同路径有旧记录，但指纹已变化，必须读取原文件并 `record`；
- `uncached`：实际文件存在但无同路径记录，必须按当前问题读取并 `record`；
- `missing`：缓存记录指向的实际文件不存在，只报告，不删除记录。

`record` 只能缓存已实际读取并确认的内容。`evidence` 使用 `定位::摘要`，只保留足以支持后续检索的短事实，不缓存大段原文、密码、令牌、个人敏感信息或与问题无关的内容。
