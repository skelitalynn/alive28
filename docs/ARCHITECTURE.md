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
- `backend/app/graph/nodes.py`：任务读取、反思、Proof、进度和报告节点。
- `backend/app/services/reflection.py`：Reflection Prompt、JSON 提取、截断和 fallback。
- `backend/app/services/report.py`：周报与结营报告生成。
- `backend/app/services/nft_image.py`：Pollinations、Gemini 和 SVG fallback。
- `backend/app/models.py`：`UserProgress` 与 `DailyLog`。
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

- `ProofRegistry.sol`：每个地址、每天只保存一次 `bytes32` Proof。
- `RestartBadgeNFT.sol`：存在 Proof 时铸造 Day NFT，28 个 Day NFT 后铸造 Final NFT。
- `MilestoneNFT.sol`：用户为自己铸造指定 token ID 与 URI。

后端数据库和链上状态目前是两套状态来源，后端通过客户端上报的 `txHash` 更新本地记录。

## 主要调用链

### 每日打卡

```text
POST /checkin
  -> DailyPrompt
  -> UserInput normalization
  -> Reflection LLM
  -> ProofBuilder
  -> ProgressUpdate / SQLite commit
  -> BadgeCheck
  -> CheckinResponse
```

同一地址、挑战和日期由数据库唯一约束保持幂等。非 Demo 模式下，`dateKey` 使用当前日期；Demo 模式根据 `dayIndex` 推导日期。

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
Browser sends transaction
  -> client submits txHash to backend
  -> backend writes submitted/minted state
```

当前后端没有查询链上 receipt、sender、contract 或 event，因此该确认链路不能作为可信证据。

## 数据与隐私

`DailyLog` 当前保存：

- 地址、日期、任务天数。
- 标准化后的日记原文。
- AI Reflection。
- salt、输入哈希和 Proof 哈希。
- 可选交易哈希。

已确认的风险：

- 日记以明文保存在 SQLite。
- LLM 与图片生成 adapter 会接收用户内容。
- Pollinations Prompt 被编码进 URL。
- 仅凭地址即可查询或修改关联数据，没有签名认证。

涉及日记、身份或外部模型的修改必须先阅读 `docs/PROGRESS.md` 的安全阻塞项。

## LLM 输出约束现状

现有实现包含 Prompt 约束、JSON 提取、字段存在检查、最大长度截断和 fallback。
它尚未包含：

- 输入风险分类。
- 严格的字段类型、最小长度和禁止额外字段验证。
- 自伤、他伤或医疗场景的专用路由。
- Prompt 注入与语义安全校验。
- 模型、Prompt 版本和 fallback 指标。
- 面向边界输入的回归评测集。

因此，Pydantic 响应模型不能被视为完整的 LLM 安全 Seam。

## 目标打卡工作流

后续目标 Graph：

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

每次打卡使用稳定的 `thread_id` 或 `checkin_id`。Checkpoint 至少应记录：

- 已完成节点。
- 风险和质量判断。
- 生成结果与校验错误。
- 修复次数。
- 是否已经持久化。

生产环境需要持久化 Checkpointer；内存实现只适合测试。

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
