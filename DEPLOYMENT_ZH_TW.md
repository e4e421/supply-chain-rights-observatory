# 研究情報網站｜GitHub 設定與驗收指南（繁體中文）

專案：`e4e421/supply-chain-rights-observatory`

## 必須由擁有者手動完成的設定

### 1. 授權 GitHub App 存取新儲存庫（目前阻礙程式寫入）

- 開啟 [GitHub App 安裝設定](https://github.com/settings/installations/81637662)。
- 在 Repository access / 儲存庫存取權限下確認目前為 **Only select repositories**。
- 點選 Select repositories，新增 `e4e421/supply-chain-rights-observatory`，再儲存。
- 請勿提供帳號密碼、Personal Access Token 或 API 金鑰。
- 如果授權新增後仍無法寫入，檢查 GitHub App 的 Contents 寫入權限，必要時由 GitHub App 安裝頁面接受更新後的授權。

### 2. 選擇 GitHub Pages 發布方式

- 開啟 [Settings → Pages](https://github.com/e4e421/supply-chain-rights-observatory/settings/pages)。
- **Build and deployment → Source → GitHub Actions**。
- 不選擇 `Deploy from a branch`，因為 Actions 使用 `GITHUB_TOKEN` 提交資料，不會另行觸發分支 Pages 建置。

### 3. 啟用與手動測試自動更新

- 開啟 [Actions](https://github.com/e4e421/supply-chain-rights-observatory/actions)。
- 找到 **Refresh public intelligence and deploy** 工作流程。
- 選擇 **Run workflow → main → Run workflow**。
- 檢查 `collect` 與 `deploy` 兩個工作是否成功。
- 正常情況下網站的「最後成功擷取」與總筆數會更新。來源可能被限制而出現 `partial`，可在 Actions 檢視警告。

### 4. 檢視網站

- 預期網址：https://e4e421.github.io/supply-chain-rights-observatory/
- 或從 Settings → Pages 點選 Visit site。
- 初次發布有可能需要數分鐘；若尚未配置 Pages，預期網址不代表已上線。

## 建議但非必要的安全設定

- GitHub 帳號啟用 2FA/passkey，通知及個人電子郵件使用 GitHub 的隱私選項。
- 檢查 git commit author / 公開 GitHub Profile；**GitHub Pages 網域與公開 repo 本身會暴露帳號 handle**。若需將研究者身分與網站分開，應另建中立名稱的 GitHub 組織，並視情況使用自訂網域。
- 如未來增加需驗證的 API，僅儲存在 **Settings → Secrets and variables → Actions**，不要儲存在 `docs/`、Git 歷史或 `sources/`。
- 限制 `main` 分支強制推送與刪除；若啟用強制 PR 審核，需要另外允許具體的資料更新流程提交，否則 `collect` 可能無法更新 JSON。
- 不在前端加入研究夥伴帳號、聯絡方式、未公開訪談或企業保密資料。GitHub Pages 不提供真正的隱私存取控制。

## 驗收標準

- [ ] GitHub App 安裝名單包含指定 repo，讀寫 API 實際操作成功。
- [ ] repo 已包含 `docs/`、`scripts/`、`sources/`、`.github/workflows/` 等完整檔案。
- [ ] GitHub Pages Source 設為 GitHub Actions。
- [ ] Actions 產生第一次 `docs/data/latest.json` 更新紀錄。
- [ ] 網站在桌機／手機可閱讀、搜尋、篩選、匯出 CSV。
- [ ] 前台檔案沒有 API key 或研究成員個資；失效來源及更新狀態可見。
- [ ] 對外分享前核對來源、文章日期、法規版本與政策效力。

## 每日更新與研究方法提醒

- 排程預計臺北時間 06:23，GitHub Actions 可能延遲；實際時間以頁面和執行紀錄為準。
- 新聞聚合資料只是線索，不能當成人權違規的已確認統計；Crossref DOI 資料不能代替全文方法審查。
- 事件報導量、企業揭露與實際勞動結果須分別研究，避免將資料可見性偏差誤認為因果效果。
