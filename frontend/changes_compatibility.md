# 前端修复与后端接口补齐说明

本文档合并了前端修复记录 + 后端缺失接口清单，供联调与补齐使用。

---

## 1. 前端修复内容汇总

我们主要修复了以下三类问题，以确保前端项目的逻辑正确性和构建稳定性：

### A. 逻辑修复 (Logic Fixes)
- **夏令时日期计算修正** (`src/lib/store/localStore.ts`):
  - **问题**: 天数索引计算公式 (`Math.floor((t - s) / 24h)`) 在夏令时切换期间容易出错。例如，当一天只有 23 小时的时候，`Math.floor` 会导致计算结果少一天（off-by-one error）。
  - **修改**: 改用 `Math.round` 并优化了 `updateStreak` 的日期递增逻辑 (`setDate + 1`)。
  - **作用域**: 仅影响纯前端模拟模式 (`mockClient`) 下的本地数据计算。

### B. 类型与代码规范修复 (Type & Lint Fixes)
- **非空断言添加** (`src/app/daily/[dayIndex]/page.tsx`):
  - **修改**: 为明确存在的对象添加 `!` 断言，解决 TypeScript 编译报错。
- **变量覆盖警告** (`src/lib/api/mockClient.ts`):
  - **修改**: 调整了对象属性展开顺序，消除了潜在的逻辑覆盖风险。

### C. 构建配置修复 (Build Fixes)
- **Suspense 边界添加** (`src/app/report/page.tsx`):
  - **修改**: 将使用 `useSearchParams` 的组件包裹在 `<Suspense>` 中。
  - **必要性**: 这是 Next.js 静态构建的强制要求，不修复会导致项目无法打包上线。

---

## 2. 后端对接兼容性分析

**结论：目前的修改完全不会影响与原来的后端对接，且为对接打下了更好的基础。**

具体理由如下：

### 1) 逻辑隔离 (Mock Isolation)
- **现状**: 本次修改的核心逻辑（日期计算、本地存储）均封装在 `localStore.ts` 和 `mockClient.ts` 中。
- **对接时**: 当您准备对接真实后端时，只需在 `src/lib/api/index.ts` 中将模式切换为 HTTP 模式。届时，数据流将走 `httpClient.ts`，直接调用后端接口。
- **互不干扰**: 后端通常会有自己独立的日期处理逻辑。前端现在的模拟逻辑（mock logic）届时会被旁路或弃用，不会对后端数据产生“污染”。

### 2) 接口契约保持 (Interface Consistency)
- **未修改**: 严格遵守 `src/lib/api/client.ts` 中定义的 `ApiClient` 接口规范。
- **无缝切换**: 只要后端 API 实现符合 TypeScript 接口定义，前端组件无需感知底层是 `mockClient` 还是 `httpClient`。

### 3) 工程稳定性 (Engineering Stability)
- **构建保障**: 修复的 Build 错误（如 Suspense）是前端工程层面的通用修复。
- **必要性**: 前端必须先能编译通过，才能联调上线。

---

## 3. 缺失接口清单（需后端补齐）

> 目标：让 `frontend` 在 HTTP 模式可无缝替代 mock，并支持里程碑 NFT（Week1/Week2/Final）。
> 说明：当前后端已有 `/checkin`、`/progress`、`/report`、`/tx/confirm`、`/sbt/confirm` 等，但缺少里程碑相关接口，且部分响应字段不足。

### 3.1 里程碑 NFT 铸造接口（必须新增）
**Endpoint**: `POST /milestone/mint`

**用途**: Week1/Week2 里程碑 NFT 铸造确认（Final 可单独使用 `/sbt/confirm` FINAL，或也可走此接口）。

**Request**
```json
{
  "address": "0x...",
  "milestoneId": 1,
  "txHash": "0x...",
  "chainId": 11155111,
  "contractAddress": "0x..."
}
```

**Response**
```json
{
  "ok": true,
  "milestones": {
    "1": "0x...",
    "2": "0x..."
  }
}
```

**校验规则（建议）**
- `milestoneId` 必须是 1/2/3。
- 里程碑已铸造则幂等返回。
- 打卡天数不足：返回 400，错误说明 `need 7/14/28`。

---

### 3.2 Daily 页面聚合数据接口（新增）
**Endpoint**: `GET /dailySnapshot?address=0x...&dayIndex=7`

**Response**
```json
{
  "dateKey": "2026-01-31",
  "task": {
    "dayIndex": 7,
    "title": "...",
    "instruction": "...",
    "hint": "..."
  },
  "log": {
    "id": "uuid",
    "address": "0x...",
    "challengeId": 1,
    "dayIndex": 7,
    "dateKey": "2026-01-31",
    "normalizedText": "...",
    "reflection": {"note":"...","next":"..."},
    "saltHex": "0x...",
    "proofHash": "0x...",
    "status": "CREATED",
    "txHash": null,
    "daySbtTxHash": null,
    "createdAt": "2026-01-31T12:00:00Z"
  },
  "alreadyCheckedIn": true
}
```

---

### 3.3 首页 DayN 快照接口（新增）
**Endpoint**: `GET /homeSnapshot?address=0x...`

**Response**
```json
{
  "dayBtnLabel": "Day 7",
  "dayBtnTarget": 7,
  "startDateKey": "2026-01-25",
  "todayDateKey": "2026-01-31"
}
```

---

## 4. 现有接口需要补字段（强烈建议）

### 4.1 `GET /progress` 增补字段
```json
{
  "finalSbtTxHash": "0x...",
  "milestones": {
    "1": "0x...",
    "2": "0x..."
  },
  "startDateKey": "2026-01-25"
}
```

### 4.2 `POST /checkin` 增补字段（或返回完整 log）
```json
{
  "logId": "uuid",
  "dateKey": "2026-01-31",
  "dayIndex": 7,
  "reflection": {"note":"...","next":"..."},
  "proofHash": "0x...",
  "saltHex": "0x...",
  "normalizedText": "...",
  "status": "CREATED",
  "txHash": null,
  "daySbtTxHash": null,
  "createdAt": "2026-01-31T12:00:00Z",
  "alreadyCheckedIn": true
}
```

---

## 5. ApiClient 与接口映射建议

| ApiClient 方法 | 推荐后端接口 | 说明 |
|---|---|---|
| `getHomeSnapshot` | `GET /homeSnapshot` | 缺失（需新增） |
| `getDailySnapshot` | `GET /dailySnapshot` | 缺失（需新增） |
| `checkin` | `POST /checkin` | 需补字段 |
| `submitProof` | `POST /tx/confirm` + 再获取 log | 若愿意可新增 `POST /proof/submit` |
| `mintDay` | `POST /sbt/confirm` (type=DAY) + 再获取 log | 可沿用现有 |
| `composeFinal` | `POST /sbt/confirm` (type=FINAL) | 现有 |
| `mintMilestone` | `POST /milestone/mint` | 缺失（需新增） |
| `getProgress` | `GET /progress` | 需补字段 |
| `getReport` | `GET /report` | 现有 |

---

## 6. 里程碑 NFT 铸造规则（统一口径）
- Week1（milestoneId=1）：完成 **>=7 天打卡**
- Week2（milestoneId=2）：完成 **>=14 天打卡**
- Final（milestoneId=3）：完成 **>=28 天打卡**（或 DaySBT 全部铸造，可根据产品决策）

---

## 7. 下一步建议
- 现在的代码库处于 **可构建、无逻辑错误** 状态。
- 后端补齐接口后，将 `NEXT_PUBLIC_API_MODE` 切换为 `http` 即可联调。
