# 测试与完成定义

## 验证层级

| 范围 | 命令 | 当前覆盖 |
|---|---|---|
| Harness 和文档 | `python scripts/harness/check_docs.py` | 文档路由、配置和本地链接 |
| 后端 | `python -m pytest backend/app/tests -q` | 钱包认证、receipt/event、Reflection Safety、Checkpoint、事务与幂等 |
| 前端 | `npm --prefix frontend run build` | Next.js 构建和 TypeScript 检查 |
| 合约 | `forge test --root contracts` | ProofRegistry 与 RestartBadgeNFT |

完整验证：

```powershell
python scripts/harness/doctor.py --run
```

Harness 会顺序执行 `.harness/config.json` 中的 `commands.check`，并在任务验证时把输出写入 `.harness/evidence/`。

## 首次验证前

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
npm --prefix frontend ci
git submodule update --init --recursive
```

如果当前终端没有激活 `.venv`，后端测试应使用：

```powershell
.\.venv\Scripts\python.exe -m pytest backend/app/tests -q
```

`.harness/config.json` 使用通用的 `python` 命令，CI 或本地执行者必须确保它指向已安装依赖的环境。

## 接口冒烟测试

后端启动后：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod "http://127.0.0.1:8000/dailyPrompt?dayIndex=1"
```

Demo 模式可直接打卡：

```powershell
$body = @{
  address = "0x1111111111111111111111111111111111111111"
  dayIndex = 1
  timezone = "Asia/Shanghai"
  text = "今天完成了第一天记录"
  imageUrl = $null
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri http://127.0.0.1:8000/checkin `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

非 Demo 模式必须先通过前端钱包签署 `/auth/nonce` 返回的 message，并把
`/auth/verify` 返回的 token 作为 `Authorization: Bearer <token>` 发送。

随后检查：

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/progress?address=0x1111111111111111111111111111111111111111"
Invoke-RestMethod "http://127.0.0.1:8000/report?address=0x1111111111111111111111111111111111111111&range=week"
```

## 当前 LLM 与恢复覆盖

当前自动化已覆盖：

- 严格 Reflection Schema 与语义禁区。
- Prompt 注入、短有效输入和危机分流。
- 临时超时重试、错误输出修复与安全 fallback。
- 数据库事务失败不留下孤立进度。
- 相同 `checkinId` 从持久化 SpoonOS 快照恢复。
- 恢复不重复调用 Reflection、不重复日志和 streak。
- 同 ID 不同输入返回冲突。
- 模型次数、节点耗时、节点尝试次数和错误摘要。
- nonce 单次消费、session 地址绑定和未认证拒绝。
- Proof receipt 的 chain、status、sender、contract 和事件匹配。
- 伪造 Day NFT 与 Milestone 事件不会改变本地状态。

仍缺少大规模离线安全评测、真实供应商故障测试、并发恢复竞争和 Checkpoint 生命周期测试。

## Reflection Safety 计划验收

下一阶段自动测试至少覆盖：

- 有效输入进入普通生成并保存一次。
- 短但真实的输入不会仅因字数被拒绝。
- 随机字符、广告和 Prompt 注入返回 `clarify` 或 `reject`。
- `clarify`、`reject` 不创建日志、不更新 streak、不生成 Proof。
- 危机输入优先于质量判断进入危机路径。
- 危机路径不创建 Proof、不更新 streak、不触发 NFT。
- 模型多字段、缺字段、错误类型和超长输出被拒绝。
- 诊断、用药、保证性承诺和危险动作被语义校验拒绝。
- Repair 最多执行一次。
- Repair 仍失败时进入与失败类型匹配的 fallback。
- 临时网络错误按策略重试，内容错误不作为网络重试。
- Checkpoint 恢复不会重复创建日志或增加 streak。
- 数据库任一写入失败时整个打卡事务回滚。

链上阶段测试至少覆盖：

- 任意地址不能通过伪造请求修改其他用户状态。
- 任意 `txHash` 不能在没有合法 receipt 和 event 时确认成功。
- 未批准的 Proof 不能获得正式里程碑资格。
- revoked Proof 不参与后续里程碑计算。
- 链后补偿保留原交易历史。

详细测试数据分类和分阶段完成标准见 `IMPLEMENTATION_PLAN.md`。

## 手工端到端检查

1. 首页可以建立 Demo 身份或连接钱包。
2. `/daily/1` 可以读取任务、提交文字并显示反馈。
3. 重复提交同一日期不会创建第二条日志。
4. `/progress` 显示完成天数。
5. `/report` 可生成周报或使用 fallback。
6. 未配置合约时不执行真实交易。

## 完成定义

功能项只有在以下条件全部满足时才能进入 `passing`：

- `docs/FEATURES.json` 中有可观察行为和独立验证命令。
- `python scripts/harness/task.py verify <ID>` 返回成功。
- `.harness/evidence/<ID>/.../result.json` 已生成。
- 相关文档与 `.env.example` 已同步。
- 没有通过吞掉异常、跳过检查或伪造链上确认来获得绿灯。

当前仓库没有 CI。Harness 本地验证不能替代未来的持续集成。
