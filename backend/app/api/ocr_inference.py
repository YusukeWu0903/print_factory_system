"""Conservative field inference for OCR rows from unfamiliar print tickets."""
import re
import unicodedata
from collections import defaultdict
from datetime import date

# Each label names a business concept; units alone do not identify billed quantities.
LABELS = {
    "item_name": "印件名稱|印品名稱|產品名稱|產品名|品名|書名",
    "client_name": "客戶名稱|委託單位|訂購單位",
    "client_order_no": "客戶單號|訂購單號|訂單編號|委印單號",
    "plate_number": "製版編號",
    "date": "訂單日期|工單日期|開單日期|收單日期",
    "due_date": "交貨日期|交期|預交日期",
    "paper_input": "需料明細|需料數量|用紙量|用紙數量|入紙數量|備紙量|領紙量",
    "paper_weight": "紙磅|紙張磅數|紙重|基重",
    "paper_type": "紙種|紙別|紙質",
    "paper_size": "原紙尺寸|入紙尺寸",
    "press_size": "印刷尺寸",
    "press_runs": "印刷台數|台數",
    "finisher": "後加工廠|後送地點|後站",
    "book_count": "訂購本數|訂印本數|印製本數|來單本數",
    "notes": "預生產量|預計產量|生產數量|預計印量",
}
ALIASES = {label: key for key, names in LABELS.items() for label in names.split("|")}
TRANSLATE = str.maketrans("单号数张纸订单产称书种领备厂后预计实货录", "單號數張紙訂單產稱書種領備廠後預計實貨錄")
LABEL = re.compile(r"^(" + "|".join(sorted(ALIASES, key=len, reverse=True)) +
                   r"|[\w]{0,7}(?:單號|編號))\s*[:：]?\s*(.*)$")
UNITS = {
    "paper_input": r"\d+(?:\.\d+)?\s*令(?:\s*[+＋]\s*\d+\s*張)?",
    "paper_weight": r"\d+(?:\.\d+)?\s*(?:gm|gsm|g|g/m2|克)",
    "press_runs": r"\d+(?:\.\d+)?\s*台",
    "book_count": r"[\d,]+(?:\s*\+\s*[\d,]+)?\s*本",
}


def validated(key, value):
    if not value or len(value) > 200 or LABEL.fullmatch(value):
        return None
    if key == "date":
        m = re.fullmatch(r"(\d{3,4})[./年-](\d{1,2})[./月-](\d{1,2})日?",value)
        if m:
            y,m,d = map(int,m.groups())
            try:
                return date(y+1911 if y < 1000 else y,m,d).isoformat()
            except ValueError:
                pass
        return None
    if key in ("plate_number","client_order_no"):
        return value if re.fullmatch(r"[\w./-]{2,64}", value) and re.search(r"\d",value) else None
    if key in UNITS:
        if re.fullmatch(UNITS[key],value,re.I):
            return value
        if key == "press_runs" and re.fullmatch(r"\d+(?:\.\d+)?",value):
            return value
        return None
    return value


def infer_fields(rows, mapped_lines=None):
    tokens = []
    for box, raw, score in rows:
        x,y = zip(*box)
        text = unicodedata.normalize("NFKC",raw).strip().translate(TRANSLATE)
        tokens.append((min(x),min(y),max(x),max(y),text,raw,score))
    matches = defaultdict(list)
    consumed = set()
    evidence = defaultdict(list)
    for i,(left,top,right,bottom,text,raw,score) in enumerate(tokens):
        label = LABEL.fullmatch(text)
        if not label:
            continue
        name, value = label.groups()
        key = ALIASES.get(name,"client_order_no")
        indices = [i]
        source = raw
        confidence = score
        if not value:
            nearby = []
            h = max(1,bottom-top)
            for j,(x,y,x2,y2,v,original,c) in enumerate(tokens):
                if i == j:
                    continue
                # Same printed row first, then directly below the same header.
                if right-2 <= x <= right+14*h and abs(y+y2-top-bottom) < h:
                    nearby.append((0,abs(x-right),j))
                elif bottom-1 <= y <= bottom+2*h and abs(x-left) < h*1.5:
                    nearby.append((1,abs(y-bottom),j))
            if not nearby:
                continue
            _,_,j = min(nearby)
            value,original,c = tokens[j][4:]
            if LABEL.fullmatch(value):
                continue
            confidence = min(score,c)
            source = raw+"　"+original
            consumed.add(j)
            indices.append(j)
        normalized = validated(key,value)
        if normalized is not None:
            strong = confidence >= .85 and name in ALIASES and key != "notes"
            matches[key].append((normalized,source,strong))
            if strong:
                evidence[key].extend(indices)
    for i,(_,_,_,_,value,raw,_) in enumerate(tokens):
        if i not in consumed:
            unit_value = value.rsplit(":",1)[-1].strip()
            if LABEL.fullmatch(value):
                continue
            for key,pattern in UNITS.items():
                if re.fullmatch(pattern,unit_value,re.I):
                    matches[key].append((unit_value,raw,False))
            if re.fullmatch(r"[\d,]+\s*張",unit_value):
                matches["notes"].append((raw,raw,False))
    fields, suggestions = {}, []
    for key,items in matches.items():
        values = {v for v,_,_ in items}
        if len(values)==1 and any(certain for _,_,certain in items):
            fields[key] = items[0][0]
            if mapped_lines is not None:
                mapped_lines.update((i,key) for i in evidence[key])
        else:
            for value,source,_ in dict.fromkeys(items):
                suggestions.append({"key":key,"value":source if key=="notes" else value,"source":source})
    return fields,suggestions
