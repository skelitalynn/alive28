# 当前进度

更新时间：2026-06-22

## 当前目标

当前处于设计完成、代码未开始阶段。没有 `active` 功能项。下一次代码任务应创建并启动 `F-002 Reflection Safety Graph`。

## 最近完成

- 建立 `docs/README.md` 单一文档入口。
- 将原 README、启动、测试和问题清单迁移到职责明确的文档。
- 安装 WIP=1、任务状态、验证证据和会话交接脚本。
- `F-001` 文档路由验证通过；证据路径记录在 `docs/FEATURES.json`。
- 新增 `IMPLEMENTATION_PLAN.md`，明确 SpoonOS 硬约束、Agent 能力、Reflection Safety、链前拒绝、链后补偿、隐私和分阶段实施方案。

## 当前实现状态

已从代码确认存在：

- 前后端每日打卡主链路。
- Reflection 与报告 LLM 调用及静态 fallback。
- SQLite 日志、进度和里程碑记录。
- ProofRegistry、Day/Final NFT 和 Milestone NFT 合约。
- 前端钱包交易调用和 Demo 地址模式。

这些是代码中可见的能力，不代表完整端到端环境已经验证通过。

## 已知阻塞与风险

### P0：安全与可信性

- Reflection 只有格式和最大长度约束，没有危机路由与语义安全验证。
- 手动地址和请求中的地址没有签名认证，可冒用其他地址。
- `/tx/confirm`、`/nft/confirm` 和 `/milestone/mint` 不验证链上 receipt 或 event。
- 日记原文明文保存，并发送给外部 LLM 或图片生成 adapter。
- Pollinations 调用把用户内容放入 URL Prompt。

### P1：工程可靠性

- 后端测试覆盖很少，没有 LLM、路由或完整打卡集成测试。
- 前端没有自动化测试。
- 数据库没有迁移工具，只使用 `create_all()`。
- 没有 CI。
- `mockClient.ts`、`spoonClient.ts`、`spoonAgent.ts` 和旧 `frontend/lib/api.ts` 形成重复实现。
- 部分源码仍存在历史编码损坏。

### 当前验证基线

2026-06-22：

- Harness 结构检查通过。
- 文档路由检查通过。
- 完整 `doctor.py --run` 停在后端测试收集：当前 `python` 环境缺少 `sqlmodel`。
- 因验证链按失败即停止，前端构建和合约测试未在该次 Harness 运行中执行。
- 前期单独检查已确认 `frontend/node_modules` 未安装，Foundry 子模块未初始化。

这些是环境基线问题，不应被记录成代码测试通过或失败。

## 下一步建议

1. 初始化依赖并跑通 `.harness/config.json` 的完整验证链。
2. 锁定并核对实际 SpoonOS SDK 版本的 Graph、工具、记忆、Checkpointer 和重试接口。
3. 创建唯一活动任务 `F-002 Reflection Safety Graph`。
4. 按 `IMPLEMENTATION_PLAN.md` 的 Phase 1 实现风险分类、输入质量、生成、校验、修复、危机和 fallback 节点。
5. 后续按 Phase 2–5 处理恢复、身份、链上可信性、隐私、长期记忆和 CI。

实际执行顺序由 `docs/FEATURES.json` 中唯一的 `active` 功能项决定。
