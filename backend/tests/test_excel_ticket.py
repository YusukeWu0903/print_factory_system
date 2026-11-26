"""Integration checks against operator-supplied templates, using in-memory copies."""
import os
from io import BytesIO
from pathlib import Path

import pytest
from openpyxl import load_workbook

from test_system_flow import client, login, create_client


@pytest.mark.parametrize("name,cut,expected", [
    ("南一菊全單.xlsx", "菊全開", ["13"]),
    ("南一2K單.xlsx", "2K", ["6.5"]),
    ("南一2K學教用不同紙.xlsx", "2K", ["6.5","1.6"]),
])
def test_nanyi_template(client, name, cut, expected):
    directory = os.environ.get("NANYI_TEMPLATE_DIR")
    if not directory:
        pytest.skip("Set NANYI_TEMPLATE_DIR to check the operator's original templates")
    source = Path(directory) / name
    h = login(client)
    cid = create_client(client,h)
    url = "/api/work-orders/excel-preview"
    original = client.post(url, headers=h, content=source.read_bytes())
    assert original.status_code == 200, original.text
    assert all(x["reams"] == "" for x in original.json()["totals"])
    book = load_workbook(source)
    s = book.active
    dual = len(expected) == 2
    first = 7 if dual else 8
    def populate(row, values):
        for col,value in values.items():
            s[col+str(row)] = value
    populate(1, {"B":"115.11.25", "E":"11-547"})
    populate(2, {"B":"範本測試"})
    populate(3, {"B":"1600+150", "E":"31×43", "F":"60g珍白"})
    populate(first, {"B":"1/1", "C":3, "D":1800, "E":50})
    populate(first+1, {"C":0.5, "D":920, "E":30})
    if dual:
        populate(11, {"B":"200+100", "F":"70g上質 UPM"})
        populate(16, {"A":"教用", "C":3,"D":350,"E":50})
        populate(17, {"A":"解答","C":0.5,"D":350,"E":50})
    def upload():
        out = BytesIO()
        book.save(out)
        return client.post(url,headers=h,content=out.getvalue())
    result = upload()
    assert result.status_code == 200, result.text
    assert [x["reams"] for x in result.json()["totals"]] == expected
    fields = result.json()["fields"]
    assert fields["cut_type"] == cut and fields["date"] == "2026-11-25"
    assert fields["client_order_no"] == "11-547" and "quantity" not in fields
    assert client.get("/api/work-orders/").json() == []
    order = {**fields, "client_id":cid,"quantity":1, "status":"已請款","source_hash":result.json()["source_hash"]}
    payload = {"orders":[order]}
    failed = client.post("/api/work-orders/migrate", headers=h, json={"orders":[order,{**order,"client_id":999999}]})
    assert failed.status_code == 422
    assert client.get("/api/work-orders/").json() == []
    saved = client.post("/api/work-orders/migrate",headers=h,json=payload)
    assert saved.status_code == 200, saved.text
    assert len(saved.json()["added"]) == 1
    assert client.post("/api/work-orders/migrate",headers=h,json=payload).json()["added"] == []
    stored = client.get("/api/work-orders/"+str(saved.json()["added"][0])).json()
    assert stored["status"] == "已請款"
    if dual:
        spec = stored["combined"]
        assert spec["teacher_paper"]["quantity"] == "200+100"
        assert spec["student_paper"]["paper"] == "31×43 60g珍白"
        assert spec["teacher_paper"]["paper"] == "70g上質 UPM"
        assert spec["answer"]["runs"][0]["reams"] == "0.4"
    else:
        assert stored["paper_input"] == expected[0]+" 令"
        assert "1600+150" in stored["notes"] and "放損 50" in stored["notes"]
    s[f"F{first}"] = "=1"
    assert upload().status_code == 422
