from app.api.ocr_inference import infer_fields


def token(x,y,text,score=.97):
    width = 12*len(text)
    return ([[x,y],[x+width,y],[x+width,y+16],[x,y+16]],text,score)


def test_unfamiliar_layout_uses_position_units_and_ambiguity():
    rows = [token(15,10,"用紙量"),token(140,10,"7.35令"),
            token(15,45,"訂購單號：AB-23"),token(15,80,"製造單號：MN-45"),
            token(15,115,"預計產量：6,930張"),token(15,150,"成品清單")]
    fields,choices=infer_fields(rows)
    assert fields == {"paper_input":"7.35令"}
    assert {c["value"] for c in choices if c["key"]=="client_order_no"} == {"AB-23","MN-45"}
    assert any("6,930張" in c["source"] for c in choices)
    assert infer_fields([token(10,10,"7.35令")])[0] == {}
    assert infer_fields([token(10,10,"用紙量"),token(10,35,"3令",.6)])[0] == {}
    assert infer_fields([token(10,10,"交貨日期：2027/03/01")])[0] == {"due_date":"2027/03/01"}
