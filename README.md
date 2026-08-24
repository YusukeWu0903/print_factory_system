# 🏭 印刷廠工單與對帳系統

> 專為傳統代工印刷廠設計的輕量化工單管理與自動對帳系統

## ✨ 功能特色

### 📋 工單管理
- **工單列表**：卡片式顯示，支援狀態篩選（全部/印製中/待請款/已請款）
- **新增工單**：支援印刷規格完整輸入
  - 紙張規格：紙磅、紙別、裁別（菊全開/四開/八開...）
  - 印刷色數：正面/反面色數（數字輸入）
  - 人員管理：作業人員編號
  - 費用明細：紙錢、版費、印工（自動試算總金額）
- **狀態流轉**：印製中 → 已完成待請款 → 已請款（防呆機制，不可跳級）

### 👥 客戶管理
- 客戶新增/編輯/刪除
- 統一編號驗證（8碼）
- 結帳日設定（1-31號）

### 📊 月底對帳系統 (Phase 4)
- **月份/客戶雙重篩選**：快速查詢特定月份特定客戶的待請款工單
- **明細表格**：日期、品名、數量、規格（裁別/色數/人員）、金額
- **彙總資訊**：工單筆數、總金額即時顯示
- **批次結帳**：全選/單選工單 → 一鍵確認結帳（待請款 → 已請款）
- **可用月份自動載入**：依客戶自動顯示有待請款工單的月份

### 📱 行動裝置優先
- Mobile-First 設計，單手操作友善
- 大觸控區域（最小 48px）
- 底部導航列切換頁面
- 浮動動作按鈕 (FAB) 快速新增

### 🔧 技術架構
| 層級 | 技術棧 |
|------|--------|
| **後端** | FastAPI + SQLAlchemy 2.0 + SQLite |
| **前端** | Vue 3 + Tailwind CSS + Vite |
| **部署** | Ngrok Tunnel 內網穿透 + Vite Proxy |
| **資料庫** | SQLite (可遷移至 PostgreSQL) |

---

## 🚀 快速開始

### 環境需求
- Python 3.10+
- Node.js 18+
- Git

### 後端啟動
```bash
cd backend

# 建立虛擬環境 (建議)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安裝依賴
pip install -r requirements.txt

# 設定環境變數 (複製 .env.example 並修改)
# cp .env.example .env

# 啟動後端 (Port 8000)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端啟動
```bash
cd frontend

# 安裝依賴
npm install

# 啟動開發伺服器 (Port 5173)
npm run dev

# 建置生產版本
npm run build
```

### 內網穿透 (手機測試)
```bash
# 安裝 ngrok (需註冊帳號並設定 authtoken)
# ngrok config add-authtoken YOUR_TOKEN

# 啟動雙 Tunnel
# 終端機 1: 前端
ngrok http 5173 --host-header=rewrite

# 終端機 2: 後端 API
ngrok http 8000 --host-header=rewrite

# 或使用自動化腳本
python start_tunnel.py
```

---

## 📁 專案結構
```
print_factory_system/
├── backend/
│   ├── app/
│   │   ├── api/           # API 路由
│   │   │   ├── clients.py         # 客戶 CRUD
│   │   │   ├── work_orders.py     # 工單 CRUD + 狀態流轉
│   │   │   └── reconciliation.py  # 對帳查詢/結帳
│   │   ├── core/          # 核心設定
│   │   ├── models/        # SQLAlchemy Models
│   │   ├── schemas/       # Pydantic Schemas
│   │   └── main.py        # FastAPI 入口
│   ├── requirements.txt
│   └── .env               # 環境變數
│
├── frontend/
│   ├── src/
│   │   ├── components/    # 共用元件
│   │   │   ├── AppLayout.vue      # 應用佈局 + 底部導航
│   │   │   └── StatusBadge.vue    # 狀態標籤
│   │   ├── composables/   # 組合式函式
│   │   ├── views/         # 頁面元件
│   │   │   ├── WorkOrderList.vue  # 工單列表
│   │   │   ├── CreateWorkOrder.vue # 新增工單
│   │   │   └── Reconciliation.vue # 月底對帳
│   │   ├── router/        # Vue Router
│   │   ├── services/      # API 服務
│   │   └── composables/   # Composables
│   ├── vite.config.js     # Vite + Proxy 設定
│   └── tailwind.config.js # Tailwind 主題色
│
├── start_tunnel.py        # Ngrok 自動化腳本
└── README.md
```

---

## 🔑 環境變數說明

### Backend (.env)
```env
DATABASE_URL=sqlite:///./print_factory.db
DEBUG=True
```

---

## 📡 API 文檔
啟動後端後訪問：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要端點
| 方法 | 路徑 | 說明 |
|------|------|------|
| GET/POST | /api/clients/ | 客戶列表/新增 |
| PATCH/DELETE | /api/clients/{id} | 更新/刪除客戶 |
| GET/POST | /api/work-orders/ | 工單列表/新增 |
| PATCH | /api/work-orders/{id}/status | 狀態更新 (防呆) |
| GET | /api/reconciliation/months | 可對帳月份 |
| GET | /api/reconciliation/summary | 對帳彙總明細 |
| POST | /api/reconciliation/confirm | 批次確認結帳 |

---

## 🎨 介面截圖

### 工單列表
- 狀態篩選 Tab (全部/印製中/待請款/已請款)
- 卡片式顯示：品名、客戶、日期、金額、狀態標籤
- 底部狀態更新按鈕

### 新增工單
- 日期選擇器
- 客戶下拉選單 (+ 新增客戶按鈕)
- 印刷規格區塊 (裁別/色數/人員)
- 費用明細即時試算總金額

### 月底對帳
- 客戶 + 月份雙重篩選
- 工單明細表格 (規格標籤顯示)
- 全選/單選 + 底部總計 + 確認結帳按鈕

---

## 📱 手機測試流程

1. 電腦啟動前後端 + ngrok
2. 手機掃描 QR Code (終端機顯示 ASCII QR Code)
3. 瀏覽器開啟 ngrok 網址
4. 若出現 ngrok 警告頁 → 點擊「Visit Site」
4. 開始測試：新增工單 → 狀態流轉 → 月底對帳

---

## 🛠️ 開發指令速查

```bash
# 後端
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端
cd frontend
npm install
npm run dev          # 開發模式
npm run build        # 生產建置
npm run preview      # 預覽生產建置

# Ngrok 自動化
python start_tunnel.py
```

---

## 🤝 貢獻指南

1. Fork 專案
2. 建立功能分支 (`git checkout -b feature/xxx`)
3. Commit 變更 (`git commit -m 'feat: xxx'`)
4. Push 分支 (`git push origin feature/xxx`)
5. 發起 Pull Request

---

## 📄 授權

MIT License - 詳見 [LICENSE](LICENSE)

---

## 👨‍💻 作者

**Yusuke Wu** - [GitHub](https://github.com/YusukeWu0903)

---

> 💡 **提示**：此專案專為傳統印刷廠設計，著重於「現場好用、手機好用、對帳快」。歡迎提出 Issue 或 PR 共同改善！