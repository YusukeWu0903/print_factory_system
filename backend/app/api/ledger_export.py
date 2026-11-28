"""Export the current database's work orders and their production details."""
from io import BytesIO

from openpyxl import Workbook
from openpyxl.cell import Cell
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from sqlalchemy.orm import joinedload

from app.models.work_order import WorkOrder


COLUMNS = {
    "id":"系統工單號", "date":"訂單日期", "client_id":"客戶編號", "client_name":"客戶名稱",
    "client_order_no":"客戶單號", "plate_number":"製版編號", "item_name":"印件名稱",
    "status":"工單狀態", "quantity":"計價數量", "book_count":"來單本數",
    "completed_quantity":"完成數量", "paper_size":"入紙尺寸", "paper_weight":"紙磅",
    "paper_type":"紙別", "cut_type":"裁別", "paper_input":"入紙數量", "plate_info":"版材",
    "press_size":"印刷尺寸", "press_actual":"印刷實數", "press_waste":"放損",
    "press_runs":"台數", "press_ink":"印刷顏色", "front_side":"正面色數",
    "back_side":"反面色數", "operator":"領機", "finisher":"後加工廠", "due_date":"交期",
    "paper_fee":"紙費", "plate_fee":"版費", "wage":"印工", "total_amount":"總金額",
    "notes":"備註", "ocr_review_notes":"辨識待整理備註", "revision":"修訂次數", "updated_at":"最後更新時間",
}


def append(sheet, values):
    cells = []
    for value in values:
        cell = Cell(sheet, value=value)
        if isinstance(value, str):
            cell.data_type = "s"
        cells.append(cell)
    sheet.append(cells)


def export_ledger(db):
    book = Workbook()
    ledger = book.active
    ledger.title = "工單總表"
    versions = book.create_sheet("學教用紙")
    pieces = book.create_sheet("分項回報")
    runs = book.create_sheet("印刷明細")
    append(ledger, COLUMNS.values())
    append(versions, ["系統工單號","版本","來單數量","尺寸與紙質","紙張用料（令）"])
    append(pieces, ["系統工單號","印件","印刷指示","完成數量"])
    append(runs, ["系統工單號","印件","列次","色數","台數","實際需求","放損","令數","備註"])
    for w in db.query(WorkOrder).options(joinedload(WorkOrder.client)).order_by(WorkOrder.date, WorkOrder.id):
        values = dict(vars(w), client_name=w.client.name, status=w.status.value)
        append(ledger, (values[k] for k in COLUMNS))
        if w.combined:
            for key, label in [("student","學用"),("teacher","教用正文"),("answer","解答")]:
                if key != "answer":
                    paper = w.combined[key+"_paper"]
                    append(versions,[w.id,"學用" if key=="student" else "教用",paper["quantity"],paper["paper"],paper["reams"]])
                item = w.combined[key]
                append(pieces,[w.id,label,item["instruction"],(w.piece_reports or {}).get(key)])
                for number, row in enumerate(item["runs"],1):
                    append(runs,[w.id,label,number,*(row.get(k) for k in ("colors","presses","demand","waste","reams","note"))])
    for sheet in book:
        sheet.freeze_panes = "B2"
        sheet.auto_filter.ref = sheet.dimensions
        for cell in sheet[1]:
            cell.font = Font(bold=True,color="FFFFFF")
            cell.fill = PatternFill("solid",fgColor="335644")
            sheet.column_dimensions[get_column_letter(cell.column)].width = 38 if cell.value in ("印件名稱","備註","最後更新時間") else 19
    output = BytesIO()
    book.save(output)
    return output.getvalue()
