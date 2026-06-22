# Alive28 文档索引

本目录是项目知识的唯一权威入口。根目录 `README.md` 仅用于项目介绍和最短启动路径。

## 阅读顺序

| 文档 | 什么时候读 | 内容 |
|---|---|---|
| [PRODUCT.md](./PRODUCT.md) | 理解项目目标时 | 产品背景、用户旅程、范围与非目标 |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 修改代码或数据流前 | 模块职责、调用链、数据与信任关系 |
| [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) | 开始下一阶段开发前 | SpoonOS Agent、LLM 安全、链上凭证与分阶段实施计划 |
| [DEVELOPMENT.md](./DEVELOPMENT.md) | 安装和启动时 | 环境、配置、本地运行、合约和数据库 |
| [testing.md](./testing.md) | 验证改动时 | 验证层级、命令、完成定义和当前基线 |
| [PROGRESS.md](./PROGRESS.md) | 开始或交接任务时 | 当前目标、已知问题、下一步 |
| [DECISIONS.md](./DECISIONS.md) | 变更重要设计时 | 已确认决策和待确认问题 |
| [FEATURES.json](./FEATURES.json) | 执行 Harness 工作流时 | WIP=1 的机器可读任务状态 |

## 项目地图

```text
frontend/   Next.js 页面、钱包交互、后端客户端
backend/    FastAPI、Graph 工作流、LLM、SQLite
contracts/  ProofRegistry 与 NFT 合约
docs/       项目知识与状态
scripts/    Harness 管理和验证脚本
.harness/   验证证据、会话交接和命令配置
```

## Agent Harness

<!-- harness-adopter:start -->

- 启动规则：[`../AGENTS.md`](../AGENTS.md)
- 架构规则：[`ARCHITECTURE.md`](./ARCHITECTURE.md)
- 后续实施计划：[`IMPLEMENTATION_PLAN.md`](./IMPLEMENTATION_PLAN.md)
- 当前进度：[`PROGRESS.md`](./PROGRESS.md)
- 决策记录：[`DECISIONS.md`](./DECISIONS.md)
- 开发环境：[`DEVELOPMENT.md`](./DEVELOPMENT.md)
- 测试与完成定义：[`testing.md`](./testing.md)
- 功能状态：[`FEATURES.json`](./FEATURES.json)

Harness 管理命令见根目录 `AGENTS.md`。验证日志写入 `.harness/evidence/`，会话交接写入 `.harness/session/`。

<!-- harness-adopter:end -->

## 文档维护规则

- 运行方式变化：更新 `DEVELOPMENT.md`。
- 模块职责、数据流或依赖变化：更新 `ARCHITECTURE.md`。
- 当前目标或阻塞变化：更新 `PROGRESS.md`。
- 需要后续维护者理解的重要取舍：更新 `DECISIONS.md`。
- 不再维护并行的启动、测试或问题清单文档。
