# Alive28 项目问题清单（交付前扫描）

更新时间：2026-02-03

本清单基于当前仓库文件扫描与运行现状整理，按影响程度排序。  
目标：交付前明确需要修复 / 核对的点，避免 Demo/评审时踩坑。

## 高优先级（会导致功能报错或流程中断）

1) 里程碑 NFT 铸造弹窗报错（未配置合约地址）
   - 现象：页面提示 “NFT 合约地址未配置，请设置 NEXT_PUBLIC_MILESTONE_NFT”
   - 位置：`frontend/src/lib/nft/mintMilestone.ts`
   - 原因：连接钱包时会走真实链上 mint，未配置合约地址直接报错
   - 影响：里程碑页点击铸造必失败
   - 建议：  
     - 短期 Demo：允许 “未配置合约地址时只显示图片 + 仅走 /milestone/mint 记录”
     - 正式：配置 `NEXT_PUBLIC_MILESTONE_NFT`

2) 里程碑页面/元数据出现乱码（文件编码损坏）
   - 位置：
     - `frontend/src/app/milestone/[id]/page.tsx`
     - `frontend/src/lib/nft/milestoneNFT.ts`
   - 现象：中文显示为乱码（非 UTF-8）
   - 影响：UI 文案异常，且容易引发构建问题
   - 建议：统一以 UTF-8 重新保存这两个文件

3) 里程碑图片路径不一致（UI 与实际 public 文件不匹配）
   - 现状：  
     - 你已添加图片在：`frontend/public/nft/week1.svg|week2.svg|final.svg`
     - 代码中仍引用：`/nft-assets/milestone-*.png`
   - 位置：`frontend/src/lib/nft/milestoneNFT.ts`
   - 影响：NFT 图片显示为空或 404
   - 建议：将图片路径改为 `/nft/week1.svg` 等，与 public 文件一致

4) 前端 API 接口定义仍包含已移除的 NFT 逻辑
   - 位置：`frontend/src/lib/api/client.ts`
   - 现状：仍包含 `mintDay/composeFinal`、`dayMintCount/finalMinted` 等字段
   - 影响：与最新文档（已移除 NFT）不一致，容易导致对接误解/调用错误
   - 建议：清理 API 类型与方法，或明确标注“已废弃”

## 中优先级（会造成混淆或重复实现）

5) 存在旧版 API 实现文件，可能误用
   - 位置：`frontend/lib/api.ts`（非 `frontend/src`）
   - 现状：仍包含 `/nft/confirm` 等旧接口
   - 影响：重复维护，团队协作时容易误用
   - 建议：删除或迁移到 `frontend/src/lib/api/` 并标记废弃

6) 文档中的里程碑图片 URL 与实际托管方式不一致
   - 文档：`https://YOUR_DOMAIN/static/week1.png`
   - 实际：`/nft/week1.svg`（前端 public）
   - 影响：交付文档与实际运行不一致
   - 建议：文档更新为当前路径或后端静态托管地址

## 低优先级（不影响主流程，但建议处理）

7) OCR 未实现的 TODO
   - 位置：`backend/app/graph/nodes.py:77`
   - 说明：`image OCR not implemented`
   - 影响：轻微，不影响当前文本打卡主流程

8) 环境文件 / 数据库需确保不入库
   - 位置：`.env`, `frontend/.env.local`, `contracts/.env`, `alive.db`
   - 说明：目前 `.gitignore` 已覆盖，仍需确认未被追踪

---

## 建议的最小修复优先顺序
1. 修正 `milestoneNFT.ts` 图片路径 + 乱码问题  
2. Milestone 页面允许在未配置合约时“只显示图片 + 仅记录后端”  
3. 清理 `frontend/src/lib/api/client.ts` 的 NFT 字段/方法  
4. 清理 `frontend/lib/api.ts` 旧文件或标记废弃  
5. 更新《项目文档.md》的图片与 API 说明

