# chousi-skill（抽丝）

“抽丝”是一个 Codex Skill：不依赖 RAG 或向量数据库，直接在获准访问的本地知识库、项目文档、笔记和代码中，通过关键词扩展、文件关联与证据回溯逐层检索，输出可复查的答案。

## 能做什么

- 从自然语言问题提取关键词、同义词、实体和时间线索；
- 从一次命中继续追踪链接、引用、版本、编号和关联文件；
- 综合跨文件证据，区分事实、推论、冲突和未知项；
- 用绝对文件路径和行号标注来源；
- 严格只读知识库，绝不改名、移动、删除或修改已有文件；
- 每次检索优先复用目标目录中的 `.cache`，按文件指纹检查过期并增量刷新；
- 缓存格式与 xunxu-skill 保持同类结构，同时使用 `.chousi` 前缀避免覆盖其它工具缓存；
- 兼容 xunxu 的 OCR、转写、视频关键帧及组合证据缓存，并读取依赖评估识别能力盲区；
- 按文件类型进行局部意图识别，每个候选文件每轮最多读取 5 个、每块 200–500 字符；
- 区分首次检索、重复提问和复用 xunxu 缓存三种流程，缓存按检索方向增量生长；
- 全程本地，不把知识库上传到外部服务。

## 只读边界与缓存

抽丝对知识库正文只有读取权限，不执行文件整理。唯一允许的写入是检索根目录的 `.cache`：不存在时初始化，存在时先核对机器缓存、可读索引与实际文件。文件大小、纳秒修改时间或首尾采样内容发生变化时，抽丝重新读取相关文件并增量更新缓存；指纹未变化时直接使用缓存。

机器缓存保存于 `.cache/.chousi.intent.json`，可读索引通常保存于 `.cache/file2intent.md`。如果该索引已经由其它工具维护，则抽丝改用 `.cache/.chousi.file2intent.md`，不会覆盖已有缓存。

## 安装

将仓库复制到 Codex 的 skills 目录：

```bash
git clone https://github.com/ifir/chousi-skill.git
cp -R chousi-skill ~/.codex/skills/chousi
```

如果已经安装，可用最新仓库内容覆盖 `~/.codex/skills/chousi`。安装或更新后，在下一轮 Codex 对话中即可使用。

## 使用

可以显式调用：

```text
使用 $chousi 在 /path/to/knowledge-base 中查找关于“项目定价调整”的资料，给出结论、证据和仍不确定的地方。
```

也可以直接提出适合本地检索的问题，例如：

```text
帮我从本地会议纪要里梳理这个决策是怎么形成的，并标出关键来源。
```

## 仓库结构

```text
chousi-skill/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── cache-compatibility.md
│   └── retrieval-workflows.md
├── scripts/
│   └── cache_manager.py
└── README.md
```
