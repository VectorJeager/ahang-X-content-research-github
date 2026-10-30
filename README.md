# 阿杭内容研究 Skill

把 @Astronaut_1216（叫我阿杭）的现有阶段研究，整理成可供大模型按需读取的 Skill。

**这是独立研究整理，不是作者官方产品。包内有31条证据摘录，未完成最早起连续1500篇原创与引用帖的全文研究。**

已加入用户提供的四段直播（第05—08段）中白衣发言者的16项主题观点，附时间戳、应用建议和适用边界。视频主题与X帖子分别归档，不据画面推定其账号身份。

## 可以用来做什么

- 研究账号的内容演变、定位、选题与表达方式。
- 拆解工具推荐、AI工作流和内容与服务的连接。
- 用自己的真实材料准备原创内容草稿与实践计划。
- 检索原帖摘录、阅读状态和直达链接，继续增补证据。
- 按视频时间戳回看白衣发言者关于公开学习、垂直定位、个人品牌、AI用例和业务交付的观点。

来源记录截至2026年10月30日。收入、涨粉和效果主要为作者自述，包内不提供收益保证、完整账号统计或自动采集服务。

## 文件结构

```text
.
├── README.md
├── LICENSE
├── NOTICE.md
├── tests/
│   └── test_evidence.py
└── skills/
    └── ahang-content-research/
        ├── SKILL.md
        ├── agents/openai.yaml
        ├── scripts/evidence.py
        ├── assets/
        │   ├── content-brief.md
        │   └── research-brief.md
        └── references/
            ├── research-boundaries.md
            ├── stage-report.md
            ├── detailed-analysis.md
            ├── video-insights.md
            ├── evidence.json
            ├── writing-guide.md
            └── evidence-update.md
```

原阶段报告与18页详解的内容已转换为Markdown和JSON。包内不重复放入Word文件、预览图片或本机渲染脚本。研究证据的原文摘录只在 `references/evidence.json` 保存一份，分析文件引用证据编号。

视频补充见 [白衣发言者观点](skills/ahang-content-research/references/video-insights.md)。四段总长24分57.45秒，采用本地ASR、转写审读和相关连续画面核对整理，尚非逐句人工听校的实录。原视频、音频、自动转写全文及本地模型均不进入上传包；没有公开URL的来源以文件名和时间戳定位。

## 使用方式

### 在支持 Skill 的客户端中使用

将 `skills/ahang-content-research` 整个文件夹放入客户端配置的技能目录，确保该文件夹根目录直接包含 `SKILL.md`。使用客户端的发现或安装方式加载它。Codex中的显式调用示例：

```text
使用 $ahang-content-research，解释阿杭如何从公开学习转向场景化内容，并给出对应原帖。
```

本包不依赖特定MCP服务、模型API或账号登录。`agents/openai.yaml` 为Codex提供界面元数据；其他客户端可按自身支持方式读取 `SKILL.md` 和参考资料。本项目没有逐一验证所有客户端的自动发现规则。

### 在普通对话中使用

先提供 `SKILL.md` 与 `references/research-boundaries.md`，再按问题提供相关分析或证据记录。不必把整个目录一次性塞入上下文。

### 使用示例

```text
1. 根据已读样例，拆解阿杭工具推荐帖的开头、操作说明和结尾。引用原帖并标注哪些只有预览。

2. 我刚用AI整理了一份课程咨询记录，人工纠正了三处分类。用我的真实材料写一篇X帖子，不添加收入或客户成绩。

3. 我想学习多模型协作。先检索有关证据，再设计一个能核对结果的小任务，区分作者做法和你的建议。

4. 我补充了几条原帖。请按证据更新说明去重、记录读取状态，更新阶段分析，不改变尚未证明的覆盖结论。

5. 应用直播中白衣发言者的观点，从我实际工作里的一个问题设计AI体验任务，再根据真实结果准备帖子。说明参考的V编号与视频时间。
```

## 本地查询与检查

脚本只读本地JSON，不联网，不发布内容。使用Python 3.10或更高版本，无第三方运行依赖。从仓库根目录执行：

```sh
python skills/ahang-content-research/scripts/evidence.py stats
python skills/ahang-content-research/scripts/evidence.py search 多模型
python skills/ahang-content-research/scripts/evidence.py show E18
python skills/ahang-content-research/scripts/evidence.py list --status preview_only
python skills/ahang-content-research/scripts/evidence.py validate
python -m unittest discover -s tests -v
```

命令默认输出JSON，便于大模型继续处理。`--dataset` 可以读取另一份符合相同结构的数据，原数据不会被脚本修改。搜索按关键词在标题、标签、摘录和分析中匹配，不是语义搜索；搜索无匹配不说明作者没有写过该主题。

这些命令只查询和校验X研究JSON。视频的V01—V16主题由模型按 `video-insights.md` 的任务索引读取，不包含在CLI搜索和统计中。

## 覆盖范围

| 项目 | 目前情况 |
| --- | --- |
| 仓库内实际证据 | 31条，其中包含回复、预览、卡片及作者网站整理版 |
| 原会话报告的观察数 | 451条混合记录，未保留为451行完整原始底稿 |
| 原会话中的主帖扫描片段 | 160条，不能当作160篇已完整读取的正文 |
| 最早可见记录 | 2025年1月8日，未证明是历史第一条 |
| 连续前1500篇全文覆盖 | 尚未完成 |
| 新增视频补充 | 四段本地视频的16项主题观点，独立V编号，不作为新增X帖子 |

这些口径不能混用，不能用31或451直接计算“1500篇研究完成率”。完整边界见 [研究边界](skills/ahang-content-research/references/research-boundaries.md)。

## 上传到 GitHub

将这个目录内的文件作为一个新仓库的内容上传即可。也可以通过本机Git提交后推送到你选择的仓库。本包没有创建远程仓库、替你提交或推送，也不包含账号凭证。

如只需要分发Skill，上传 `skills/ahang-content-research` 文件夹即可；完整仓库同时提供说明、权利归属和本地检查。

## 权利与来源

代码、Skill指令和原创研究说明采用MIT许可证。被引用的原帖文字、账号名称、商标及第三方材料不在MIT授权范围内，详见 [NOTICE.md](NOTICE.md)。摘录保留原作者归属与来源链接，不作为新的原创帖文素材分发。
