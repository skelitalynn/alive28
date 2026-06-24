# 本地开发

## 前置条件

- Python 3.11 或更高版本。
- Node.js 和 npm；仓库包含 `frontend/package-lock.json`。
- 可选：Foundry，用于合约构建和测试。
- Git 子模块，用于 OpenZeppelin 和 forge-std。

在仓库根目录初始化子模块：

```powershell
git submodule update --init --recursive
```

## 后端

创建根目录虚拟环境并安装依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
```

编辑 `backend/.env`。非 Demo 模式至少配置可用的 `DEEPSEEK_API_KEY`、`RPC_URL` 和已部署合约地址。启动：

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

健康检查：

```text
GET http://127.0.0.1:8000/health
```

预期结构：

```json
{
  "status": "not_ready",
  "version": "mvp-1.0.0",
  "demo_mode": false,
  "mode": "production",
  "ready": false,
  "checks": {
    "rpcUrl": false,
    "proofRegistryAddress": false,
    "restartBadgeAddress": false,
    "milestoneNftAddress": false,
    "milestoneBaseUri": false,
    "proofApprovalPrivateKey": false
  },
  "blockingIssues": [
    {
      "code": "RPC_URL_MISSING",
      "message": "RPC_URL must point to the chain used for receipt verification."
    }
  ]
}
```

`DEMO_MODE=true` 时 `/health` 不要求链上配置，`ready=true` 且 `mode=demo`。非 Demo 模式下，`ready=false` 表示真实链上闭环不可用，必须先修复 `blockingIssues` 中列出的 RPC、合约地址、metadata URI 或 validator 私钥配置。

### 后端环境变量

| 变量 | 用途 | 示例或默认值 |
|---|---|---|
| `DATABASE_URL` | SQLModel 数据库 | `sqlite:///./alive.db` |
| `DEFAULT_TIMEZONE` | 默认时区 | `Asia/Shanghai` |
| `CHALLENGE_ID` | 当前挑战 ID | `1` |
| `CHAIN_ID` | 后端允许确认的链 | `11155111` |
| `RPC_URL` | receipt/event 查询节点 | 非 Demo 必须配置；占位值会使 `/health.ready=false` |
| `PROOF_REGISTRY_ADDRESS` | ProofRegistry 合约 | 非 Demo 必须是非零部署地址 |
| `RESTART_BADGE_ADDRESS` | Day/Final NFT 合约 | 非 Demo 必须是非零部署地址 |
| `MILESTONE_NFT_ADDRESS` | Milestone NFT 合约 | 非 Demo 必须是非零部署地址 |
| `MILESTONE_BASE_URI` | Milestone metadata 根地址 | 非 Demo 必须替换占位域名 |
| `AUTH_NONCE_TTL_SECONDS` | 签名 challenge 有效期 | `300` |
| `AUTH_SESSION_TTL_SECONDS` | 钱包 session 有效期 | `86400` |
| `PROOF_APPROVAL_PRIVATE_KEY` | ProofRegistry validator 私钥，仅后端持有 | 非 Demo 必须配置为有效私钥 |
| `PROOF_APPROVAL_TTL_SECONDS` | 单次 Proof 批准有效期（秒） | `300` |
| `CHECKPOINT_COMPLETED_RETENTION_SECONDS` | 已完成 Checkpoint 保留期 | `604800`（7 天） |
| `CHECKPOINT_INCOMPLETE_RETENTION_SECONDS` | 未完成/失败 Checkpoint 保留期 | `2592000`（30 天） |
| `DEFAULT_LLM_PROVIDER` | SpoonOS 默认模型供应商 | `deepseek` |
| `DEFAULT_MODEL` | 默认模型 | `deepseek-chat` |
| `DEEPSEEK_API_KEY` | DeepSeek 密钥 | 必须替换示例值 |
| `DEEPSEEK_BASE_URL` | DeepSeek Base URL | `https://api.deepseek.com/v1` |
| `DEMO_MODE` | 是否按选择的 Day 推导日期 | `false` |
| `DEMO_START_DATE_KEY` | Demo 起始日期 | `2026-01-01` |
| `GOOGLE_AI_API_KEY` | Gemini 图片生成 | 可选 |

`DEEPSEEK_MAX_TOKENS`、`DEEPSEEK_TIMEOUT` 等变量由 SDK 读取，不在
`backend/app/config.py` 中直接消费。

### 临时状态清理

先预览候选数量：

```powershell
.\.venv\Scripts\python.exe scripts\maintenance\cleanup.py --dry-run
```

确认后执行：

```powershell
.\.venv\Scripts\python.exe scripts\maintenance\cleanup.py
```

命令可重复执行，适合由 Windows Task Scheduler、cron 或部署平台的定时任务调用。它只删除过期认证材料、过期未消费批准和超出保留期的 Checkpoint，不删除日记、补偿审计、已消费批准或链上确认记录。

### NFT 图片生成

`POST /ai/generate-nft` 只接受：

```json
{"address":"0x...","logId":"..."}
```

该接口始终要求钱包 Bearer session，包括 Demo 模式。服务端从所属日志解析 Day，再从 `tasks.json` 读取公开任务标题；日记原文、Reflection、地址、Proof 和客户端自由 Prompt 不会发送给 Pollinations 或 Gemini。

## 前端

```powershell
Copy-Item frontend\.env.example frontend\.env.local
npm --prefix frontend ci
npm --prefix frontend run dev
```

访问 `http://localhost:3000`。

### 前端环境变量

| 变量 | 用途 |
|---|---|
| `NEXT_PUBLIC_API_BASE` | 后端地址，默认 `http://127.0.0.1:8000` |
| `NEXT_PUBLIC_CHAIN_ID` | 钱包目标链 ID |
| `NEXT_PUBLIC_PROOF_REGISTRY` | ProofRegistry 地址 |
| `NEXT_PUBLIC_BADGE_NFT` | RestartBadgeNFT 地址 |
| `NEXT_PUBLIC_MILESTONE_NFT` | MilestoneNFT 地址 |

未部署合约时不要执行真实链上按钮。前端会在发起钱包交易前拒绝零地址或非法合约地址配置；后端 `/health.ready=false` 时说明生产链路尚未就绪。

## 本地 MVP 路径

1. 打开 `http://localhost:3000`。
2. 非 Demo 模式连接钱包并签署登录 challenge；Demo 模式可使用手动/随机地址。
3. 进入 `/daily/1`。
4. 输入感受并点击“生成反馈”。
5. 打开 `/progress` 和 `/report` 检查数据。

手动地址只在 `DEMO_MODE=true` 时展示，不具备认证能力。

## 合约

```powershell
Set-Location contracts
forge build
forge test
```

部署前复制 `contracts/.env.example` 并配置 RPC 与私钥。示例：

```powershell
$env:RPC_URL = "https://..."
$env:PRIVATE_KEY = "..."
$env:PROOF_VALIDATOR = "0x..."
$env:NFT_BASE_URI = "https://..."
forge script script/Deploy.s.sol --rpc-url $env:RPC_URL --private-key $env:PRIVATE_KEY --broadcast
```

`PROOF_VALIDATOR` 必须等于后端 `PROOF_APPROVAL_PRIVATE_KEY` 派生出的地址。部署后把地址同步到后端和 `frontend/.env.local`。私钥和真实环境文件不得提交。

非 Demo 里程碑铸造会先调用 `POST /milestone/prepare`。确保后端
`MILESTONE_BASE_URI` 是公开可访问的 metadata 根地址；前端会原样使用后端返回的
`tokenId` 和 `tokenUri` 发起交易。

## 数据库

后端启动时调用 `SQLModel.metadata.create_all()`，不会迁移已有表。

本地无保留价值的数据可以删除 `backend/alive.db` 后重建。需要保留数据时，必须执行明确 SQL 迁移或引入迁移工具；不要依赖 `create_all()` 修改已有表。

F-005 为 `dailylog` 增加 Proof 补偿字段。保留已有 SQLite 数据时，启动新代码前执行一次：

```powershell
sqlite3 backend\alive.db ".read backend/migrations/20260622_f005_proof_approval.sql"
```

随后首次启动会通过 `create_all()` 创建 `proofapproval` 与 `proofcompensation` 新表。执行迁移前先备份数据库；全新或可丢弃的本地数据库直接重建即可。

历史字段变更曾要求：

```sql
ALTER TABLE dailylog ADD COLUMN day_nft_tx_hash VARCHAR(66);
```

执行前应先检查实际表结构。

## 常见问题

- `ModuleNotFoundError: sqlmodel`：使用项目虚拟环境安装 `backend/requirements.txt`。
- `next is not recognized`：执行 `npm --prefix frontend ci`。
- Foundry 找不到 OpenZeppelin 或 forge-std：初始化 Git 子模块。
- `/checkin` 返回 500：检查后端日志、模型密钥和 SpoonOS 配置。
- 页面请求失败：确认后端运行且 `NEXT_PUBLIC_API_BASE` 正确。
- 中文乱码：文件必须保存为 UTF-8；不要通过错误编码批量重写源码。
