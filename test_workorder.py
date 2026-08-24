import requests
import json

url = 'http://127.0.0.1:8000/api/work-orders/'
data = {
    'date': '2026-08-21',
    'client_id': 1,
    'item_name': '海報印刷',
    'quantity': 100,
    'paper_weight': '250g',
    'paper_type': '道林紙',
    'front_side': '4色',
    'back_side': '0色',
    'operator': '02',
    'notes': '需摺疊加工 UV上光',
    'paper_fee': 800,
    'plate_fee': 1500,
    'wage': 2500
}

resp = requests.post(url, json=data)
print(f'Status: {resp.status_code}')
print(f'Response: {json.dumps(resp.json(), ensure_ascii=False, indent=2)}')

# Also test GET
resp2 = requests.get('http://127.0.0.1:8000/api/work-orders/')
print(f'\nList Status: {resp2.status_code}')
print(f'List: {json.dumps(resp2.json(), ensure_ascii=False, indent=2)}')