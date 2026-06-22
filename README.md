# HOPE 小希 / Alive28

Alive28 是一个 28 天自我关怀与行动记录应用。用户每天完成一个轻量任务，记录感受，获得 AI 反思反馈，并查看进度、周报和结营报告；链上 Proof 与 NFT 是可选能力。

> 本项目提供自我反思和行动提示，不提供医疗诊断、心理治疗、危机干预或用药建议。

## 当前技术栈

- 前端：Next.js 14、React、TypeScript、wagmi、viem、ECharts
- 后端：FastAPI、SQLModel、SpoonOS Graph、DeepSeek
- 数据：SQLite
- 合约：Solidity、Foundry

## 文档入口

项目架构、开发环境、测试、进度、决策和 Agent Harness 的唯一入口：

- [项目文档索引](docs/README.md)
- [产品背景与范围](docs/PRODUCT.md)
- [本地开发](docs/DEVELOPMENT.md)
- [测试与完成定义](docs/testing.md)

## 最短启动路径

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
Set-Location backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

另开终端：

```powershell
Copy-Item frontend\.env.example frontend\.env.local
npm --prefix frontend ci
npm --prefix frontend run dev
```

访问 `http://localhost:3000`。完整环境变量、合约和故障排查见
[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)。
