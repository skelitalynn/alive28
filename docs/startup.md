# 项目启动文档（给组员）

> 目标：快速跑通本地 MVP（不上链）。
> 如需上链流程，见本文末尾“上链可选步骤”。

## 目录结构
- `backend/` FastAPI + SQLModel + SpoonOS GraphAgent
- `frontend/` Next.js + wagmi/viem + Tailwind + ECharts
- `contracts/` Foundry 合约（上链可选）

---

## 1. 启动后端
> 后端使用 **项目根目录** 的 `.venv`

### 1.0 进入虚拟环境（可选但推荐）
```powershell
cd .
.\.venv\Scripts\Activate.ps1
```
如遇 PowerShell 执行策略限制，可用：
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

验证：
```
http://127.0.0.1:8000/health
```
预期返回：
```json
{"status":"ok","version":"mvp-1.0.0","demo_mode":false}
```
（前端从 `demo_mode` 与后端同步，用于里程碑页是否上链）

> 若未创建 `.venv`：
```powershell
cd .
python -m venv .venv
.\.venv\Scripts\pip.exe install -r backend\requirements.txt
```

> 后端环境变量：`backend/.env`
- 从 `backend/.env.example` 复制并填好 `DEEPSEEK_API_KEY`。

---

## 2. 启动前端
```powershell
cd frontend
npm install
npm run dev
```

打开：
```
http://localhost:3000
```

> 前端环境变量：`frontend/.env.local`
- 从 `frontend/.env.example` 复制
- 确认：
```
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
```
> **不要把 `.env` / `.env.local` 提交到仓库**（已在 `.gitignore` 屏蔽）。

---

## 3. 本地 MVP 流程（不上链）
1) 打开 `http://localhost:3000/enter`
2) 进入 `/daily/1`
3) 输入一句话 → 点击“打卡并生成 proofHash”
4) **不要点击“上链提交”**（上链是可选）
5) 打开 `/progress` 查看 streak
6) 打开 `/report` 查看报告

---

## 4. 常见问题排查
- **Failed to fetch**：后端没跑 / 前端没重启 / API 地址错误
- **/dailyPrompt 500**：多半是 tasks.json BOM 或后端未重启
- **/checkin 500**：看后端日志（GraphAgent/LLM 配置问题）

---

## 5. 上链可选步骤（需要 Foundry + RPC）
1) 安装 Foundry（Windows 需 `foundryup.exe`）
2) 在 `contracts/`：
```powershell
forge install OpenZeppelin/openzeppelin-contracts
copy .env.example .env
# 填 PRIVATE_KEY 和 RPC_URL（可选 NFT_BASE_URI）
forge script script/Deploy.s.sol --rpc-url $env:RPC_URL --private-key $env:PRIVATE_KEY --broadcast
```
部署后会输出三个地址：**ProofRegistry**、**RestartBadgeNFT**、**MilestoneNFT**。
3) 把合约地址写入前端 `.env.local`：
```
NEXT_PUBLIC_PROOF_REGISTRY=0x...
NEXT_PUBLIC_BADGE_NFT=0x...
NEXT_PUBLIC_MILESTONE_NFT=0x...
```
> 若此前已部署过 ProofRegistry + RestartBadgeNFT，可只部署 MilestoneNFT 并只填 `NEXT_PUBLIC_MILESTONE_NFT`；或重新跑 Deploy 得到三个新地址后全部覆盖。
4) 后端若已有 `alive.db`，上链需记录 Day NFT：建议删除 `backend/alive.db` 后重启后端以重建表（含 `day_nft_tx_hash`），或自行执行 `ALTER TABLE dailylog ADD COLUMN day_nft_tx_hash VARCHAR(66);`。
5) 重启前端，进入 `/daily/1` 后：打卡 →「保存记录」→「上链提交」→「完成今日」；进度页可查看 dayMintCount、mintableDayIndex；里程碑页可「铸造里程碑 NFT」。

---

如需接口测试，可参考 `docs/testing.md`（含 Postman 示例）。

数据库迁移方案（SQLite MVP）

简单方案（推荐）：删除本地数据库文件并重建表
停止后端
删除 alive.db
重新启动后端（会自动 create_all）
可选 Alembic（如果你后续要保留数据）：新增迁移脚本，增加/改名字段
UserProgress：新增 day_mint_count, final_minted, final_nft_tx_hash；删除 badges_minted
DailyLog：新增 salt_hex, day_nft_tx_hash；删除 salt
本地跑通步骤（含命令）

后端启动
根目录激活虚拟环境：Activate.ps1
安装依赖：requirements.txt
启动：python -m uvicorn backend.app.main:app --reload
合约部署（Foundry）
cd contracts
forge build
设置环境：$env:RPC_URL=...、$env:PRIVATE_KEY=...、$env:NFT_BASE_URI=...
部署：Deploy.s.sol --rpc-url $env:RPC_URL --private-key $env:PRIVATE_KEY --broadcast
前端启动
cd frontend
npm install
配置 .env.local：NEXT_PUBLIC_API_BASE、NEXT_PUBLIC_PROOF_REGISTRY、NEXT_PUBLIC_BADGE_NFT
npm run dev
端到端（一次完整链路）
Daily 页：POST /checkin（前端按钮）
调用合约 submitProof(dayIndex, proofHash)
POST /tx/confirm
调用合约 mintDay(dayIndex)
POST /nft/confirm (type=DAY)
GET /progress
当 shouldComposeFinal=true 时调用 composeFinal()
POST /nft/confirm (type=FINAL)
GET /report?range=final
