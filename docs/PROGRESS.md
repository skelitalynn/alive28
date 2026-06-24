# 当前进度

更新时间：2026-06-24

## 当前目标

`F-009 Persisted Daily Completion Loop` 已完成实现与目标验证。每日主链路现在绑定页面正在展示的同一条持久化 `DailyLog`：Proof 批准、链上 Proof 确认、Day NFT 确认和进度刷新都使用同一个 `logId`，不再重新按“当前日期”选择另一条日志。

`F-010 Production Readiness Gate` 已完成实现与目标验证：非 Demo 模式通过 `/health` 暴露生产配置就绪状态，并在前端钱包交易前拒绝零地址合约配置。

`F-011 Frontend Legacy Adapter Cleanup` 已完成代码清理与目标验证：正式前端只保留 `src/lib/api/index.ts -> httpClient` 这一条后端调用 seam，旧浏览器端 mock/Agent、本地 mock store 和根目录 `frontend/lib` 平行实现已删除。

`F-012 Frontend Browser Smoke` 已完成实现与目标验证：新增浏览器级 smoke 脚本，使用受控 mock backend 驱动真实 Next.js UI，覆盖 Demo 身份、首页进入 Day 1、提交有意义打卡、展示 Reflection、跳转进度页并看到 Day 1 完成。

## 最近完成

- 建立 `docs/README.md` 单一文档入口。
- 将原 README、启动、测试和问题清单迁移到职责明确的文档。
- 安装 WIP=1、任务状态、验证证据和会话交接脚本。
- `F-001` 文档路由验证通过；证据路径记录在 `docs/FEATURES.json`。
- 新增 `IMPLEMENTATION_PLAN.md`，明确 SpoonOS 硬约束、Agent 能力、Reflection Safety、链前拒绝、链后补偿、隐私和分阶段实施方案。
- 使用 SpoonOS `StateGraph` 实现风险分类、输入质量、危机分流、Reflection 生成、输出校验、单次修复和安全 fallback。
- `clarify`、`rejected` 与 `crisis_redirected` 不创建 `DailyLog`、Proof 或进度记录。
- Reflection 采用严格 Pydantic Schema 和诊断、用药、保证性承诺等语义禁区校验。
- LLM 临时网络故障最多重试两次；内容不合格进入独立 Repair 节点，最多修复一次。
- 打卡日志与进度改为单事务提交，持久化失败时不留下孤立进度。
- 前端已处理安全分流响应，不再把无日志结果误判为成功打卡。
- 使用稳定 `checkinId` 作为 SpoonOS `thread_id`，并通过 SQLite 持久化节点前快照。
- 数据库节点失败后，相同请求可从失败节点恢复，不会重新生成 Reflection 或重复增加 streak。
- 同一未完成 `checkinId` 被不同输入复用时返回 `409 CHECKIN_ID_CONFLICT`。
- Checkin 响应包含 Prompt/模型版本、模型调用次数、节点耗时、节点尝试次数、修复和 fallback 信息。
- 完成后仅保留紧凑 Checkpoint，不保存日记原文、salt、输入哈希或 Proof。
- 非 Demo 模式使用一次性 nonce 和 EIP-191 钱包签名建立地址绑定 session。
- 地址相关 API、Reflection 和 NFT 图片生成接口均要求有效 session；Demo 手动地址继续保留。
- 前端连接钱包后先签名认证，再向页面暴露地址；token 仅保存在 `sessionStorage`。
- Proof、Day/Final NFT 和 Milestone 确认会通过配置 RPC 核对 chain、receipt、sender、contract 和 event。
- 伪造地址、重复 nonce、伪造 txHash 或错误事件不会改变本地状态。
- 只有持久化且仍为 `ACTIVE` 的安全打卡可以获得短期 validator 批准；签名绑定合约、链、钱包、日期、Proof、期限和批准 ID。
- ProofRegistry 拒绝无效、过期和重复批准；后端在可信 receipt 确认后把批准标记为已消费。
- revoke/supersede 追加补偿审计，不删除链上交易；待处理批准会失效。
- 被撤销记录不再参与进度、报告、Day NFT 本地确认或里程碑资格；替代哈希不会绕过安全 Graph 获得新批准。
- 新增可 dry-run、可重复执行的临时状态清理服务和运维命令。
- NFT 图片接口只接受用户拥有的日志引用；第三方 Prompt 仅使用公开 Day、任务标题和阶段配色。
- 里程碑准备接口统一资格检查、tokenId 和 metadata URI；前端铸造与后端事件验证使用同一 tokenId。
- 每日完成闭环已绑定持久化日志 ID；前端 Proof 提交和 Day NFT mint 都传递页面当前 `logId`，后端确认后返回更新后的同一条日志，避免用户界面和链上确认指向不同记录。
- `/health` 已返回结构化 readiness；非 Demo 缺少 RPC、合约地址、metadata URI 或 validator 私钥时 `ready=false` 并列出 blocking issues。前端交易 helper 会在请求钱包前拒绝零地址或非法合约地址。
- 前端旧 mock/Agent Adapter、本地 mock store 和 `frontend/lib` 平行 API/ABI 实现已删除；新增 Harness 检查防止这些文件或引用回流。
- 新增 `scripts/e2e/frontend_smoke.mjs`，在独立 mock backend 下启动真实 Next.js 前端，验证主页面、每日页和进度页的浏览器闭环；该 mock 只存在于测试脚本，不恢复浏览器端业务 mock/Agent seam。
- 修复每日打卡主页面的历史乱码，并为关键 UI 节点增加稳定测试标识。

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

- 日记原文明文保存，并发送给 Reflection/报告 LLM。
- Pollinations Prompt 仍在 URL 中传输，但内容已限制为公开视觉元数据。
- 危机分流模板尚未经过专业机构审核，也尚未根据用户地区动态提供资源。
- 风险规则和语义禁区已有回归测试，但仍需要更完整的离线安全评测集。

### P1：工程可靠性

- 后端已有 Reflection Safety 和完整打卡路由集成测试，但其他业务链路覆盖仍少。
- 前端已有浏览器级 smoke 验收；仍缺少组件级、失败态和真实后端联调自动化测试。
- 数据库仍未引入正式迁移工具；F-005 提供一次性 SQLite 迁移脚本。
- 没有 CI。
- 部分源码仍存在历史编码损坏。

### 当前验证基线

2026-06-24：

- SpoonOS SDK 锁定为 `spoon-ai-sdk==0.4.10`。
- 后端测试：38 passed。
- 合约测试：6 passed。
- Next.js 生产构建通过。
- 浏览器级前端 smoke 通过：真实 Next.js UI + 受控 mock backend 覆盖 Demo Day 1 打卡闭环。
- Harness 文档路由检查通过。
- `F-002` 至 `F-012` 的 Harness 证据路径记录在 `docs/FEATURES.json`。

## 下一步建议

1. 为长期记忆增加明确授权、查看、删除和撤回。
2. 决定是否把 Proof 补偿状态同步到链上，阻止撤销后的合约级后续铸造。
3. 实现正式数据库迁移和 CI。
4. 扩展浏览器级测试到失败态、钱包签名态和真实后端联调。

实际执行顺序由 `docs/FEATURES.json` 中唯一的 `active` 功能项决定。
