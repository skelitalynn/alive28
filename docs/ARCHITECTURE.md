# 系统架构

## 系统概览

```text
Browser / Wallet
       |
       v
Next.js frontend
       |
       | HTTP JSON
       v
FastAPI backend
  |       |        |
  v       v        v
SQLite  SpoonOS  Image providers
                    |
Wallet ---------- Solidity contracts
```

当前活动前端入口在 `frontend/src/lib/api/index.ts`，固定使用 `httpClient` 调用后端。后端负责业务状态、LLM 调用和报告生成；浏览器负责钱包交互和交易发起。

## 模块职责

### 前端

- `frontend/src/app/`：首页、每日任务、进度、报告和里程碑页面。
- `frontend/src/components/`：地址、钱包和共享 UI。
- `frontend/src/lib/api/httpClient.ts`：后端请求和钱包交易调用。
- `frontend/src/lib/nft/`：里程碑元数据与铸造辅助逻辑。
- `frontend/src/lib/store/`：旧的本地模拟存储实现；当前正式入口不使用它。

`mockClient.ts`、`spoonClient.ts`、`spoonAgent.ts` 和 `frontend/lib/api.ts` 当前不在活动调用链，属于待清理的历史实现。

### 后端

- `backend/app/routes.py`：HTTP 接口、输入基础检查和响应映射。
- `backend/app/graph/agent.py`：固定工作流和条件跳转。
- `backend/app/graph/nodes.py`：任务读取、风险与质量分流、Reflection 校验与修复、Proof、进度和报告节点。
- `backend/app/services/reflection_safety.py`：输入风险规则、SpoonOS 结构化分类、Prompt 注入和输入质量判断。
- `backend/app/services/reflection.py`：Reflection Prompt、严格 Schema、语义校验、受限重试、修复和 fallback。
- `backend/app/services/checkpoint.py`：兼容 SpoonOS Graph 接口的 SQLite 持久化 Checkpointer。
- `backend/app/services/auth.py`：一次性钱包 challenge、EIP-191 签名恢复和服务端 session。
- `backend/app/services/chain.py`：RPC receipt、sender、contract、chain 和 event 验证。
- `backend/app/services/proof_approval.py`：短期 validator 批准签名、有效 Proof 选择和待处理批准失效。
- `backend/app/services/cleanup.py`：过期 challenge/session/批准和超出保留期的 Graph Checkpoint 清理。
- `backend/app/services/report.py`：周报与结营报告生成。
- `backend/app/services/nft_image.py`：仅使用公开 Day/任务视觉元数据的 Pollinations、Gemini 和 SVG fallback。
- `backend/app/models.py`：业务记录、Graph Checkpoint、钱包 challenge 与 session。
- `backend/app/data/tasks.json`：28 天任务内容。

Graph 是确定性工作流。LLM 只参与 Reflection 和报告文本，不控制数据库查询、Proof 计算或里程碑规则。

### SpoonOS 硬约束

项目后续实现必须继续以 SpoonOS 作为 Agent 框架：

- 使用 SpoonOS `StateGraph` 表达打卡流程、风险分流和失败恢复。
- 使用 SpoonOS 模型或 Agent 抽象执行 Reflection 与结构化分类。
- 工具调用、记忆、Checkpoint 和节点重试优先采用 SpoonOS 已提供的机制。
- 如果当前安装版本缺少某项能力，可以在 SpoonOS Graph 节点内部实现 adapter，但不能绕开 Graph 建立第二套正式 Agent 流程。
- 前端不建立与后端并行的正式 Agent；浏览器只调用后端。

使用 SpoonOS 不意味着所有逻辑都交给 LLM。数据库写入、Proof 生成、交易验证和状态转换保持确定性。

### 合约

- `ProofRegistry.sol`：只接受 validator 对合约、链、用户、日期、Proof、期限和单次批准 ID 的绑定签名；每个地址、每天只保存一次 `bytes32` Proof。
- `RestartBadgeNFT.sol`：存在 Proof 时铸造 Day NFT，28 个 Day NFT 后铸造 Final NFT。
- `MilestoneNFT.sol`：用户为自己铸造指定 token ID 与 URI。

后端数据库和链上状态目前是两套状态来源，后端通过客户端上报的 `txHash` 更新本地记录。

### 钱包身份

非 Demo 模式的地址相关 API 使用以下流程：

```text
POST /auth/nonce(address)
  -> 一次性 challenge（5 分钟）
Wallet personal_sign(message)
POST /auth/verify(address, signature)
  -> 恢复签名地址
  -> challenge 标记已使用
  -> 返回短期 Bearer session
Address API
  -> session 有效且绑定地址一致
```

服务端只保存 session token 的 SHA-256，不保存明文 token。前端 token 保存在
`sessionStorage`，钱包断开或 API 返回 401 时清除。Demo 模式仍允许手动地址，但该地址不代表钱包所有权。

## 主要调用链

### 每日打卡

```text
POST /checkin
  -> DailyPrompt
  -> UserInput normalization
  -> RiskClassify
  -> CrisisResponse / InputQuality
  -> ClarificationResponse / RejectedInput / Reflection LLM
  -> ValidateReflection
  -> RepairReflection (最多一次) / FallbackReflection
  -> ProofBuilder（仅 accept 路径）
  -> ProgressUpdate / SQLite 单事务提交
  -> BadgeCheck
  -> CheckinResponse
```

同一地址、挑战和日期由数据库唯一约束保持幂等。风险、澄清和拒绝路径在 Proof 与持久化之前结束。非 Demo 模式下，`dateKey` 使用当前日期；Demo 模式根据 `dayIndex` 推导日期。

每次打卡还使用稳定 `checkinId` 作为 SpoonOS `thread_id`：

```text
POST /checkin(checkinId)
  -> SQLiteGraphCheckpointer 读取最新快照
  -> 无快照：从 DailyPrompt 开始
  -> 未完成快照：Command(resume=...) 从 next node 继续
  -> 已完成快照：返回幂等结果
```

快照在节点执行前持久化。节点失败时额外记录失败节点、错误摘要和尝试次数；恢复时注入新的短生命周期数据库 Session，不把 Session 序列化。成功结束后清理中间快照，只保留移除日记原文、salt 和 Proof 的紧凑完成快照。

### 报告

```text
GET /report
  -> WeeklyReport or FinalReport
  -> read DailyLog records
  -> LLM abstract summary
  -> deterministic fallback on failure
```

### 链上确认

```text
POST /proof/approval(logId)
  -> require wallet session and owned persisted DailyLog
  -> require ACTIVE safety-approved proof and no confirmed tx
  -> return short-lived validator signature and persisted dayIndex
Browser sends submitProof(dayIndex, proofHash, deadline, approvalId, signature)
  -> client submits txHash to backend
  -> backend queries configured RPC
  -> verify configured chain and successful receipt
  -> verify transaction sender and target contract
  -> verify ProofSubmitted event includes the approved proof and approvalId
  -> mark the approval consumed and write submitted state
  -> backend returns the updated DailyLog
Browser sends mintDay(dayIndex) for that same log
  -> client submits txHash to backend with logId
  -> backend verifies Day NFT event against the persisted log dayIndex
  -> backend records the day NFT receipt and returns the updated DailyLog
```

客户端提交的 `chainId`、`contractAddress` 和 `address` 均为不可信输入。RPC 不可用、交易回滚、发送者不匹配、目标合约错误或事件内容错误时，本地状态不改变。

前端不得在 Proof 提交或 Day NFT 确认之间重新按“当前日期”选择日志。页面显示哪条 `DailyLog`，后续批准、链上确认和进度刷新就必须绑定同一个 `logId`；后端以持久化日志中的 `day_index` 校验链上事件，并把更新后的同一条日志返回给前端。

里程碑 NFT 使用后端准备流程：

```text
POST /milestone/prepare(address, milestoneId)
  -> verify wallet session and completed eligible days
  -> derive tokenId = keccak256(address bytes + one-byte milestoneId)
  -> return canonical tokenId and metadata URI
Browser mints exactly tokenId + tokenUri
POST /milestone/mint(txHash)
  -> verify Transfer event contains the same canonical tokenId
  -> record milestone idempotently
```

前端不再生成随机或时间相关 tokenId，避免链上成功但后端因事件值不一致而拒绝确认。

### Proof 补偿

`POST /proof/compensate` 只追加 `ProofCompensation` 审计记录，不删除原交易或原始 Proof：

- `REVOKE` 可用于待提交或已提交记录，会使所有未消费批准失效；该记录不再参与进度、报告、Day NFT 本地确认或里程碑资格计算。
- `SUPERSEDE` 只允许用于已经上链的 Proof，记录产品层认可的替代哈希；它不会为任意替代哈希签发新的链上批准。
- `DailyLog.tx_hash` 和链上历史保持不变，因此该流程是补偿，不是回滚。

当前 revoke/supersede 状态存放在后端产品读取模型中，并不删除已存在的链上 Proof 或已经铸造的 NFT。若要求合约本身阻止撤销后的后续铸造，需要后续增加链上补偿事件和合约状态读取。

## 数据与隐私

`DailyLog` 当前保存：

- 地址、日期、任务天数。
- 标准化后的日记原文。
- AI Reflection。
- salt、输入哈希和 Proof 哈希。
- 可选交易哈希。

当前约束：

- 日记以明文保存在 SQLite。
- Reflection 与报告 LLM 会接收完成其职责所需的用户内容。
- NFT 图片生成必须使用钱包 session 和用户拥有的 `DailyLog`，但第三方 Prompt 只包含公开 Day、任务标题和阶段配色，不包含日记、Reflection、地址、Proof 或客户端自由文本。
- Pollinations Prompt 仍编码进 URL，因此只允许发送公开视觉元数据。
- Session token 当前由浏览器 `sessionStorage` 保存，仍需要配合生产 HTTPS、严格 CORS 和 XSS 防护。

涉及日记、身份或外部模型的修改必须先阅读 `docs/PROGRESS.md` 的安全阻塞项。

## LLM 输出约束现状

当前 Reflection Safety Seam 包含：

- 明确危机规则优先、模糊风险由 SpoonOS `ChatBot` 结构化分类补充。
- Prompt 注入、重复字符、纯链接和过薄输入判断。
- `note` 与 `next` 的严格类型、长度和禁止额外字段校验。
- 诊断、用药和保证性承诺等语义禁区。
- 临时模型故障受限重试，非法内容最多修复一次，再进入审核过的确定性 fallback。
- 危机、澄清和拒绝路径不生成 Proof、不写日志、不更新 streak。
- 覆盖否定风险表达、短有效输入、修复、fallback 和事务回滚的集成测试。

当前响应还包含 Prompt/模型版本、模型调用次数、修复次数、fallback 原因、节点耗时、节点尝试次数和最后错误摘要。

仍未完成：集中式指标后端、专业审核的危机资源和更完整的离线评测集。

## 当前打卡工作流

当前 SpoonOS Graph：

```text
DailyPrompt
    |
NormalizeInput
    |
RiskClassify
    |-------------------------------|
    | crisis                       | ordinary
    v                              v
CrisisResponse                InputQualityCheck
    |                         | clarify/reject
    |                         v
    |                    ClarificationResponse
    |                              |
    | accept                       END
    |
    v
GenerateReflection
    |
ValidateReflection
    | valid
    |-------------------------------|
    | invalid                       |
    v                               |
RepairReflection                    |
    |                               |
ValidateReflectionAfterRepair       |
    | valid              | invalid  |
    |                    v          |
    |              FallbackReflection
    |____________________|__________|
                         |
                  BuildPendingProof
                         |
                   PersistCheckin
                         |
                    ProgressUpdate
                         |
                     BadgeCheck
```

关键规则：

- 风险分类先于输入质量判断。危险的短输入不能被当作“无意义输入”拒绝。
- 危机路径不生成 Proof、不更新 streak、不触发 NFT。
- `clarify` 和 `reject` 只返回引导信息，不创建正式 `DailyLog`。
- 只有通过输出校验或使用审核过的普通 fallback，才能进入 Proof 和持久化节点。
- 所有数据库写入应集中在一个事务中。
- Graph 节点返回状态，不在多个节点中随意 `commit()`。

详细字段、节点职责和实施顺序见 `docs/IMPLEMENTATION_PLAN.md`。

## Agent 能力的目标用法

### 工具调用

允许 Agent 使用的工具应按权限分级：

- 只读：读取当天任务、读取授权后的历史摘要、查询链上 receipt、获取地区化援助资源。
- 受控写入：只能由确定性 Graph 节点调用，例如保存日志和更新进度。
- 禁止直接开放给 LLM：签名私钥、任意数据库写入、任意交易发送、里程碑授予。

LLM 可以提出工具调用参数，但 Graph 必须校验参数、调用结果和后续状态转换。

### 记忆

需要区分：

- Graph State：一次执行中的短期状态。
- Checkpoint：一次执行的可恢复快照。
- `DailyLog`：业务记录，不等同于 Agent 记忆。
- 长期记忆：用户明确授权后保存的结构化偏好。

长期记忆不得默认保存日记原文。优先保存诸如“偏好写作型动作”“不希望收到社交建议”的结构化信息，并支持查看、删除和撤回授权。

### Checkpoint

当前每次打卡使用稳定 `checkinId` 作为 SpoonOS `thread_id`。Checkpoint 记录：

- 已完成节点。
- 风险和质量判断。
- 生成结果与校验错误。
- 修复次数。
- 是否已经持久化。
- 节点耗时、尝试次数和最后错误。

当前持久化后端是项目 SQLite。相同 `checkinId` 只能恢复原请求，不同输入会返回 `409 CHECKIN_ID_CONFLICT`。数据库副作用失败后不自动盲目重试，由调用方用同一请求显式恢复。

临时状态通过显式维护命令清理：

- 已完成 Checkpoint 默认保留 7 天。
- 失败或未完成 Checkpoint 默认保留 30 天，给显式恢复留出更长窗口。
- 已过期钱包 challenge、已过期或已撤销 session、已过期且未消费的 Proof 批准可立即清理。
- 已消费批准、`DailyLog`、`ProofCompensation` 和链上确认字段不属于临时状态，不由该任务删除。
- `--dry-run` 使用与实际清理相同的候选选择逻辑，但不执行数据库写入。

### 重试

只重试临时故障：

- 网络超时。
- 429。
- 模型供应商 5xx。

内容不合格进入 Repair 节点，不归类为网络重试。数据库写入和链上交易必须幂等，不能盲目重试。

建议默认值：

- LLM 调用超时 20 秒。
- 临时故障最多重试 2 次。
- 指数退避并加入随机抖动。
- 输出修复最多 1 次。
- 达到上限后进入确定性 fallback。

## 目标链上工作流

链上不可回滚，因此验证必须发生在提交之前：

```text
输入
  -> 风险分类
  -> 质量判断
  -> Reflection 生成与校验
  -> 数据库事务成功
  -> 签发可上链批准凭证
  -> 用户提交交易
  -> 后端验证 receipt、sender、contract、event
  -> 本地状态确认
```

无意义输入在“签发批准凭证”之前停止，不存在链上回滚。

链上确认后发现问题时，只能采用补偿语义：

- `revoked`：该 Proof 后续不再被产品承认。
- `superseded`：新 Proof 替代旧 Proof。
- 发出撤销事件并在读取模型中过滤。

历史交易不会消失。

## 当前架构约束

- 正式前端调用通过后端；不要把模型密钥或正式 LLM 调用放入浏览器。
- LLM 输出在持久化和展示前必须经过后端校验。
- 客户端提供的地址和交易哈希均为不可信输入。
- 链上 Proof 是提交承诺，不是任务真实性或心理状态证明。
- `tasks.json` 是每日任务的唯一内容源。
- 数据库模型变化必须提供迁移方案或明确的本地重建步骤。

## 待自动化规则

以下问题已经出现，但尚未转成自动检查：

- 前端存在未使用且规则冲突的 Agent 实现。
- 多个源码文件曾出现编码损坏。
- API 类型和后端响应存在漂移风险。
- 数据库仅使用 `create_all`，没有迁移门禁。
