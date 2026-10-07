# 印刷廠工單與對帳系統

這是一套供單一管理員使用的印刷工單系統。前端使用 Vue 3、Vite 和 Tailwind CSS；後端使用 FastAPI、SQLAlchemy 和 SQLite。手機可透過 ngrok 開啟前端網址，所有資料 API 都需要先登入。

## 目前功能

- **工單**：新增、列表、狀態篩選與狀態更新。工單可記錄客戶單號、紙張、裁別、色數、人員、備註和費用。總金額為 `(紙錢 + 版費 + 印工) × 數量`。
- **客戶**：在「客戶管理」頁新增、編輯和刪除。已有工單的客戶不能刪除。統一編號可留空；填寫時須為 8 碼數字。
- **對帳**：按客戶的每月結帳日分期，列出待請款工單，選取後批次標記為已請款。例如結帳日為 15 號時，`2026-10` 涵蓋 `2026-09-16` 至 `2026-10-15`。若結帳日為 31 號而當月較短，截止日取該月最後一天。
- **登入**：單一管理員密碼。密碼只以 scrypt 雜湊存於本機 `.env`，登入會建立可登出的伺服器端工作階段。工作階段預設 12 小時到期；修改密碼並重新啟動後端後，舊工作階段失效。

## 啟動

需求：Python 3.10+、Node.js 20.19+ 或 22.12+。以下指令分別在兩個終端機執行。

### 後端

```powershell
cd backend
python -m pip install -r requirements.txt
Copy-Item .env.example .env  # 只有第一次需要；若 .env 已存在請保留
python -m app.core.set_admin_password
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

設定密碼時需輸入兩次，至少 12 字元。也可執行 `python -m app.core.set_admin_password --generate` 產生強密碼；指令只顯示明文一次，請妥善保存。`.env` 是本機設定，不應提交到 Git。更換密碼時再次執行同一指令，然後重新啟動後端。

### 前端

```powershell
cd frontend
npm ci
npm run dev
```

在電腦開啟 `http://localhost:5173`。Vite 會將 `/api` 轉送到本機的 8000 埠。後端僅綁定 `127.0.0.1`，請勿另外把後端 8000 埠建立公開 tunnel。若 8000 已被其他服務使用，可將後端改用 18000 埠，並在啟動前端的終端機先設定 `$env:API_PROXY_TARGET="http://127.0.0.1:18000"`。

### 手機測試

先啟動前後端，再於專案根目錄執行 `python start_tunnel.py`，或手動執行 `ngrok http 5173 --host-header=rewrite`。手機只需開啟**前端** tunnel 網址並登入。工作階段使用 `Secure`、`HttpOnly`、`SameSite=Strict` cookie；公開連線請使用 ngrok 提供的 HTTPS 網址。

## 資料庫與升級

預設資料庫固定在 `backend/print_factory.db`，不隨啟動指令所在目錄改變。`DATABASE_URL` 若使用相對 SQLite 路徑，也以 `backend` 為基準。專案最外層若有 `print_factory.db`，不會自動合併或覆蓋它。

啟動時會建立缺少的資料表。若舊資料庫缺少 `client_order_no` 欄位，系統會先在 `backend/backups/` 產生 SQLite 備份，再新增欄位；新增登入資料表前也會備份既有資料庫。備份和資料庫檔案均不提交到 Git。首次升級後請確認工單數量與內容正確，再繼續使用。

## 驗證

後端測試使用獨立的記憶體資料庫，不會改動現有工單：

```powershell
cd backend
python -m pytest tests -q
```

前端建置：

```powershell
cd frontend
npm run build
```

測試涵蓋登入與拒絕未授權請求、客戶資料驗證、工單列表規格欄位、對帳結帳日前後、短月與跨年、舊資料庫備份和升級。自動化測試通過仍需在實際手機畫面確認操作與版面。

## API

啟動後端後可在 `http://127.0.0.1:8000/docs` 查看 API 規格。主要路徑：

| 路徑 | 用途 |
| --- | --- |
| `POST /api/auth/login`、`GET /api/auth/me`、`POST /api/auth/logout` | 登入、檢查與登出 |
| `/api/clients/` | 客戶新增與列表；`/{id}` 支援讀取、更新、刪除 |
| `/api/work-orders/` | 工單新增與列表；`/{id}` 支援讀取、更新、刪除 |
| `PATCH /api/work-orders/{id}/status` | 工單狀態更新 |
| `GET /api/reconciliation/months` | 客戶可對帳月份（由新到舊） |
| `GET /api/reconciliation/summary` | 指定對帳期明細與起訖日期 |
| `POST /api/reconciliation/confirm` | 將選取的待請款工單標記已請款 |

工單狀態依序為「印製中 → 已完成待請款 → 已請款」。後端允許依序退回前一狀態以更正資料；目前畫面只提供向前更新。
