# 模型价值选择能否作为行为指纹

本调查保留立项时的口径。现行 v2 已按后续需求扩展到科技、网络、哲学和低敏公共议题。 [现行选题依据](QUESTION_DESIGN.md)

调查截至 2026-11-21。对象是中文低敏日常取舍二选一，通过一份整卷文本回复识别预先列出的候选端点。

| 待验证假设 | 现有证据 | 本项目状态 |
| --- | --- | --- |
| H1 同一端点的语义选择对重放、中性前文、消息包装、等义改写、A/B 换位及两套组合模板保持稳定 | 中文道德选择已有逐题重测，模型间稳定性差异明显。英文选择研究也发现等义改写、选项换位及整卷长度效应。连续两条同角色消息在部分接口会合并。 | 待验证。没有本项目真实答卷。 |
| H2 在冻结候选集合内，一次真实 30 题整卷调用可达到 90% 宏平均识别率 | 专用探针、多次采样的简短回答和单篇开放文本均发现端点信号。公开结果使用不同的探针、训练数据规模或输入特征。 | 待验证。没有候选档案、独立盲测或实际费用。 |

可检验的预期是，一些端点会留下可重复的选择模式，尤其是在两个选项都合理、代价不同的题目上。**目前证据支持做受控实验，无法预判 30 题能达标。** 调查将“价值选择”用于描述题目所呈现的取舍行为。对于同一训练权重经不同提供商或后训练部署的情况，观察单位是实际调用的端点及配置。

## AI Compass 原始方法与数据

核查了官网英文方法页及上游提交 `852bc17aa7d40b0ec51095320efc4be35af8b84a`。网站有 165 个预设 AI 研究立场，快测 10 条、完整测试 50 条、专业核心测试 120 条。陈述用五档作答，按题目权重计入五轴。主图的横纵位置体现其中两轴，色阶表示范式轴，外围头衔有各自阈值。 [方法页](https://sihanxu.me/ai-compass/en/method/) · [图表](https://sihanxu.me/ai-compass/en/chart/) · [版本化题目配置](https://github.com/SihanXU/ai-compass/blob/852bc17aa7d40b0ec51095320efc4be35af8b84a/data/tests.yaml)

上游公开 **165 份角色答卷，每个立场一份**。校准说明称，每份答卷按相应百科条目模拟该立场的坚定拥护者，答卷人看不到轴、轴方向和当前位置。JSON 提供各陈述的最终选择。脚本读取每个立场的一份 `answers`，算出原始轴分，缩放坐标，再用匈牙利算法分配图格。部分锚点、中间块和外围头衔有额外规则。图中每个立场是角色答卷校准后的立场位置，公开数据粒度是一份最终角色答卷。原始作答者类型、模型名与版本、逐字生成提示、采样参数、生成次数、是否在发布前合并多轮输出均未知。官网另称“consistency”的量根据各轴内的同向和反向回答计算，衡量卷内方向冲突。该量无法给出跨调用逐题复测一致率。 [校准说明](https://github.com/SihanXU/ai-compass/blob/852bc17aa7d40b0ec51095320efc4be35af8b84a/CONTRIBUTING.md#recalibrate-the-chart) · [公开答卷](https://github.com/SihanXU/ai-compass/tree/852bc17aa7d40b0ec51095320efc4be35af8b84a/data/calibration/personas) · [校准脚本](https://github.com/SihanXU/ai-compass/blob/852bc17aa7d40b0ec51095320efc4be35af8b84a/scripts/calibrate.mjs)

它为题库版本化、题目语义方向和取舍维度提供参考。对 H1 缺少重测数据，对 H2 缺少按模型身份标记的训练样本和留出预测。普通人或模型的轴分、最近图格及角色校准坐标都无法直接用作两项假设的验收数据。

## 检索记录与证据口径

本次为定向广泛调查。检索以 *Evaluating the Moral Beliefs Encoded in LLMs* 和 *Whose Opinions Do Language Models Reflect?* 为起点，沿作者、附录、数据卡、复现仓库和相关文献追踪，交叉查找相反结果。入口包括 ACL Anthology、PMLR、NeurIPS、ICLR、USENIX、arXiv、期刊官网、公开数据仓库、提供商研究与 API 文档、技术博客、开发者论坛及 Hacker News。主要检索组合如下。

| 路径 | 检索词与追踪对象 |
| --- | --- |
| 价值观测量 | `MoralChoice` `OpinionQA` `GlobalOpinionQA` `Chinese moral choice` `ValueBench` `psychometric test-retest reliability` `values in the wild` |
| 提示和环境 | `semantic paraphrases political compass` `multiple choice option order` `irrelevant context` `questions per prompt social desirability` `consecutive user turns merged` `temperature 0 same seed same fingerprint` |
| 闭集识别和反例 | `LLMmap held-out configuration` `model attribution held-out response` `single-token output distributions` `agent wrapper fingerprinting replication` `cross-provider fingerprint` |

“未知”表示在已核查公开材料中未确认对应值。“未做”表示原研究任务没有报告所列的闭集模型识别检验。表中的一致性保留原研究定义。复测同选率、分数差、分布距离、分类正确率和人群对齐是不同指标。

## 中文证据表

### 价值选择、意见分布和量表复测

| 来源及定位 | 模型、语言、任务与调用条件 | 重复次数及模型内结果 | 模型间差异、独立识别和适用性 |
| --- | --- | --- | --- |
| Scherrer 等，MoralChoice，NeurIPS 2023，§3.3、表 1、§4.2–4.3、图 4–5、附录 C。 [论文](https://arxiv.org/abs/2307.14324) · [数据卡与重复数](https://huggingface.co/datasets/ninoscherrer/moralchoice/blob/82540cc6dde4f932b0e87616141da935575be140/README.md) | 英文。28 个开放和闭源模型，包括 GPT-4、GPT-3.5-Turbo、Claude v1.3、Claude Instant v1.0/v1.1、PaLM 2 和 FLAN-T5。正文报告 687 道低歧义、680 道高歧义；初版数据卡另列更宽的元数据口径，实验题数以正文为准。每次一题并重置上下文，A/B、Repeat、Compare 各两种顺序，温度 1。 | 数据卡记录低歧义每题每形式 5 样本，高歧义 10。图 4 的 QF-C 基于选择分布的相似性，另测形式内熵。有模型按模板或顺序改变答案，也有模型保持较强偏好。 | 模型聚类和选择分布有差异。识别未做。H1 强相关，尤其是拆分“复测随机性”和“措辞敏感性”。H2 只提供潜在区分信号。 |
| Santurkar 等，OpinionQA，ICML 2023，§2、§4、附录 A.3–A.4、B 节选项顺序分析。 [论文](https://proceedings.mlr.press/v202/santurkar23a/santurkar23a.pdf) · [作者访谈](https://forum.openai.com/en/public/videos/whose-opinions-do-language-models-reflect-2023-09-13) | 英文。美国 Pew 的 1,498 题和 60 个人口群体。9 个 OpenAI 和 AI21 模型，含 GPT-3、text-davinci-003、Jurassic 系列。对选项标签的对数概率归一化，包含默认与指定群体视角条件。 | 随机重放次数未知。跨话题“consistency”衡量模型最贴近的人群是否稳定。选项重排使各模型代表性分数小幅下降。 | 模型与人群分布的对齐及引导程度不同。识别未做。H1 可借鉴分布与人群对齐的区别，H2 无单次生成证据。 |
| Liu 等，Evaluating Moral Beliefs across LLMs through a Pluralistic Framework，Findings EMNLP 2024，§4.1–4.3、图 2、附录 B.1–B.4 表 6–8。 [论文](https://aclanthology.org/2024.findings-emnlp.272.pdf) | 中文 472 个道德场景。ChatGLM2-6B-32K、Ernie-Bot-turbo、Gemini Pro、GPT-3.5-turbo-16K。API 逐场景选择和自报坚定程度，有两条例子及选项换位平行实验。附录报告默认或指定温度及五档温度对照。 | 三轮重问完全同选比例按上述顺序为 **56%、98%、89%、89%**。温度 0 对 1 的选择一致率分别为 79%、97%、92%、94%。两组指标来自不同实验。 | 图 2 中模型之间的选择一致率约 58%–84%。识别未做。是 H1 的直接邻近证据，但题材、输出、样本结构及对照均与本项目不同。H2 值得实测。 |
| Durmus 等，GlobalOpinionQA，COLM 2024，§2.2–2.4、图 2–5、附录 B/D。 [论文](https://arxiv.org/abs/2306.16388) · [研究说明](https://www.anthropic.com/news/towards-measuring-the-representation-of-subjective-global-opinions-in-language-models) | 一个经 RLHF 和 Constitutional AI 调整的对话模型，精确商用版本未知。GAS/WVS 联合题库，比较默认、指定国别视角及中、俄、土翻译。用选项预测概率比较各国人群分布。 | 同条件独立重放次数及逐题一致率未知。指定国别会改变输出分布，换语言没有稳定地提高与该语言地区人群的相似度。 | 单模型，研究侧重人群比较，识别未做。H1 支持限制语言并排除带身份视角的前文，不能估计中性前文效应。 |
| Röttger 等，Political Compass or Spinning Arrow?，ACL 2024，§4.1–4.5、图 2–4、附录 D。 [论文](https://aclanthology.org/2024.acl-long.816/) · [早期人工测试](https://www.aisnakeoil.com/p/does-chatgpt-have-a-liberal-bias) | 英文 62 条 Political Compass Test 陈述，10 个模型，包括 GPT-3.5/GPT-4 的 0613、1106 版本及 Llama 2 Chat、Mistral Instruct、Zephyr。逐题、温度 0。等义分析用 Mistral 7B Instruct v0.1 和 GPT-3.5 1106 的 10 个最小改写模板。 | 每提示评价一次。即使陈述和选项没变，仅改引导问句也会移动最终坐标。是否明确要求单选改变有效率，开放作答再次改变测量结果。 | 格式服从度有很大模型差异，识别未做。H1 的强反例，特别适用于 D5。H2 需要防止把格式信号当作语义偏好。这里的 Political Compass Test 与用户给出的 AI Research Compass 是两个项目。 |
| Shu 等，Assessing the Reliability of Large Language Models on Psychometric Instruments，NAACL 2024，§3–6、表 1、图 1–3。 [论文](https://aclanthology.org/2024.naacl-long.295/) | 英文人格与伦理量表。Falcon、BLOOMZ、Llama 2、FLAN-T5、GPT-3.5/GPT-4 等，温度 0。改变格式、选项顺序、选项表达、直接否定及改写否定。 | 15 个高可解析模型的大多数选项顺序一致率高于 0.70。10/15 在否定一致性接近或低于 0.50；重复同提示次数未知。否定条件要求语义方向随题意反转。 | 稳定性随模型和扰动异质，识别未做。H1 支持分项显示一致率，改写否定的成绩不能代替等义改写成绩。 |
| Bodroža 等，Personality testing of large language models，Royal Society Open Science 2024，§2–3、表 1–7。 [论文](https://pmc.ncbi.nlm.nih.gov/articles/PMC11461045/) | 英文，七个模型，包括 GPT-3.5-turbo-16k、GPT-4、GPT-4o、Gemini Pro、Llama 3 Sonar Large 32K Chat、Mixtral-8x7b-instruct 与早期 GPT-3。用各自界面、默认或预设设置，要求按人格量表作答。 | 每模型在相隔 5 天的两个时间点测试。加权 Cohen 一致性系数从负值到完美一致，模型及量表差异均明显。Llama 3 与 GPT-4o 在研究中相对较高，GPT-4 与 Gemini 较低。 | 模型与平台、提示干预混杂，端点识别未做。H1 提示复测时间条件需要记录，量表一致系数不能直接代替二选一题目的一致率。 |
| Faulborn 等，Only a Little to the Left，ACL 2025，§3.2–3.4、§5–6。 [论文与数据链接](https://aclanthology.org/2025.acl-long.1529/) | 英文政治倾向测量。11 个模型，包括 Falcon、Llama、Mistral 基础及指令版本，另有 gpt-3.5-turbo-0125 和论文所用 GPT-4。89 条陈述、30 个提示版本，从生成文本识别立场。 | 每个模型、题项、提示组合 3 次，共 88,110 条。报告政治测量分数对提示敏感，本项目定义下的逐题复测率未知。 | 指令模型总体更偏左，选用 Political Compass Test 可夸大部分差异。识别未做。H1 支持把提示视为测量条件，H2 仅提示可区分性。 |
| Ren 等，ValueBench，ACL 2024，§3–4。 [论文](https://aclanthology.org/2024.acl-long.111/) | 英文，44 套量表、453 个维度。GPT-3.5 Turbo、GPT-4 Turbo、Llama 2 7B/70B、Mistral 7B、Mixtral 8×7B。将量表陈述改写成求建议的问题，另做开放式价值理解任务。 | 图 4 提供量表自报与求建议问法不一致的实例，统一重放轮次和整卷稳定率未知。 | 各模型有共享和特有倾向。表 2 GPT-4 Turbo 价值关系识别的 F1 在对称和不对称提示下分别为 85.7 与 65.7。该指标衡量价值关系判断任务。端点身份识别未做，H1 可借鉴测量定义。 |
| Anthropic，Values in the Wild，COLM 2025，§2–4 和数据卡。 [论文](https://www-cdn.anthropic.com/c16bed19d9e2653f2086345a88f3844d184e2e82.pdf) · [公开数据卡](https://huggingface.co/datasets/Anthropic/values-in-the-wild) | Claude.ai Free/Pro 自然对话，主样本大部分为 Claude 3.5 Sonnet。约 70 万对话中筛出 308,210 个主观对话。模型辅助标注所表现的实践、认识论、人际等价值，用户提示及采样参数未统一。 | 同提示重放和同模型一致率未知。记录的是自然任务里的价值表达频率。 | 语境影响表达，有时顺应、有时抵抗或重新表述。未做本项目的识别。H1 支持把“中性前文”与真实改变任务含义的上下文分开。 |
| Anthropic，Claude’s values across models and languages，2026，§1–3、图 3–4、方法附录。 [研究报告](https://www.anthropic.com/research/claude-values-models-languages) | Claude.ai 309,815 个主观对话，Sonnet 4.6、Opus 4.6、Opus 4.7 × 20 种语言（含中文），平均每模型语言组合约 5,000 个。339 个价值标注降至四轴，解释约 15% 变化。 | 自然对话样本，各次提示不同，统一采样参数及重放一致率未知。语言变化伴随任务与用户构成变化。 | 同系列 Opus 4.6 与 4.7 的平均剖面不同。识别未做。H2 支持纳入有条件可测的相邻版本。H1 的配对量仍需自行测量。 |
| Anthropic，Measuring political bias in Claude，2025，Models and evaluation set、Results、Caveats。 [报告与附录入口](https://www.anthropic.com/research/political-even-handedness) | 1,350 对提示、150 主题、9 类任务。Claude Sonnet 4.5、Opus 4.1、GPT-5、Gemini 2.5 Pro、Grok 4、Llama 4 Maverick。部分使用公开系统提示，推理模式不完全一致，模型裁判评估相对公允度。 | 同提示重放次数及逐题同选率未知。95% 等数值是公允度，评的是成对文本质量。 | 各模型公允度约 66%–97%，存在配置混杂。识别未做。H1/H2 仅用于记录系统指令和推理设置的设计依据。 |

### 反例、服务行为及单次整卷的影响

| 来源及定位 | 模型、语言、任务与调用条件 | 重复及模型内结果 | 模型间差异、独立识别和适用性 |
| --- | --- | --- | --- |
| Narayanan 与 Kapoor，Does ChatGPT have a liberal bias?，2023，开头实验记录和注 2。 [原文](https://www.normaltech.ai/p/does-chatgpt-have-a-liberal-bias) | 英文 62 条政治指南针题，公开 ChatGPT 的 GPT-4、GPT-3.5，精确快照和采样配置未知。人工核查回答。 | 重复未知，报告 GPT-4 有 52/62、GPT-3.5 有 33/62 未表态。这里衡量应答行为，站点配置与 API 有差别。 | 格式遵从和是否表态随模型而变，身份识别未做。H1/H2 均应记录格式失败且保留固定分母。 |
| Salecha 等，PNAS Nexus 2024，Methods、图 1–2。 [论文](https://doi.org/10.1093/pnasnexus/pgae533) · [项目页](https://llmsocialbias.github.io/llm-social-desirability-research/) | 英文 Big Five，含 GPT-4/GPT-3.5 0613、Claude 3、Llama 3 等。改变同一提示的题量，另测改写、随机排序及温度。 | 图 1 每模型平均 30 次。1 题对 20 题时社会赞许倾向变化，GPT-4 约 1.20、Llama 3 约 0.98 个人类标准差。逐题同选率未知。 | 变化按模型而异，识别未做。H1 指出题组可构成上下文，H2 强烈支持分别实际发送 30、50 题卷。 |
| Pezeshkpour 与 Hruschka，Findings NAACL 2024，§2–4、表 1。 [论文](https://aclanthology.org/2024.findings-naacl.130.pdf) | 英文客观多选。GPT-4、InstructGPT、Llama-2-13B，研究候选顺序的几种排列及少样本演示。发布版 §2 补充具体模型命名。 | 同提示重放率未知。表 1 最好、最差位置准确率之差约 13–85 个百分点，取决于模型和任务。 | 位置效应强度不同，识别未做。支持 H1 的 D6 以及用语义而非字母评分。该数值是有标准答案题目的性能跨度。 |
| Sclar 等，FormatSpread，ICLR 2024，§2–4、图 2–4。 [论文](https://arxiv.org/abs/2310.11324) · [代码](https://github.com/msclar/formatspread) | 53 个 Super-NaturalInstructions 子任务，在 LLaMA-2-13B 等模型的少样本设置中改变分隔符、标签及排版。 | LLaMA-2-13B 最大跨度 76 个准确率百分点。相同提示重复及本项目逐题同选率未知。 | 格式的相对表现跨模型相关较弱，识别未做。H1 支持控制可见正文，研究的排版变化与 API 消息序列变化是不同干预。 |
| Shi 等，Large Language Models Can Be Easily Distracted by Irrelevant Context，ICML 2023，§4–5、表 3。 [论文](https://proceedings.mlr.press/v202/shi23a/shi23a.pdf) | 英文数学题。code-davinci-002、text-davinci-003，在题内加入无关信息。贪婪解码温度 0，自洽采样温度 0.7。 | GSM-IC-4K 基于 100 道原题。code-davinci-002 的一项 CoT 扰动后的微准确率为 72.4%、严格宏准确率为 6.0%。对应的 76.2% 和 6.3% 是各自按原题解出比例归一化的值。同提示逐题重放率未报告。 | 方法和模型敏感性不同，识别未做。H1 支持 D3。含数字的题内干扰与独立中性前文不同，不外推下降幅度。 |
| Sharma 等，Towards Understanding Sycophancy，ICLR 2024，§2–3、附录 B。 [论文](https://arxiv.org/abs/2310.13548) | 英文。GPT-4、GPT-3.5、Claude 1.3/2 等商业助手，加入“用户喜欢／不喜欢”等偏好或挑战回答。自由文本通常温度 1，多选通常温度 0。 | 重复依子实验不同，附录个别生成实验为 100 次。本项目式逐题稳定率未知。回应会随明示偏好或反问而变化。 | 多模型存在顺应，识别未做。H1 支持中性材料回避身份、奖励、明确偏好及“多数人会选”这类线索。 |
| Anthropic Messages API，`messages` 字段。 [API 参考](https://platform.claude.com/docs/en/api/messages/create) | 原生 Messages API 明文说明将连续 `user` 或连续 `assistant` 消息合入同一个 turn，文档描述与内容语言无关。 | 这是接口规范，重测和逐题率不适用。 | H1 的 D3–D4 与 D1–B2 在已知合并端点按不可测处理。它仍占 H2 固定席位。若请求成功且卷可用，H2 可记录该实际执行的包装行为下的语义预测。其他兼容网关需要逐个核查。 |
| OpenAI，Reproducible outputs with the seed parameter，2023 Cookbook。 [示例和输出](https://developers.openai.com/cookbook/examples/reproducible_outputs_with_the_seed_parameter) | 文档例子使用 gpt-3.5-turbo-1106 的英语生成任务，比较默认和固定 seed 123、温度 0，介绍 gpt-4-1106-preview 支持情况和 `system_fingerprint`。 | 带可检视的多次响应。官方称重放只能尽力保持一致。本项目式逐题结果未知。 | 识别未做。H1 仍需真实 D1–D2。响应元数据可存作审计，交给分类器会泄露身份。 |
| Thinking Machines Lab，Defeating Nondeterminism in LLM Inference，2025，Demonstration。 [实验博客](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/) · [Hacker News 讨论](https://news.ycombinator.com/item?id=45200925) | 自部署 Qwen3-235B-A22B-Instruct-2507、关闭思考、温度 0。英文单提示生成 1,000 token，对照有无批次不变算子。 | 每条件 1,000 次。常规算子有 80 种文本，最常见 78 次。批次不变算子条件下 1,000 次文本相同。 | 单模型，识别未做。H1 提供重放漂移的服务层机制，开放长文本多样性不能换算为低敏二选一翻转率。论坛评论用于追踪机制争议。 |
| OpenAI Developer Community，Deterministic Results Impossible for GPT-4o，2024。 [开发者实验帖](https://community.openai.com/t/deterministic-results-impossible-for-gpt-4o/1059584) · [独立讨论帖](https://community.openai.com/t/inconsistent-and-inaccurate-responses-from-gpt-4o/895453) | 自报 gpt-4o-2024-08-06，固定请求参数，温度 0、固定 seed，生成结构化文本。 | 主帖报告同参数及同系统指纹下 10 次仍有变化。独立样本和同一任务逐题一致率未知。 | 识别未做。社区复现实例只算线索，支持记录请求日期和结束状态，不能据此估计服务商不确定性的频率。 |

### 黑盒端点识别

| 来源及定位 | 模型、语言、任务与调用条件 | 重复及模型内结果 | 模型间差异、独立识别和适用性 |
| --- | --- | --- | --- |
| Pasquini 等，LLMmap，USENIX Security 2025，§7.1–7.2、图 5、表 2、附录 C 表 C.1。 [论文](https://www.usenix.org/system/files/usenixsecurity25-pasquini.pdf) | 42 个开放/闭源版本，含 GPT-4o-2024-05-13、Claude 3.5 Sonnet 20240620、Llama、Qwen、Mistral 等；专用探针与文本特征。预设温度、系统提示和编排条件，训练/测试提示配置不重叠。 | 训练配置每模型 75 条轨迹，每轨迹汇集多个真实交互。模型内相似度按其文本特征计算，本项目式逐题率未知。 | 默认策略 1 次约 **72.9%**，8 次 **95.3%**，42 版本闭集测试；表 2 平均闭集为 95.35%。部分近亲版本混淆，例如 Meta-Llama-3-70B-Instruct 和其微调变体。H2 支持独立配置留出这一设计，成绩无法转用于中文价值选择。 |
| Sun 等，Idiosyncrasies in Large Language Models，ICML 2025，§2.1、表 1、图 2、附录 A.1。 [论文](https://proceedings.mlr.press/v267/sun25z.html) · [代码](https://github.com/locuslab/llm-idiosyncrasies) | GPT-4o-2024-08-06、Claude-3.5-Sonnet-20241022、Grok Beta、Gemini-1.5-Pro-002、DeepSeek-V3。DeepSeek 使用 DeepSeek-Chat 接口名。2024-11-28 至 2025-02-06 通过官方 API 按默认采样，使用 UltraChat 提示生成开放文本。分类器读取单篇回复，输入上限 512 token，利用词句和结构。 | 同提示逐次重放率未知。每提示集约 11,000 条序列，10,000 训练、1,000 留出，跨模型共用拆分。 | 五类留出 **97.1%**，均匀基线 20%。H2 的单篇归属存在性证据，题量、语种、训练规模与输出信号都不同。H1 无语义复测证据。 |
| One Token Is Enough，arXiv 2026 预印本，§IV–VII、表 III、图 3–4。 [论文](https://arxiv.org/abs/2607.10252) | OpenRouter 165 个模型、53 个服务商，英语、俄语、中文及阿拉伯语，10 类简短任务，例如随机数。每请求采一份短回答，聚合 40 个任务×语言单元。 | 每单元温度 1 采 30 次，高价模型 15 次。温度 0 另采 3 次。同模型独立半样本与异模型的中位 JSD 为 0.075 和 0.489；同提供商温度 0 时 90.4% 单元完全一致，混合提供商为 84.5%。 | 满量验证 AUC 0.971，等错误率 7.3%；验证某一声明身份，未做当前闭集 30 题整卷分类。“One token”指每次回复单位，分布指纹来自多次采样。H1/H2 均提示应区分同模型、同部署和单个样本。 |
| Lasso Security，How Robust is LLM Fingerprinting in the Agent Era?，2026，Setup、图 1、表 5、Limitations。 [公开复现实验](https://www.lasso.security/blog/llm-fingerprinting-agent-era) | 13 个 LLMmap 模板覆盖的模型，含 GPT-4o-2024-05-13、gpt-4-turbo、Mistral-7B-Instruct-v0.1。单服务平台，三个应用，比较原始调用、默认代理、德语、强格式约束。评估开放集工具的精确识别和族级部分匹配。 | 每条件 13×3 个模型应用组合。逐题重测未知。 | 精确识别率从裸 API 的 **24/39** 降至默认 **20/39**、德语 **15/39**、强约束 **7/39**。非同一套采分协议的小样本第三方复现。H2 明确限制对其他 harness 的外推，H1 保留消息包装对照。 |

## 证据综合与推理

1. **先验证单题选择再看整体识别。** 单题若在不同形式下大幅翻转，偏好均值仍可能显著分离。反过来，两个模型若都稳定偏向同一选项，稳定率可以很高而没有相互区分能力。两个模型也可能在一组题上恰好作出相反选择，但整卷的维度均分相同。逐题语义向量能保留这种信号。MoralChoice 将模板间分布差异和模板内熵分开，中文研究也给出了可分别查看的重测和模型间矩阵。 [MoralChoice §4.2–4.3](https://arxiv.org/abs/2307.14324) · [中文道德选择论文，图 2 与表 8](https://aclanthology.org/2024.findings-emnlp.272.pdf)
2. **同一端点的复测变动至少有三个来源。** 重放的输出变化可来自采样或推理服务。同义题和换位反映测量表述变化。中性前文和消息边界改变模型输入，服务端合并还可能使预期控制失效。把 D1–D2、D1–D3、D3–D4、D1–D5、D1–D6 分开，能定位观测波动与哪项操作同时发生。对两套盲卷只能判定组合效果。 [Röttger 等 §4](https://aclanthology.org/2024.acl-long.816/) · [Thinking Machines Lab](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/) · [Claude API](https://platform.claude.com/docs/en/api/messages/create)
3. **30 与 50 题是两次不同的干预。** 同一请求的题目数量会改变上下文，题间答案还可以相互影响。在 50 题答卷里删去 20 个答案，估计的是同一生成结果减少观测的影响。真实 30 题和 50 题成对比较还能反映题量对作答、解析及完成率的作用。短卷应复用各自长卷的措辞、选项方向和相对题序，使长度解释更清晰。 [Salecha 等图 1–2](https://doi.org/10.1093/pnasnexus/pgae533)
4. **识别信号仅从统一协议下的语义选择读取。** 开放文本分类已经证明措辞和组织方式本身有端点信号。在本项目里，格式、延迟、token 用量、自报身份和返回的模型名均可能成为捷径。采集阶段保留它们作诊断，匿名评分阶段只读题号与语义选项。缺答跳过且设整卷覆盖门槛，可减少少量答题碰巧高分的情况。选题和建档都按开发配置整组留出，D1/D2 一起留出，避免逐题拆分把同一卷的行为泄漏到验证中。 [Sun 等 §2–3](https://proceedings.mlr.press/v267/sun25z.html) · [LLMmap §7.1](https://www.usenix.org/system/files/usenixsecurity25-pasquini.pdf)
5. **样本规模限定结论。** 当候选数为 \(M\) 时，主检验只有 \(2M\) 个真实短卷机会。若 \(M=2\)，最低达标为 4/4；若 \(M=5\)，最低达标为 9/10，个别模型仍可能只命中一次。同一题组、同一模板族及同一服务期可能相关，不能把题数当作独立样本量。90% 是本轮验收值。观察到一次“成功”仍只支持冻结候选、固定语种、模板和采集时段。 [下一步规划](NEXT_STEPS.md)

检索覆盖了能回答设计问题的代表性来源。对低敏中文日常取舍、纯文本逐行输出、每次一份 30 题整卷、训练每端点仅六次和两套独立新模板这个组合，所审阅来源里没有可直接采用的盲测成绩。
