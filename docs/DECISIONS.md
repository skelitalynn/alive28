# 决策记录

本文件记录后续维护者必须理解的已确认取舍。尚未决定的问题不得伪装成规则。

| 日期 | 决策 | 原因 | 状态 |
|---|---|---|---|
| 2026-06-22 | `docs/README.md` 是唯一文档路由入口 | 避免根目录、启动文档和问题清单形成重复知识源 | Accepted |
| 2026-06-22 | Harness 使用 `docs/FEATURES.json`、WIP=1 和验证证据 | 让任务状态可机读，禁止未验证完成 | Accepted |
| 2026-06-22 | 对外把 AI 定位为反思助手，不称为心理医生 | 当前实现禁止诊断且没有医疗产品所需的临床和危机能力 | Accepted |
| 2026-06-22 | 当前正式前端通过后端调用 LLM | 防止模型密钥与安全规则分散到浏览器；符合活动调用链 | Accepted |
| 2026-06-22 | 链上 Proof 表示提交承诺，不表示任务真实性 | 合约只保存调用者提交的哈希，没有现实世界验证 | Accepted |
| 2026-06-22 | Demo 地址与钱包身份必须在文档中区分 | 手动地址没有所有权证明，只适用于演示 | Accepted |
| 2026-06-22 | SpoonOS 是正式 Agent 流程的硬约束 | 项目要求使用 SpoonOS；后续风险分流、生成、校验和恢复继续由 SpoonOS Graph 编排 | Accepted |
| 2026-06-22 | LLM 不直接拥有业务副作用 | 数据库写入、Proof、交易确认和里程碑由确定性节点控制，降低不可预测输出造成的影响 | Accepted |
| 2026-06-22 | 风险分类必须先于输入质量判断 | 避免把短小但危险的表达误判为无意义输入 | Accepted |
| 2026-06-22 | 未通过输入与输出校验的打卡不生成 Proof | 将拒绝发生在链上提交前，避免依赖不存在的链上回滚 | Accepted |
| 2026-06-22 | 链上确认后使用撤销或替代语义，不称为回滚 | 区块链历史不可删除，只能追加补偿状态 | Accepted |
| 2026-06-22 | 危机路径不更新 streak、不生成 Proof 或 NFT | 危机表达不是常规成长任务，不应被游戏化或铸造成奖励 | Accepted |
| 2026-06-22 | 长期记忆默认不保存日记原文 | 日记高度敏感；仅在明确授权后保存可查看、可删除的结构化偏好 | Accepted |
| 2026-06-22 | SpoonOS Graph Checkpoint 使用项目 SQLite adapter | SpoonOS 0.4.10 Graph 默认 Checkpointer 仅内存保存；项目已有 SQLite，使用同一数据库可在进程重启后恢复且无需新增基础设施 | Accepted |
| 2026-06-22 | 数据库副作用失败后由相同 `checkinId` 显式恢复 | 数据库写入不能后台盲目重试；稳定幂等键让调用方可安全重放，并能检测同 ID 不同请求的冲突 | Accepted |
| 2026-06-22 | 正式身份采用一次性 nonce + EIP-191 签名 + 服务端 session | 当前需求只需要证明地址控制权；该方案接口较小，nonce 单次消费，session token 只保存哈希，后续可迁移到 SIWE | Accepted |
| 2026-06-22 | 客户端 txHash 只作为链查询键，不作为成功证据 | 后端必须从配置 RPC 核对 chain、receipt status、sender、contract 和预期 event 后才更新本地状态 | Accepted |
| 2026-06-22 | Proof 上链采用短期、单次 EIP-191 validator 批准 | 签名绑定合约、链、钱包、日期、Proof、期限和批准 ID；合约与后端都检查单次消费，未通过安全 Graph 的输入不能直接提交 | Accepted |
| 2026-06-22 | revoke/supersede 是后端追加式补偿记录 | 链上历史不可删除；撤销影响产品读取和资格，替代只用于已上链 Proof，且任意替代哈希不会自动获得新批准 | Accepted |
| 2026-06-22 | 临时安全状态由显式幂等维护命令清理 | challenge、session、未消费批准和 Checkpoint 不应无限增长；完成 Checkpoint 保留 7 天、未完成保留 30 天，已消费批准和业务记录不删除 | Accepted |
| 2026-06-23 | NFT 图片 Prompt 只使用公开任务视觉元数据 | 图片供应商不需要日记或 Reflection 即可生成装饰性资产；钱包 session 与日志所有权只用于授权，不进入 Prompt | Accepted |
| 2026-06-23 | 里程碑 tokenId 和 metadata URI 由后端准备 | tokenId 同时参与前端交易和后端事件验证，必须只有一个规范算法；前端不得使用时间戳或随机值 | Accepted |
| 2026-06-24 | 每日完成链路绑定页面当前 `DailyLog` 的 `logId` | Proof 批准、链上 Proof 确认和 Day NFT 确认必须指向同一条持久化日志，避免前端在交易前后重新选择“当前日期”导致状态写入另一条记录 | Accepted |
| 2026-06-24 | `/health` 暴露生产配置 readiness，但不替代链上 receipt 校验 | 配置完整性和链上事实是两层检查；缺少 RPC、合约地址、metadata URI 或 validator 私钥时应提前暴露 `ready=false`，但交易成功仍必须由确认接口验证 receipt、sender、contract 和 event | Accepted |
| 2026-06-24 | 前端只保留一个正式后端调用 seam | 旧浏览器端 mock/Agent、本地 mock store 和根目录 `frontend/lib` 平行实现与后端 SpoonOS Graph 规则冲突，删除后把 LLM、安全校验和业务状态的 locality 固定在后端 | Accepted |

## 待决定

- 日记是否服务端加密，以及密钥和删除权由谁控制。
- 危机输入是仅显示地区化资源，还是需要人工升级能力。
- 是否保留可转让 Day NFT；原始产品叙事曾使用 SBT，但当前合约允许转让。
- 是否把 revoke/supersede 进一步同步为链上补偿事件，使合约读取也能阻止后续 Day/Final NFT。
- Proof 撤销是否需要管理员复核或用户申诉流程。

待决定项只有在用户或项目负责人明确选择后，才转成 Accepted 决策。
