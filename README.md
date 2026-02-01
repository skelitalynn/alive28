# HOPE小希 · 28天心灵成长之旅

00 后毕业即失业，焦虑与抑郁蔓延？
AI Agent 即将替代 80% 的岗位，人类价值被反复质疑？
流量、标题党、游戏、短视频，构成一场温柔却持久的精神麻醉？
我们被困在「奶头乐」里，逐渐失去意义感，滑向虚无主义？
——
可我们凭什么要为这些中心化的精神鸦片买单？
 凭什么要为这些他人制造的地狱剧本买单？
 凭什么被一双无形的大手推着前进，
 被迫接受「不如去死」「一了百了」的结局设定？
——
你问我：「死了么？」
 我人间哪吒，天生傲骨 —— 我就不。
于是有了 HOPE（小希）：
 一款陪你穿越人生至暗时刻的 AI Agent，
 一款真正感知人类情绪、不是劝你振作、
 而是陪你一点点「活回来」「重建人生节奏」的系统。

HOPE 基于 Spoon OS —— 为感知经济打造的 Agentic Framework 构建，
 它不是心灵鸡汤，也不是陪聊工具，
 而是一套可执行的 人生重启协议：
 当意志失效时，让更稳定的系统接管；
 当你撑不住时，让更懂你的 Agent 陪你。
---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Next.js 14、React、TypeScript、wagmi/viem、TailwindCSS、ECharts |
| 后端 | FastAPI、SQLModel、SpoonOS Graph Agent（spoon-ai-sdk）、DeepSeek LLM |
| 合约 | Solidity、Foundry（可选部署） |
| 数据库 | SQLite（默认） |

---

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
├── contracts/        # Foundry 合约（可选）
├── docs/             # 启动与测试文档
├── 项目文档.md       # 产品与规则详细说明
└── README.md        # 本文件
```

---

## 快速启动

### 1. 后端

```bash
# 建议使用项目根目录的 .venv
cd backend
pip install -r requirements.txt
# 复制 backend/.env.example 为 backend/.env，填写 DEEPSEEK_API_KEY 等
uvicorn app.main:app --reload
```

健康检查：`GET http://127.0.0.1:8000/health`  
返回示例：`{"status":"ok","version":"mvp-1.0.0","demo_mode":false}`

### 2. 前端

```bash
cd frontend
npm install
# 复制 frontend/.env.example 为 frontend/.env 或 .env.local
# 至少设置 NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
npm run dev
```

访问：`http://localhost:3000`

---

## 环境变量

**后端（`backend/.env`）**

| 变量 | 说明 | 默认 |
|------|------|------|
| DATABASE_URL | 数据库连接 | sqlite:///./alive.db |
| DEFAULT_TIMEZONE | 默认时区 | Asia/Shanghai |
| DEEPSEEK_API_KEY | DeepSeek API Key | 必填 |
| DEEPSEEK_BASE_URL | DeepSeek 接口地址 | https://api.deepseek.com/v1 |
| DEMO_MODE | 演示模式（压缩天数、里程碑可仅记录不上链） | false |
| DEMO_START_DATE_KEY | 演示模式起始日期 | 可选 |

**前端（`frontend/.env` 或 `.env.local`）**

| 变量 | 说明 | 默认 |
|------|------|------|
| NEXT_PUBLIC_API_BASE | 后端 API 地址 | http://127.0.0.1:8000 |
| NEXT_PUBLIC_CHAIN_ID | 链 ID（上链时） | 11155111 |
| NEXT_PUBLIC_PROOF_REGISTRY | ProofRegistry 合约地址 | 0x... |
| NEXT_PUBLIC_MILESTONE_NFT | 里程碑 NFT 合约地址 | 0x... |

前端通过 `GET /health` 的 `demo_mode` 与后端同步：DEMO 模式下里程碑页「记录里程碑」仅走后端记录；非 DEMO 模式下连接钱包需上链铸造。

---

## 主要功能

- **首页**：欢迎页、当前 Day 按钮、查看进度/周报入口。
- **每日打卡（`/daily/[dayIndex]`）**：当日任务、输入感受、生成反馈（Reflection）、保存记录、完成今日（铸造 Day SBT，需合约）。
- **进度（`/progress`）**：连续天数、已完成天数、可铸造日、里程碑资格。
- **周报 / 结营报告（`/report`）**：周报（range=week）、结营报告（range=final），含图表。
- **里程碑（`/milestone/1|2|final`）**：第 7 / 14 / 28 天里程碑，展示对应 NFT 图片（`public/nft/week1.svg` 等），记录或铸造里程碑（是否上链由后端 `demo_mode` 决定）。

身份：支持钱包连接（wagmi）或手动输入地址；断开钱包后清空本地身份并跳回首页。

---

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

---

## 交付说明

- **产品名称**：HOPE小希（28天心灵成长之旅）
- **SpoonOS**：后端使用 SpoonOS Graph Agent，承担 DailyPrompt、Reflection、报告等核心流程。
- **DEMO 模式**：后端 `DEMO_MODE=true` 时，前端从 `/health` 读取 `demo_mode`，里程碑仅记录不上链；生产环境关闭 DEMO_MODE，连接钱包时需上链铸造。
- **里程碑 NFT 图片**：使用 `frontend/public/nft/` 下 `week1.svg`、`week2.svg`、`final.svg`，无需合约即可在里程碑页展示。
- 更细的产品规则、名词表、Graph 节点定义、合约规范见 **项目文档.md**；本地启动与上链步骤见 **docs/startup.md**。

---

## 上链步骤（生产 / 测试网）

### 1. 部署合约（Foundry）

```bash
cd contracts
# 安装依赖（若未安装）
forge install OpenZeppelin/openzeppelin-contracts
# 复制 .env.example 为 .env，填写 PRIVATE_KEY、RPC_URL（如 Sepolia）
cp .env.example .env
# 可选：SBT_BASE_URI 用于 RestartBadgeSBT 的 tokenURI 前缀
forge script script/Deploy.s.sol --rpc-url $env:RPC_URL --private-key $env:PRIVATE_KEY --broadcast
```

部署后会输出三个地址：**ProofRegistry**、**RestartBadgeSBT**、**MilestoneNFT**。

### 2. 配置前端与后端

**前端 `frontend/.env` 或 `.env.local`：**

```
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
NEXT_PUBLIC_CHAIN_ID=11155111
NEXT_PUBLIC_PROOF_REGISTRY=<ProofRegistry 地址>
NEXT_PUBLIC_BADGE_SBT=<RestartBadgeSBT 地址>
NEXT_PUBLIC_MILESTONE_NFT=<MilestoneNFT 地址>
```

**后端**：关闭 DEMO 模式时设 `DEMO_MODE=false`，前端从 `/health` 读取 `demo_mode` 后，里程碑页会要求上链铸造。

### 3. 数据库（若已有旧库）

后端新增字段 `DailyLog.day_sbt_tx_hash`。若使用已有 `alive.db`，需**删除 `backend/alive.db` 后重启后端**让其重建表，或自行执行 SQL 添加列：`ALTER TABLE dailylog ADD COLUMN day_sbt_tx_hash VARCHAR(66);`。

### 4. 上链流程（用户侧）

1. **每日打卡**：输入感受 → 点击「生成反馈」→ 点击「保存记录」→ 连接钱包后点击「上链提交」→ 前端调用 `ProofRegistry.submitProof(dayIndex, proofHash)` → 成功后 POST `/tx/confirm`。
2. **完成今日**：在当日已提交 Proof 的前提下，点击「完成今日」→ 前端调用 `RestartBadgeSBT.mintDay(dayIndex)` → 成功后 POST `/sbt/confirm`（type=DAY, dayIndex）。
3. **结营**：当 28 天 Day SBT 均已铸造后，进度页可触发「结营」→ 前端调用 `RestartBadgeSBT.composeFinal()` → 成功后 POST `/sbt/confirm`（type=FINAL）。
4. **里程碑 NFT**：达到 7/14/28 天后进入里程碑页，连接钱包点击「铸造里程碑 NFT」→ 前端调用 `MilestoneNFT.mint(to, tokenId, tokenURI)` → 成功后 POST `/milestone/mint` 记录 txHash。
