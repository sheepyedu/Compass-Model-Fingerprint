# Compass Model Fingerprint

研究问题是，在固定候选端点集合内，单次提交一份关于科技、网络、哲学和低敏公共议题的中文二选一问卷，能否获得既稳定又能区分端点的语义选择。

- [中文调查与证据表](docs/RESEARCH.md)包含 AI Compass 原始数据核查、论文、技术报告、公开实验及社区帖。
- [下一步实验规划](docs/NEXT_STEPS.md)记录批准版方案的实施顺序、预算、判定规则和检查点。

当前完成调查、实验规划、50 题题库和开发采集工具。真实端点与答卷待采集，两项假设均待验证。

## 探索性开发试验

[题目选择依据](docs/QUESTION_DESIGN.md)记录补充来源、题库审阅和 D7 聊天提示对照。当前题库在 `data/questions-v2.tsv`，每行依次是题号、维度、基线题干、开发等义题干、两套盲测题干和两个固定语义选项。v1 为日常取舍历史版本。

`pilot.py` 使用 Python 标准库。先运行 `python3 pilot.py validate`。有已核对的端点配置后运行 `python3 pilot.py budget --endpoints <本地清单>`，以 `python3 pilot.py collect --endpoints <本地清单> --db <本地账本> --max-usd <批准上限>` 发送。运行 `python3 pilot.py report --endpoints <本地清单> --db <本地账本>` 查看已记录结果。配置结构及预算见[试验运行说明](docs/PILOT.md)，合成测试见 [TEST.md](TEST.md)。
