import requests
import json

BASE = 'http://127.0.0.1:8000/api'

# 1. 建立測試客戶
print("=== 建立測試客戶 ===")
client_resp = requests.post(f'{BASE}/clients/', json={'name': '測試客戶', 'tax_id': '12345678', 'billing_cycle': 15})
print(f'客戶: {client_resp.status_code} - {client_resp.json()}')
client_id = client_resp.json()['id']

# 2. 建立含 client_order_no 的工單
print("\n=== 建立含 client_order_no 的工單 ===")
wo_data = {
    'date': '2026-08-24',
    'client_id': client_id,
    'item_name': '海報印刷',
    'quantity': 100,
    'client_order_no': 'PO-2026-0842',  # 新欄位
    'paper_weight': '250g',
    'paper_type': '道林紙',
    'cut_type': '菊全開',
    'front_side': 4,
    'back_side': 0,
    'operator': 2,
    'notes': '測試客戶單號',
    'paper_fee': 800,
    'plate_fee': 1500,
    'wage': 2500
}
wo_resp = requests.post(f'{BASE}/work-orders/', json=wo_data)
print(f'工單: {wo_resp.status_code}')
print(json.dumps(wo_resp.json(), ensure_ascii=False, indent=2))

# 3. 建立一張不含 client_order_no 的工單 (測試舊資料相容)
print("\n=== 建立不含 client_order_no 的工單 (舊欄位相容測試) ===")
wo2_data = {
    'date': '2026-08-24',
    'client_id': client_id,
    'item_name': '名片印刷',
    'quantity': 500,
    'paper_fee': 300,
    'plate_fee': 600,
    'wage': 1000
}
wo2_resp = requests.post(f'{BASE}/work-orders/', json=wo2_data)
print(f'工單: {wo2_resp.status_code}')
print(json.dumps(wo2_resp.json(), ensure_ascii=False, indent=2))

# 4. 查詢列表確認回傳含 client_order_no
print("\n=== 工單列表回傳檢查 ===")
list_resp = requests.get(f'{BASE}/work-orders/')
print(f'列表: {list_resp.status_code}')
for wo in list_resp.json():
    print(f'  id={wo["id"]} item={wo["item_name"]} client_order_no={wo.get("client_order_no")!r}')

print("\n✅ 驗證完成")