# Agent Entry Point

所有项目知识从 [docs/README.md](docs/README.md) 开始读取。根目录只保留启动入口，不复制架构、进度或决策正文。

开始任务前：

1. 阅读 `docs/README.md`。
2. 阅读 `docs/PROGRESS.md` 与 `docs/FEATURES.json`。
3. 修改结构、数据流或外部依赖前，阅读 `docs/ARCHITECTURE.md` 与 `docs/DECISIONS.md`。
4. 运行 `python scripts/harness/doctor.py` 检查 Harness 路由和 WIP 状态。

工作规则：

- 任意时刻最多一个功能项处于 `active`。
- 没有可复现的验证证据，不得将功能项标记为 `passing`。
- 保留用户已有改动；不要为当前功能扩展无关重构。
- 不把 LLM 输出、客户端上报的交易哈希或手动输入的钱包地址视为可信事实。
- 新增环境变量时同步更新对应 `.env.example` 和 `docs/DEVELOPMENT.md`。
- 数据库模型变化必须记录迁移或明确说明本地重建策略。

常用命令：

```powershell
python scripts/harness/task.py list
python scripts/harness/task.py start <ID>
python scripts/harness/task.py verify <ID>
python scripts/harness/doctor.py
python scripts/harness/doctor.py --run
python scripts/harness/finish.py
```
