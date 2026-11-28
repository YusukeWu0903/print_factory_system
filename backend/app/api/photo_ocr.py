"""Local photo OCR for work-order drafts. Return suggestions, never write an order."""
import io
import re
import unicodedata
from datetime import date
from functools import lru_cache
from threading import BoundedSemaphore

from fastapi import APIRouter, HTTPException, Request
from starlette.concurrency import run_in_threadpool

router = APIRouter()
slot = BoundedSemaphore(1)
MAX_BYTES = 12 * 1024 * 1024


@lru_cache(maxsize=1)
def engine():
    from rapidocr_onnxruntime import RapidOCR
    return RapidOCR(intra_op_num_threads=2, inter_op_num_threads=1, det_limit_type="max",
                    det_limit_side_len=1800)


def production_ticket(lines):
    """Map the labelled sections of the 平面印刷工單; repeated tables have different owners."""
    fields = {}
    def unique(key, values):
        choices = set(values)
        if len(choices) == 1:
            fields[key] = choices.pop()

    def section(start, ends):
        pos = next((i for i,t in enumerate(lines) if re.fullmatch(start,t)), None)
        if pos is None:
            return []
        tail = lines[pos+1:]
        return tail[:next((i for i,t in enumerate(tail) if re.fullmatch(ends,t)),len(tail))]

    for i,t in enumerate(lines):
        if re.fullmatch(r"印件名(?:稱|称)?[:：]?",t):
            nearby = lines[max(0,i-2):i] + lines[i+1:i+3]
            unique("item_name", (v for v in nearby if re.search(r"(學用|学用|教用|正式版|[考試试]卷)",v)))
        if re.fullmatch("印[製制][數数]量[:：]?",t) and i+1 < len(lines):
            if re.fullmatch(r"[\d,]+(?:\s*[+＋]\s*[\d,]+)?本",lines[i+1]):
                fields["book_count"] = lines[i+1]
    paper = section(r"[紙纸][張张][規规]格", r"[實实][數数]|放[損损]|印刷尺寸")
    sizes = [m.groups() for t in paper if (m := re.fullmatch(r"(\d+(?:\.\d+)?)\s*[*xX×]\s*(\d+(?:\.\d+)?)\s*英[吋寸时]",t))]
    unique("paper_size",(f"{w} × {h} 英吋" for w,h in sizes))
    types = [m[1] for t in paper if (m := re.fullmatch(r"(?:\d+(?:\.\d+)?g[.． ]*)+([㐀-鿿]+)",t,re.I))]
    unique("paper_type", types)
    # Some scans join the material quantity and the supplier's telephone into one token.
    amounts = [m.groups() for t in paper if (m := re.fullmatch(r"(\d+(?:\.\d+)?)(令|張|张)(?:\s*0\d{1,2}[-－]\d{6,8})?",t))]
    if len(set(types)) == len(set(sizes)) == 1 and amounts:
        units = [u.replace('张','張') for _,u in amounts]
        if len(units) == len(set(units)):
            fields["paper_input"] = "＋".join(n+" "+u for (n,_),u in zip(amounts,units))
    printing = section("印刷尺寸", "完工[數数]量|製作規格|制作规格")
    unique("press_size",(v for v in printing if re.fullmatch(r"\d+[Kk]",v)))
    colors = {m.groups() for t in printing if (m := re.fullmatch(r"正(\d+)反(\d+)",t))}
    if len(colors) == 1:
        front,back = colors.pop()
        fields.update(front_side=int(front),back_side=int(back))
    return fields


def is_manufacturing_notice(texts):
    return any(re.search(r"[製制]造通知[單单]", t) for t in texts) and any(
        re.search(r"出版[單单][號号]", t) for t in texts)


def notice_fields(rows):
    lines = [unicodedata.normalize("NFKC", t).strip() for _,t,score in rows if score >= .65]
    fields, notes = {}, []

    def single(pattern, source):
        values = {m[1].strip() for line in source if (m := re.search(pattern, line))}
        return values.pop() if len(values) == 1 else ""

    for key, pattern in {
        "client_order_no": r"^[製制]造通知[單单]\s*:\s*(\d+)\s*$",
        "item_name": r"^[產产座]品名(?:[稱称])?\s*:\s*(.+)",
        "finisher": r"(?:後|后)站\s*:\s*([㐀-鿿]+)",
        "press_runs": r"^共\s*(\d+)\s*台$",
    }.items():
        value = single(pattern,lines)
        if value:
            fields[key] = value
    if any("翰林出版" in line for line in lines):
        fields["client_name"] = "翰林出版"
    planned = single(r"[預预]生[產产]量\s*:\s*([\d,]+)",lines)
    if planned:
        unit = " 張" if any(re.fullmatch(re.escape(planned)+r"\s*[張张]",t) for t in lines) else ""
        notes.append("預生產量："+planned+unit)
    start = next((i for i,t in enumerate(lines) if re.search("需料明[細细]",t)), None)
    if start is not None:
        material = []
        for line in lines[start+1:]:
            if re.search(r"[備备][註注]|印量明[細细]",line):
                break
            material.append(line)
        sheets = [re.search(r'(.+?)(\d+(?:\.\d+)?)"\s*[*×x]\s*(\d+(?:\.\d+)?)"\s*[*×x]\s*(\d+(?:\.\d+)?)gm?',t,re.I) for t in material]
        sheets = [m for m in sheets if m]
        amounts = [m[1] for t in material if (m := re.fullmatch(r"(\d+(?:\.\d+)?)\s*令",t))]
        if len(sheets) == 1:
            name,width,height,weight = sheets[0].groups()
            fields.update(paper_type=re.sub(r"^\d+\s*", "", name).translate(str.maketrans("强纸","強紙")),
                          paper_size=f"{width} × {height} 英吋", paper_weight=weight+"g")
            if len(amounts) == 1:
                fields["paper_input"] = amounts[0]+" 令"
    details = [t for t in lines if re.match(r"^第\s*\d+(?:\s*[-~～至]\s*\d+)?\s*台",t) and re.search(r"印\s*\d",t)]
    if any(re.search("印量明[細细]",t) for t in lines):
        notes.append("印量明細（請逐台對照原單，含校車損及分台用色）")
        notes.extend(details)
    if notes:
        fields["notes"] = "\n".join(notes)
    return fields


def candidates(rows):
    fields = {}
    def following(label):
        for index, (box, text, score) in enumerate(rows):
            m = re.match(label + r"\s*[:：]?\s*(.*)$", text)
            if not m or score < .75:
                continue
            if m[1]:
                return m[1]
            right = [(b[0][0], t) for b,t,c in rows if c >= .75 and b[0][0] >= box[1][0]-3
                     and abs(b[0][1]-box[0][1]) < max(8, (box[2][1]-box[0][1])*.65)]
            if right:
                return min(right)[1]
        return ""
    reliable = [t.strip() for _,t,c in rows if c >= .75]
    nanyi = any("南一書局" in t or "南一书局" in t for t in reliable)
    if nanyi:
        fields["client_name"] = "南一書局"
    for key, pattern in [('item_name',r'(?:產品名稱|产品名称|印件名[稱称]|品名|[高中小][參参])'),
                         ('client_order_no',r'(?:客[戶户][單单][號号]|[編编][號号])' if nanyi else r'客[戶户][單单][號号]')]:
        value = following(pattern)
        if value:
            fields[key] = value
    # On photographed tickets, perspective can move values below the label baseline.
    if nanyi:
        for i,t in enumerate(reliable[:-1]):
            following_text = reliable[i+1]
            if re.fullmatch(r"[編编][號号][:：]?", t) and re.fullmatch(r"[0-9A-Za-z]+[-－][0-9A-Za-z-]+", following_text):
                fields["client_order_no"] = following_text
        for (_,label,label_score), (_,title,title_score) in zip(rows, rows[1:]):
            if (re.fullmatch(r"[高中小][參参]", label.strip()) and label_score >= .65
                    and title_score >= .85 and len(title.strip()) >= 4):
                fields.setdefault("item_name", title.strip())
    text = " ".join(reliable)
    d = re.search(r'(?<!\d)(1\d{2}|20\d\d)\s*[年./-]\s*(\d{1,2})\s*[月./-]\s*(\d{1,2})(?!\d)',text)
    if d:
        y,m,day=map(int,d.groups())
        try: fields['date']=date(y+1911 if y<200 else y,m,day).isoformat()
        except ValueError: pass
    weight=re.search(r'(?<!\d)(\d{2,3})\s*(?:gm|g)(?![a-z])',text,re.I)
    student = next((i for i,t in enumerate(reliable) if t in ("學用","学用")), None)
    teacher = next((i for i,t in enumerate(reliable) if t == "教用"), None)
    if nanyi and student is not None and teacher is not None and student < teacher:
        combined = {k: {"instruction":"","runs":[]} for k in ("student","teacher","answer")}
        for key, start, stop in (("student",student,teacher),("teacher",teacher,len(reliable))):
            block = reliable[start+1:stop]
            head = block[:next((i for i,t in enumerate(block) if "台數" in t or "台数" in t), 6)]
            qty = next((t for t in head if re.fullmatch(r"\d+(?:\s*[+＋]\s*\d+)?",t)), "")
            paper = [t for t in head if re.search(r"\d\s*[xX×]\s*\d|\d\s*(?:gm|g)",t,re.I)]
            combined[key+"_paper"] = {"quantity":qty,"paper":" ".join(paper),"reams":""}
        fields["combined"] = combined
    elif weight:
        fields['paper_weight']=weight[1]+'g'
    finisher = following(r"(?:後|后)加工(?:廠|厂)?")
    if finisher and finisher not in ("交期","日期"):
        fields["finisher"] = finisher
    if any(re.match(r"工[單单][單单][號号]",t) for t in reliable) and any(re.match("印件名",t) for t in reliable):
        fields.update(production_ticket(reliable))
    if is_manufacturing_notice([t for _,t,_ in rows]):
        fields.update(notice_fields(rows))
    return fields


def recognize(data):
    import numpy as np
    from PIL import Image, ImageOps, UnidentifiedImageError
    import pillow_heif
    pillow_heif.register_heif_opener()
    try:
        with Image.open(io.BytesIO(data)) as original:
            if original.format not in {'JPEG','PNG','HEIF','WEBP'} or original.width*original.height > 24_000_000:
                raise HTTPException(422,"僅支援 2400 萬像素以內的工單照片")
            img=ImageOps.exif_transpose(original).convert("RGB")
            header = img.crop((0, 0, img.width//2, img.height//5))
            img.thumbnail((2200,2200))
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise HTTPException(422,"無法讀取照片")
    rows,_=engine()(np.asarray(img)[:,:,::-1].copy())
    rows=rows or []
    if is_manufacturing_notice([t for _,t,_ in rows]) and not any("翰林出版" in t for _,t,_ in rows):
        header.thumbnail((1600,1000))
        header_rows,_ = engine()(np.asarray(header)[:,:,::-1].copy())
        rows.extend(row for row in (header_rows or []) if "翰林出版" in row[1] and row[2] >= .85)
    from app.api.ocr_inference import infer_fields
    texts = [text for _,text,_ in rows]
    known = (is_manufacturing_notice(texts) or any("南一書局" in t or "南一书局" in t for t in texts)
             or (any(re.match(r"工[單单][單单][號号]",t) for t in texts) and any(re.match("印件名",t) for t in texts)))
    mapped_lines = {}
    inferred, suggestions = infer_fields(rows, mapped_lines)
    fields = inferred
    if known:
        # The dedicated parser knows how this vendor separates print versions.
        fields = candidates(rows)
        suggestions = [s for s in suggestions if s["key"] not in fields]
    # A vendor rule may reinterpret a generic match. Retain the source in review
    # unless the field and the value agree. Never discard a partially matched line.
    mapped_lines = {i:key for i,key in mapped_lines.items() if fields.get(key) == inferred[key]}
    # Whole text values from dedicated templates can also be accounted for.
    # Keep standalone numbers and mixed-content rows for their table context.
    for i,text in enumerate(texts):
        value = unicodedata.normalize("NFKC",text.strip())
        if i in mapped_lines or value.isdecimal():
            continue
        keys = [key for key,field in fields.items() if isinstance(field,str)
                and value == unicodedata.normalize("NFKC",field.strip())]
        if len(keys) == 1:
            mapped_lines[i] = keys[0]
    return {"fields": fields, "suggestions": suggestions, "texts":texts, "mapped_lines":mapped_lines}


@router.post("/recognize")
async def recognize_photo(request: Request):
    if not slot.acquire(blocking=False):
        raise HTTPException(429,"辨識中，請稍後再試")
    try:
        data=bytearray()
        async for chunk in request.stream():
            if len(data)+len(chunk)>MAX_BYTES: raise HTTPException(413,"照片上限為 12 MB")
            data.extend(chunk)
        return await run_in_threadpool(recognize,data)
    finally:
        slot.release()
