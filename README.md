# HOPE小希 · 28天心灵成长之旅

基于 SpoonOS Graph Agent 的 28 天打卡与里程碑 NFT 应用：每日任务 → 用户输入 → LLM 反馈 → 隐私承诺上链（仅 proofHash）→ 里程碑 NFT。

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
| POST | /tx/confirm | 上链交易确认 |
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
