"""Local photo OCR for the public trial only. Return suggestions, never write an order."""
import io
import re
from datetime import date
from functools import lru_cache
from threading import BoundedSemaphore

import numpy as np
from fastapi import APIRouter, HTTPException, Request
from PIL import Image, ImageOps, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool

router = APIRouter()
slot = BoundedSemaphore(1)
MAX_BYTES = 12 * 1024 * 1024


@lru_cache(maxsize=1)
def engine():
    from rapidocr_onnxruntime import RapidOCR
    return RapidOCR(intra_op_num_threads=2, inter_op_num_threads=1, det_limit_type="max",
                    det_limit_side_len=1800)


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
    for key, pattern in [('item_name',r'(?:產品名稱|产品名称|印件名[稱称]|品名|高[參参])'),
                         ('client_order_no',r'客[戶户][單单][號号]')]:
        value = following(pattern)
        if value:
            fields[key] = value
    text = " ".join(t for _,t,_ in rows)
    d = re.search(r'(?<!\d)(1\d{2}|20\d\d)\s*[年./-]\s*(\d{1,2})\s*[月./-]\s*(\d{1,2})(?!\d)',text)
    if d:
        y,m,day=map(int,d.groups())
        try: fields['date']=date(y+1911 if y<200 else y,m,day).isoformat()
        except ValueError: pass
    weight=re.search(r'(?<!\d)(\d{2,3})\s*(?:gm|g)(?![a-z])',text,re.I)
    if weight: fields['paper_weight']=weight[1]+'g'
    return fields


def recognize(data):
    import pillow_heif
    pillow_heif.register_heif_opener()
    try:
        with Image.open(io.BytesIO(data)) as original:
            if original.format not in {'JPEG','PNG','HEIF','WEBP'} or original.width*original.height > 24_000_000:
                raise HTTPException(422,"僅支援 2400 萬像素以內的工單照片")
            img=ImageOps.exif_transpose(original).convert("RGB")
            img.thumbnail((2200,2200))
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise HTTPException(422,"無法讀取照片")
    rows,_=engine()(np.asarray(img)[:,:,::-1].copy())
    rows=rows or []
    return {"fields": candidates(rows), "texts":[text for _,text,_ in rows]}


@router.post("/recognize")
async def recognize_photo(request: Request):
    if request.headers.get("X-Data-Mode") != "sandbox":
        raise HTTPException(403,"僅供沙盒使用")
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
