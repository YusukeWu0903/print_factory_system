"""Read a single Nan Yi production ticket into an editable draft."""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO
import re
from zipfile import ZipFile

from fastapi import HTTPException
from openpyxl import load_workbook
from openpyxl.utils.datetime import from_excel


def reject(message):
    raise HTTPException(422, message)


def amount(value, address):
    try:
        n = Decimal(value or "0")
    except InvalidOperation:
        reject(f"{address} 請填數字")
    if not n.is_finite() or n < 0 or n > 999999999 or n.as_tuple().exponent < -12:
        reject(f"{address} 數量超出範圍")
    return n


def display(n):
    return format(n.normalize(), "f")


def ticket(sheet, epoch):
    if not sheet.max_row or not sheet.max_column or sheet.max_row > 300 or sheet.max_column > 40:
        reject("工作表超出南一單張工單格式")
    cells = {c.coordinate: c for row in sheet.iter_rows() for c in row if c.value is not None}

    def cell(address, allow_formula=False):
        c = cells.get(address)
        if c is None:
            return ""
        if c.data_type == "e":
            reject(f"{address} 有 Excel 錯誤值")
        if c.data_type == "f" and not allow_formula:
            reject(f"{address} 含有非令數公式，請在副本中貼上計算後的值")
        return str(c.value).strip()

    def order_date(address):
        raw = cells[address].value if address in cells else None
        if isinstance(raw, (int, float)):
            raw = from_excel(raw, epoch)
        if isinstance(raw, datetime):
            raw = raw.date()
        if isinstance(raw, date):
            return raw.isoformat()
        match = re.fullmatch(r"(\d{3,4})[./年-](\d{1,2})[./月-](\d{1,2})日?", cell(address))
        if match:
            year, month, day = map(int, match.groups())
            try:
                return date(year + (1911 if year < 1000 else 0), month, day).isoformat()
            except ValueError:
                pass
        if raw:
            reject(f"{address} 日期無法辨認，請填寫完整年月日")
        return ""

    if [cell(a) for a in ("A1","D1","D3")] != ["日期","編號","紙質"]:
        reject("無法辨認南一工作傳票表頭")
    dual = cell("A3") == "學用"
    if not dual and cell("A3") != "本數":
        reject("缺少本數或學用欄")
    headers = [r for r in range(3, sheet.max_row+1) if cell(f"B{r}") == "色數"]
    if len(headers) != (2 if dual else 1):
        reject("印刷數量區段不完整")
    divisor = None
    notes = []
    combined = {}
    previous_end = 0
    warnings = []
    fields = dict(item_name=cell("B2"), date=order_date("B1"), client_order_no=cell("E1"))
    totals = []
    for index, head in enumerate(headers):
        if [cell(f"{c}{head}") for c in "BCDEFG"] != ["色數","台數","實際需求","放損","令數","備註"]:
            reject("印刷明細欄位順序有異動")
        end = next((r for r in range(head+1, sheet.max_row+1) if cell(f"B{r}").startswith("紙張用料合計")), None)
        if not end or end <= head+1:
            reject("缺少用料合計")
        first = head+1
        def formula(r):
            return cell(f"F{r}", allow_formula=True).upper().replace(" ", "").replace("$", "")
        if formula(end) != f"=SUM(F{first}:F{end-1})":
            reject(f"F{end} 合計範圍與明細不符")
        start = 3 if index == 0 else previous_end+1
        if index and cell(f"A{start}") != "教用":
            reject("缺少教用紙材區")
        quantity = cell(f"B{start}")
        size, paper = (cell(f"{c}{start}") for c in "EF")
        instruction = " · ".join(filter(None,[cell(f"{c}{start+1}") for c in "BFG"]))
        ink = cell(f"B{start+2}") if cell(f"A{start+2}") == "印刷顏色" else ""
        group = "teacher" if index else "student"
        combined[group] = {"instruction":" · ".join(filter(None,[instruction,ink])), "runs":[]}
        if index:
            combined["answer"] = {"instruction":"", "runs":[]}
        piece = group
        total = Decimal(0)
        has_quantity = False
        for r in range(first,end):
            base = f"(D{r}+E{r})"
            formulas = {f"=SUM({term}/{unit})": (unit, multiply)
                        for unit in (500,1000) for multiply,term in [(True,f"C{r}*{base}"),(False,base)]}
            rule = formulas.get(formula(r))
            if not rule or (divisor and rule[0] != divisor):
                reject(f"F{r} 的換算公式與南一範本不符，請核對原檔")
            divisor, multiply = rule
            label,colors,presses,demand,waste,note = [cell(f"{c}{r}") for c in "ABCDEG"]
            if index and label:
                if label not in ("教用","教用正文","解答"):
                    reject(f"A{r} 請標明教用或解答")
                piece = "answer" if label == "解答" else "teacher"
            if not any([colors,presses,demand,waste,note]):
                continue
            value = (amount(demand,f"D{r}")+amount(waste,f"E{r}")) / divisor
            if multiply:
                value *= amount(presses,f"C{r}")
            if (multiply and not presses) or not demand:
                warnings.append(f"第 {r} 列缺少台數或實際需求，請核對原檔。")
            total += value
            has_quantity |= bool(demand or waste)
            row = dict(colors=colors,presses=presses,demand=demand,waste=waste,reams=display(value),note=note)
            combined[piece]["runs"].append(row)
            if not dual:
                notes.append(" · ".join(filter(None,[label, f"色數 {colors}" if colors else "", f"台數 {presses}" if presses else "",
                    f"實際需求 {demand}" if demand else "",f"放損 {waste}" if waste else "", f"{display(value)} 令",note])))
        reams = display(total) if has_quantity else ""
        title = "教用" if index else "學用" if dual else "用紙"
        totals.append({"label":title,"reams":reams})
        if dual:
            combined[group+"_paper"] = dict(quantity=quantity,paper=" ".join(filter(None,[size,paper])),reams=reams)
        else:
            fields.update(paper_size=size,paper_type=paper,press_runs=instruction,press_ink=ink,
                          paper_input=reams+" 令" if reams else "")
            if re.fullmatch(r"[1-9][0-9]{0,8}",quantity):
                fields["quantity"] = int(quantity)
            if quantity:
                fields["book_count"] = quantity
                notes.insert(0,"來單本數："+quantity)
        previous_end = end
    if dual and divisor != 1000:
        reject("學教用不同紙範本應使用 2K 公式")
    if cell(f"A{end+1}") != "備註" or cell(f"A{end+2}") != "後加工":
        reject("找不到備註或後加工欄")
    notes.append(cell(f"B{end+1}"))
    plate = cell(f"G{end+1}")
    if plate and plate.replace(" ","") != "新版口再版口":
        notes.append("原單版材："+plate)
    fields.update(cut_type="2K" if divisor == 1000 else "菊全開",combined=combined if dual else None,
                  notes="\n".join(filter(None,notes)),finisher=cell(f"B{end+2}"),due_date=cell(f"G{end+2}"))
    if "quantity" not in fields:
        warnings.append("請核對並填寫工單計價數量；來單本數與放損分開保留。")
    if not fields["item_name"]:
        warnings.append("原檔未填品名，請在工單補填。")
    return {"template": "2K學教用不同紙" if dual else fields["cut_type"]+"單",
            "fields":fields,"totals":totals,"warnings":warnings}


def preview(data):
    try:
        with ZipFile(BytesIO(data)) as archive:
            if len(archive.infolist()) > 250 or sum(i.file_size for i in archive.infolist()) > 8_000_000:
                reject("活頁簿超出單張工單容量")
        book = load_workbook(BytesIO(data), read_only=True, data_only=False, keep_links=False)
        try:
            if len(book.worksheets) != 1:
                reject("請使用一份工作表一張工單的南一範本")
            return ticket(book.active,book.epoch)
        finally:
            book.close()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(422,"無法讀取 Excel，請確認是未加密的 .xlsx 工單") from exc
