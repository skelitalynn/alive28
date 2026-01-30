# MVP 本地测试步骤（不上链）

> 目标：跑通“打卡 → 生成 proofHash → 进度/报告”全流程，不触发链上交易。

## 0. 前置检查
- 当前目录应为项目根目录：`C:\Users\86183\Desktop\web3实习计划\project`
- 后端使用根目录 `.venv`（如未创建请先执行 `python -m venv .venv`）

## 1. 启动后端
```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

确认后端健康：
```text
http://127.0.0.1:8000/health
```
应返回：
```json
{"status":"ok","version":"mvp-1.0.0"}
```

## 2. 启动前端
```powershell
cd ..\frontend
npm install
npm run dev
```

确认前端可访问：
```text
http://localhost:3000
```

## 3. 基础接口测试（可选）
### 3.0 使用 Postman（可选）
可以。你可以用 Postman 直接请求接口并查看返回 JSON。

**Postman 设置（通用）**
- Method: `GET` 或 `POST`
- URL: `http://127.0.0.1:8000/...`
- Headers: `Content-Type: application/json`

**示例：POST /checkin**
- Method: `POST`
- URL: `http://127.0.0.1:8000/checkin`
- Headers: `Content-Type: application/json`
- Body → raw → JSON：
```json
{
  "address": "0x1111111111111111111111111111111111111111",
  "timezone": "Asia/Shanghai",
  "text": "今天完成了第一天打卡",
  "imageUrl": null
}
```
响应会返回 JSON（含 `logId` / `proofHash` / `reflection` / `streak`）。

### 3.1 获取 Day 1 任务卡
浏览器打开：
```text
http://127.0.0.1:8000/dailyPrompt?dayIndex=1
```

### 3.2 打卡（POST /checkin）
PowerShell：
```powershell
$body = @{ 
  address = "0x1111111111111111111111111111111111111111";
  timezone = "Asia/Shanghai";
  text = "今天完成了第一天打卡";
  imageUrl = $null
} | ConvertTo-Json

Invoke-RestMethod -Uri http://127.0.0.1:8000/checkin -Method Post -ContentType "application/json" -Body $body
```
预期返回字段包含：`logId`、`proofHash`、`reflection`、`streak`。

### 3.3 进度查询（GET /progress）
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/progress?address=0x1111111111111111111111111111111111111111"
```

### 3.4 报告（GET /report）
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/report?address=0x1111111111111111111111111111111111111111&range=week"
```

## 4. 前端交互测试（不触发上链）
1. 打开 `http://localhost:3000/enter`，连接钱包（可选）
2. 进入 `http://localhost:3000/daily/1`
3. 输入一句话，点击“打卡并生成 proofHash”
4. 不要点击“上链提交”（避免链上 RPC 报错）
5. 打开 `http://localhost:3000/progress` 查看 streak
6. 打开 `http://localhost:3000/report` 查看报告

## 5. 常见问题
- **Failed to fetch**：后端未运行或前端未重启
- **/dailyPrompt 500**：tasks.json BOM（已处理），重启后端
- **/checkin 500**：GraphAgent 报错时查看后端终端日志

---

如需上链测试，请再单独部署合约并配置 `NEXT_PUBLIC_RPC_URL`、`NEXT_PUBLIC_PROOF_REGISTRY`。
