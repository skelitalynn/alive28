# HOPE 小希 · 28 天心灵成长之旅

> 基于 SpoonOS 的 AI Agentic Framework，陪伴用户完成 28 天成长挑战。
> 它不是鸡汤，而是一套可执行的「人生重启协议」：当意志波动时，让系统接管流程、记录与反馈。

## 亮点

- 28 天打卡路径 + AI Reflection 反馈
- 进度、周报、结营报告可视化
- 里程碑 NFT（可选上链；DEMO 模式仅记录）
- 钱包连接（wagmi）或手动地址两种身份

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Next.js 14、React、TypeScript、wagmi/viem、TailwindCSS、ECharts |
| 后端 | FastAPI、SQLModel、SpoonOS Graph Agent（spoon-ai-sdk）、DeepSeek LLM |
| 合约 | Solidity、Foundry（可选部署） |
| 数据库 | SQLite（默认） |

## 快速开始

### 后端

```bash
# 建议使用项目根目录的 .venv
cd backend
pip install -r requirements.txt
# 复制 backend/.env.example 为 backend/.env，填写 DEEPSEEK_API_KEY 等
uvicorn app.main:app --reload
```

健康检查：`GET http://127.0.0.1:8000/health`

### 前端

```bash
cd frontend
npm install
# 复制 frontend/.env.example 为 frontend/.env 或 .env.local
# 至少设置 NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
npm run dev
```

访问：`http://localhost:3000`

## 配置

### 后端环境变量（`backend/.env`）

| 变量 | 说明 | 默认 |
|------|------|------|
| DATABASE_URL | 数据库连接 | sqlite:///./alive.db |
| DEFAULT_TIMEZONE | 默认时区 | Asia/Shanghai |
| DEEPSEEK_API_KEY | DeepSeek API Key | 必填 |
| DEEPSEEK_BASE_URL | DeepSeek 接口地址 | https://api.deepseek.com/v1 |
| DEMO_MODE | 演示模式 | false |
| DEMO_START_DATE_KEY | 演示模式起始日期 | 可选 |

### 前端环境变量（`frontend/.env` 或 `.env.local`）

| 变量 | 说明 | 默认 |
|------|------|------|
| NEXT_PUBLIC_API_BASE | 后端 API 地址 | http://127.0.0.1:8000 |
| NEXT_PUBLIC_CHAIN_ID | 链 ID（上链时） | 11155111 |
| NEXT_PUBLIC_PROOF_REGISTRY | ProofRegistry 合约地址 | 0x... |
| NEXT_PUBLIC_BADGE_SBT | RestartBadgeSBT 合约地址 | 0x... |
| NEXT_PUBLIC_MILESTONE_NFT | 里程碑 NFT 合约地址 | 0x... |

前端通过 `GET /health` 的 `demo_mode` 与后端同步：DEMO 模式下里程碑页仅记录不上链；非 DEMO 模式下连接钱包需上链铸造。

## 目录结构

```
project/
├── backend/          # FastAPI + Graph Agent + SQLModel
│   ├── app/
│   │   ├── config.py
│   │   ├── routes.py
│   │   ├── graph/    # SpoonOS Graph Agent 节点
│   │   ├── services/ # reflection / report / nft_image / tasks / time
│   │   └── ...
│   ├── requirements.txt
│   └── .env.example
├── frontend/         # Next.js + wagmi
│   ├── src/
│   │   ├── app/      # 页面：首页、daily/[dayIndex]、progress、report、milestone/[id]
│   │   ├── components/
│   │   └── lib/      # api、store、nft、wagmi
│   ├── public/nft/   # 里程碑 NFT 图片：week1.svg, week2.svg, final.svg
│   └── .env.example
├── contracts/        # Foundry 合约
├── docs/             # 启动与测试文档
└── README.md
```

## 页面与功能

| 页面 | 说明 |
|------|------|
| `/` | 欢迎页、当前 Day 入口、进度/周报入口 |
| `/daily/[dayIndex]` | 当日任务、输入感受、Reflection 反馈、保存记录、完成今日（可铸 Day SBT） |
| `/progress` | 连续天数、已完成天数、可铸造日、里程碑资格 |
| `/report` | 周报（range=week）、结营报告（range=final），含图表 |
| `/milestone/1|2|final` | 7 / 14 / 28 天里程碑，展示或铸造对应 NFT |

身份：支持钱包连接（wagmi）或手动输入地址；断开钱包后清空本地身份并跳回首页。

## 后端 API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /health | 健康检查，返回 version、demo_mode |
| GET | /dailyPrompt | 每日任务（dayIndex, timezone） |
| GET | /homeSnapshot | 首页快照（address） |
| GET | /dailySnapshot | 某日快照（address, dayIndex） |
| POST | /checkin | 打卡（address, dayIndex, text 等） |
| POST | /tx/confirm | Proof 上链交易确认（写回 DailyLog.tx_hash） |
| POST | /sbt/confirm | Day/Final SBT 铸造确认（写回 day_sbt_tx_hash 或 final_sbt_tx_hash） |
| POST | /milestone/mint | 里程碑铸造记录 |
| GET | /progress | 进度（address） |
| GET | /report | 周报/结营报告（address, range） |
| GET | /metadata/{token_id}.json | NFT 元数据（可选） |
| POST | /ai/reflection | AI 反馈（可选独立接口） |
| POST | /ai/generate-nft | AI 生成 NFT 图（可选） |

## 运行模式

- `DEMO_MODE=true`：前端从 `/health` 读取 `demo_mode`。
- `DEMO_MODE=false`：连接钱包时需上链铸造（生产/测试网）。

## 可选：合约部署与上链流程

### 部署合约（Foundry）

```bash
cd contracts
# 安装依赖（若未安装）
forge install OpenZeppelin/openzeppelin-contracts
# 复制 .env.example 为 .env，填写 PRIVATE_KEY、RPC_URL（如 Sepolia）
cp .env.example .env
# 可选：SBT_BASE_URI 用于 RestartBadgeSBT 的 tokenURI 前缀
forge script script/Deploy.s.sol --rpc-url $env:RPC_URL --private-key $env:PRIVATE_KEY --broadcast
```

部署后会输出三个地址：ProofRegistry、RestartBadgeSBT、MilestoneNFT。

### 配置前端与后端

**前端 `frontend/.env` 或 `.env.local`：**

```
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
NEXT_PUBLIC_CHAIN_ID=11155111
NEXT_PUBLIC_PROOF_REGISTRY=<ProofRegistry 地址>
NEXT_PUBLIC_BADGE_SBT=<RestartBadgeSBT 地址>
NEXT_PUBLIC_MILESTONE_NFT=<MilestoneNFT 地址>
```

**后端**：关闭 DEMO 模式时设 `DEMO_MODE=false`，前端读取 `demo_mode` 后里程碑页会要求上链铸造。

### 上链流程（用户侧）

1. **每日打卡**：输入感受 → 生成反馈 → 保存记录 → 连接钱包后上链提交 → POST `/tx/confirm`。
2. **完成今日**：当日已提交 Proof 后，调用 `RestartBadgeSBT.mintDay(dayIndex)` → POST `/sbt/confirm`（type=DAY, dayIndex）。
3. **结营**：28 天 Day SBT 均已铸造后，调用 `RestartBadgeSBT.composeFinal()` → POST `/sbt/confirm`（type=FINAL）。
4. **里程碑 NFT**：达到 7/14/28 天后，调用 `MilestoneNFT.mint(to, tokenId, tokenURI)` → POST `/milestone/mint`。

## 数据库提示（旧库升级）

后端新增字段 `DailyLog.day_sbt_tx_hash`。若使用已有 `alive.db`，需删除 `backend/alive.db` 后重启后端让其重建表，或执行：

```sql
ALTER TABLE dailylog ADD COLUMN day_sbt_tx_hash VARCHAR(66);
```

## 文档

- 本地启动与测试步骤：`docs/startup.md`
