import requests
import json

# 測試建立客戶
url = 'http://127.0.0.1:8000/api/clients/'

test_cases = [
    {'name': 'Test Client', 'tax_id': '11111111', 'billing_cycle': 15},
    {'name': '測試客戶', 'tax_id': '22222222', 'billing_cycle': 15},
    {'name': 'Test 中文', 'tax_id': '33333333', 'billing_cycle': 15},
]

print("=== 測試建立客戶 ===\n")

for i, data in enumerate(test_cases, 1):
    print(f"測試 {i}: {data['name']} / {data['tax_id']}")
    resp = requests.post(url, json=data)
    print(f"  Status: {resp.status_code}")
    print(f"  Response: {resp.text}")
    print()

# 測試查詢客戶列表
print("=== 查詢客戶列表 ===")
resp = requests.get('http://127.0.0.1:8000/api/clients/')
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text}")