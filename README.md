# chousi-skill（抽丝）

“抽丝”是一个 Codex Skill：不依赖 RAG 或向量数据库，直接在获准访问的本地知识库、项目文档、笔记和代码中，通过关键词扩展、文件关联与证据回溯逐层检索，输出可复查的答案。

## 能做什么

- 从自然语言问题提取关键词、同义词、实体和时间线索；
- 从一次命中继续追踪链接、引用、版本、编号和关联文件；
- 综合跨文件证据，区分事实、推论、冲突和未知项；
- 用绝对文件路径和行号标注来源；
- 全程本地、默认只读，不把知识库上传到外部服务。

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
└── README.md
```
