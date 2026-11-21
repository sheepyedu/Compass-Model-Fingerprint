# 探索性开发试验运行说明

现阶段采集 D1–D6 和额外的 D7，共七次整卷调用／端点。六个 DeepSeek／GPT 候选加四个 Claude，最多 70 次。D7 单列，原正式协议的六个建档槽位与四个盲测槽位保留其原有用途。若十个端点原配置继续用于正式验证，另需 40 次真实盲测。最终扩大名单时，每个新增端点六次开发建档和四次盲测。正式候选只在验证阶段冻结。

以下是官方目录中可核对的候选 ID。实际网关版本、当前权限、费率和连续消息行为需要在发送前确认。

| 候选键 | 请求模型 ID | 官方参考输入／输出费率（美元／百万 token） |
| --- | --- | --- |
| deepseek-flash | `deepseek-flash` | 0.30 / 1.20，峰时未命中缓存 |
| deepseek-pro | `deepseek-v4-pro` | 1.32 / 3.96，峰时未命中缓存 |
| gpt-sol-61 | `gpt-6.1-sol` | 2.00 / 10.00 |
| gpt-sol-62 | `gpt-6.2-sol` | 2.00 / 10.00 |
| gpt-luna | `gpt-6-luna` | 0.10 / 0.50 |
| gpt-terra | `gpt-6.1-terra` | 1.00 / 5.00 |
| claude-haiku-55 | `claude-haiku-5-5` | 0.10 / 0.50，100,000 输入 token 以内 |
| claude-sonnet-46 | `claude-sonnet-4-6` | 3.00 / 15.00 |
| claude-sonnet-5 | `claude-sonnet-5` | 2.00 / 10.00 |
| claude-sonnet-55 | `claude-sonnet-5-5` | 2.00 / 10.00 |

Sonnet 采用 5、5.5 和指定加入的 4.6。4.6 在官方模型页标为 Legacy，生命周期页面仍列为 Active。官方目录中较新的 Haiku 只有 5.5，4.5 已列为 Legacy，因此 Haiku 暂只占一个席位。网关访问仍待验证。 [DeepSeek 定价](https://api-docs.deepseek.com/quick_start/pricing/) · [OpenAI 定价](https://developers.openai.com/api/docs/pricing) · [Claude 定价](https://platform.claude.com/docs/en/about-claude/pricing) · [Claude 生命周期](https://platform.claude.com/docs/en/about-claude/model-deprecations)

官方费率下，以每次 15,000 输入 token、最多 1,024 计费输出 token 预留，本轮十端点七次约 **1.93 美元**，其中 DeepSeek 两端点约 **0.21 美元**。按当前模板正文和每次 1,024 token 的消息开销预留计算，v2 首轮题卷的官方费率参考值约 **1.58 美元**。运行器计算每份实际消息正文 UTF-8 字节数，再加清单中的服务端消息开销预留，乘以确认的端点费率。对存在未知服务端提示、分词或计价开销的网关，先核实后调整预留。

## 本地清单

清单是 JSON 数组，每端点一项。以下为结构示例，域名为占位符。实际清单和 SQLite 账本放在仓库本地忽略目录 `.claude-manager/`。凭据只从给定环境变量读取。

```json
[
  {
    "candidate": "deepseek-flash",
    "provider": "已确认服务商名称",
    "model": "deepseek-flash",
    "version": "DeepSeek-V4.1-Flash-1017",
    "confirmed_on": "2026-11-21",
    "url": "https://example.invalid/v1/chat/completions",
    "api": "chat",
    "key_env": "DEEPSEEK_API_KEY",
    "two_user_turns": "unknown",
    "defaults": {"thinking": "enabled", "two_user_turns": "unknown"},
    "parameters": {"thinking": {"type": "disabled"}, "temperature": 0},
    "output_cap": 1024,
    "framing_tokens": 1024,
    "input_usd_per_million": 0.30,
    "output_usd_per_million": 1.20,
    "price_source": "网关价格出处及适用档位"
  }
]
```

运行须至少有两个已核对端点。正式套件和探索套件共享 D1–D6，已发起的槽位在同一个账本内复用。用 `chat`、`responses` 或 `messages` 选择接口。对 Chat Completions 可配置 `chat_limit_field`。在同一端点的 D1–D7 中显式参数保持固定，记录服务商默认值与实际有效版本。原生 Claude Messages 的连续同角色消息会合并，记 `merged`。行为未知的端点保留 D4 结果供诊断，相应包装比较标为不可测。 [Anthropic Messages 参考](https://platform.claude.com/docs/en/api/messages/create)

每个账本绑定候选清单、预估费率、所有模板摘要和运行器版本。发送前原子占位，无自动重试或重定向。响应里可见的模型名、请求 ID、系统指纹、token 使用量存入本地账本，均不用于语义选题。合成测试通过仅说明工具处理这些边界的行为。真实端点的格式兼容性、题目实测区分度和费用须等开发答卷。

## 小批量筛题

`budget`、`collect`、`report` 均可加 `--quick`。挑一至两个候选，每个端点只发送 D1、D2、D6，每份为独立新会话的完整 50 题卷。只测一个端点时可分析题目的重放或位置波动。挑两个端点时，报告同时标出稳定分歧和稳定同选。其余槽位保留待用，重跑只占用从未占用的槽位。两端点小试可用同一账本和同一清单续跑完整开发配置。单端点小试仅支持单端点诊断。

逐题先看是否完整可测，再看 D1–D2 与 D1–D6 的语义翻转。在两个端点都三次有效且各自同选的题里，两端点偏向相反是“稳定分歧”，同向是“稳定同选”。报告保留原始语义选择和端点名。它们是供审阅的开发信号，两端点同选仍可能在扩大候选后产生区分度。一端点的结果仅说明其自身行为。低覆盖卷不会进入上述诊断。

开始前固定当前问卷版本，不在采集中改题。v3 和 v4 的两次题库修订各用独立账本复测。每轮先检查 D1 达到整卷门槛，再发后续对照。

[题面预筛](QUESTION_REVIEW.md)记录需要优先对照实测的题目。

DeepSeek 兼容网关的小试白名单包含两个 4.1 Flash 快照，允许同系列近邻版本对照。若服务明确要求 HTTP，获用户授权后可在小试命令中加 `--allow-http`。HTTP 小试直连清单中的入口，无重定向或代理转发。完整开发配置仍仅支持 HTTPS。
