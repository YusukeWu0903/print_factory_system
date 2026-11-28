from app.api.photo_ocr import candidates


def test_production_ticket_materials_and_job_quantities():
    # Transcribed OCR tokens in reading order, including joined supplier phone numbers.
    lines = [
        "工單單号：1511-613", "客户名称", "中参", "交貨日期", "115下南億國中地理C卷6學用正式版",
        "印件名", "客户單号21125-02", "印製數量", "1,700+150本", "成品規格",
        "紙張規格", "2令06-2472089", "31*43英时", "60g.60g珍白道林", "澤福庫存", "2.98",
        "488張06-2472089", "31*43英时", "60g.60g珍白道林", "實數", "放損", "印刷尺寸",
        "1850車", "150車", "2K", "正1反1", "926車", "50車", "2K", "正1反1", "完工數量",
    ]
    def read(tokens):
        return candidates([([[0,i*20],[10,i*20],[10,i*20+10],[0,i*20+10]],t,.99) for i,t in enumerate(tokens)])
    f = read(lines)
    assert f["client_order_no"] == "21125-02" and f["item_name"] == lines[4]
    assert f["paper_input"] == "2 令＋488 張" and f["paper_size"] == "31 × 43 英吋"
    assert f["paper_type"] == "珍白道林" and f["book_count"] == "1,700+150本"
    assert f["press_size"] == "2K" and (f["front_side"],f["back_side"]) == (1,1)
    assert "quantity" not in f and "completed_quantity" not in f
    lines[lines.index("488張06-2472089")+2] = "70g上質"
    assert "paper_input" not in read(lines)
