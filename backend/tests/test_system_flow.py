"""Isolated API checks; these tests never use the operator's SQLite file."""

import os
import sqlite3
import subprocess
import sys
import textwrap
from datetime import date
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["DEBUG"] = "False"

from app.core.passwords import hash_password  # noqa: E402

os.environ["ADMIN_PASSWORD_HASH"] = hash_password("correct-horse-battery-staple")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.core.database import BACKEND_DIR, Base, get_auth_db, get_db, resolve_database_url  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.core.schema import ensure_schema  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(bind=engine, autoflush=False)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_auth_db] = override_get_db
    with TestClient(app, base_url="https://testserver", headers={"X-Data-Mode": "production"}) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


def test_sandbox_and_production_stay_separate(tmp_path):
    production = tmp_path / "production.db"
    sandbox = tmp_path / "sandbox.db"
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{production.as_posix()}"
    env["SANDBOX_DATABASE_URL"] = f"sqlite:///{sandbox.as_posix()}"
    env["ADMIN_PASSWORD_HASH"] = hash_password("correct-horse-battery-staple")
    script = textwrap.dedent("""
        from fastapi.testclient import TestClient
        from app.main import app

        with TestClient(app, base_url="https://testserver") as client:
            login = client.post("/api/auth/login", json={"password": "correct-horse-battery-staple"})
            assert login.status_code == 200, login.text
            csrf = login.json()["csrf_token"]
            prod = {"X-Data-Mode": "production", "X-CSRF-Token": csrf}
            test = {"X-Data-Mode": "sandbox", "X-CSRF-Token": csrf}
            assert client.get("/api/clients/", headers=prod).json() == []
            assert client.get("/api/clients/", headers=test).json() == []
            response = client.post("/api/clients/", json={"name": "假客戶", "billing_cycle": 15}, headers=test)
            assert response.status_code == 201, response.text
            client_id = response.json()["id"]
            assert client.get("/api/clients/", headers=prod).json() == []
            assert len(client.get("/api/clients/", headers=test).json()) == 1
            order = client.post("/api/work-orders/", json={"date": "2026-10-08", "client_id": client_id, "item_name": "假工單", "quantity": 2}, headers=test)
            assert order.status_code == 201, order.text
            assert client.get("/api/work-orders/", headers=prod).json() == []
            assert len(client.get("/api/work-orders/", headers=test).json()) == 1
            assert client.get("/api/reconciliation/months", params={"client_id": client_id}, headers=test).status_code == 200
            assert client.get("/api/clients/", headers=test).headers["X-Data-Mode"] == "sandbox"
            assert client.get("/api/clients/", headers=prod).headers["X-Data-Mode"] == "production"
            assert client.get("/api/clients/", headers={"X-Data-Mode": "wrong"}).status_code == 400
            assert client.get("/api/clients/").status_code == 400
    """)
    result = subprocess.run(
        [sys.executable, "-c", script], cwd=BACKEND_DIR, env=env, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
    with sqlite3.connect(production) as db:
        assert db.execute("SELECT COUNT(*) FROM clients").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM work_orders").fetchone()[0] == 0
    with sqlite3.connect(sandbox) as db:
        assert db.execute("SELECT COUNT(*) FROM clients").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM work_orders").fetchone()[0] == 1


def login(client):
    response = client.post(
        "/api/auth/login", json={"password": "correct-horse-battery-staple"}
    )
    assert response.status_code == 200
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie and "Secure" in cookie and "SameSite=strict" in cookie
    return {"X-CSRF-Token": response.json()["csrf_token"]}


def create_client(client, headers, billing_cycle=15):
    response = client.post(
        "/api/clients/",
        json={"name": "測試客戶", "billing_cycle": billing_cycle},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def create_pending_order(client, headers, client_id, order_date):
    response = client.post(
        "/api/work-orders/",
        json={
            "date": order_date,
            "client_id": client_id,
            "item_name": f"工單 {order_date}",
            "quantity": 2,
            "client_order_no": f"PO-{order_date}",
            "paper_weight": "150g",
            "paper_type": "道林紙",
            "cut_type": "四開",
            "front_side": 4,
            "back_side": 0,
            "operator": 2,
            "notes": "需摺疊",
            "paper_fee": 10,
            "plate_fee": 20,
            "wage": 30,
        },
        headers=headers,
    )
    assert response.status_code == 201
    order_id = response.json()["id"]
    update = client.patch(
        f"/api/work-orders/{order_id}/status",
        json={"status": "已完成_待請款"},
        headers=headers,
    )
    assert update.status_code == 200
    return order_id


def test_login_protects_read_and_write_and_logout_revokes_session(client):
    assert client.get("/api/clients/").status_code == 401
    assert client.post("/api/clients/", json={"name": "不應建立"}).status_code == 401
    assert client.post("/api/auth/login", json={"password": "wrong"}).status_code == 401

    headers = login(client)
    assert "__Host-print_factory_session" in client.cookies
    assert client.post("/api/clients/", json={"name": "缺少安全碼"}).status_code == 403
    create_client(client, headers)
    assert len(client.get("/api/clients/").json()) == 1

    assert client.post("/api/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/clients/").status_code == 401


def test_password_rotation_invalidates_existing_session(client):
    login(client)
    settings = get_settings()
    previous_hash = settings.ADMIN_PASSWORD_HASH
    try:
        settings.ADMIN_PASSWORD_HASH = hash_password("new-administrator-password")
        assert client.get("/api/clients/").status_code == 401
    finally:
        settings.ADMIN_PASSWORD_HASH = previous_hash


def test_client_validation_and_list_print_details(client):
    headers = login(client)
    for payload in [
        {"name": " ", "billing_cycle": 15},
        {"name": "錯誤統編", "tax_id": "abcdefgh", "billing_cycle": 15},
        {"name": "錯誤結帳日", "billing_cycle": 32},
    ]:
        assert client.post("/api/clients/", json=payload, headers=headers).status_code == 422

    client_id = create_client(client, headers)
    create_pending_order(client, headers, client_id, "2026-09-16")
    listed = client.get("/api/work-orders/").json()[0]
    assert listed["client_order_no"] == "PO-2026-09-16"
    assert listed["paper_weight"] == "150g"
    assert listed["cut_type"] == "四開"
    assert listed["front_side"] == 4
    assert listed["notes"] == "需摺疊"
    assert listed["total_amount"] == 120


def test_client_deletion_rules(client):
    headers = login(client)
    disposable = create_client(client, headers)
    assert client.delete(f"/api/clients/{disposable}", headers=headers).status_code == 204

    protected = create_client(client, headers)
    create_pending_order(client, headers, protected, "2026-10-15")
    response = client.delete(f"/api/clients/{protected}", headers=headers)
    assert response.status_code == 400
    assert client.get(f"/api/clients/{protected}").status_code == 200


def test_cutoff_day_boundaries_and_confirm(client):
    headers = login(client)
    client_id = create_client(client, headers, billing_cycle=15)
    before = create_pending_order(client, headers, client_id, "2026-09-15")
    first = create_pending_order(client, headers, client_id, "2026-09-16")
    last = create_pending_order(client, headers, client_id, "2026-10-15")
    after = create_pending_order(client, headers, client_id, "2026-10-16")

    months = client.get("/api/reconciliation/months", params={"client_id": client_id})
    assert months.json() == ["2026-11", "2026-10", "2026-09"]
    summary = client.get(
        "/api/reconciliation/summary", params={"client_id": client_id, "month": "2026-10"}
    )
    assert summary.status_code == 200
    body = summary.json()
    assert (body["period_start"], body["period_end"]) == ("2026-09-16", "2026-10-15")
    assert {order["id"] for order in body["work_orders"]} == {first, last}
    assert body["total_amount"] == "240.00"

    invalid = client.post(
        "/api/reconciliation/confirm",
        json={"client_id": client_id, "month": "2026-10", "work_order_ids": [first, after]},
        headers=headers,
    )
    assert invalid.status_code == 400
    confirmed = client.post(
        "/api/reconciliation/confirm",
        json={"client_id": client_id, "month": "2026-10", "work_order_ids": [first, last]},
        headers=headers,
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["updated_count"] == 2
    assert {before, after}.isdisjoint({first, last})
    assert client.get(
        "/api/reconciliation/summary", params={"client_id": client_id, "month": "2026-10"}
    ).json()["work_order_count"] == 0


def test_short_month_cutoff_and_year_boundary(client):
    headers = login(client)
    client_id = create_client(client, headers, billing_cycle=31)
    feb_first = create_pending_order(client, headers, client_id, "2026-02-01")
    feb_last = create_pending_order(client, headers, client_id, "2026-02-28")
    create_pending_order(client, headers, client_id, "2026-03-01")
    summary = client.get(
        "/api/reconciliation/summary", params={"client_id": client_id, "month": "2026-02"}
    ).json()
    assert (summary["period_start"], summary["period_end"]) == ("2026-02-01", "2026-02-28")
    assert {order["id"] for order in summary["work_orders"]} == {feb_first, feb_last}

    from app.api.reconciliation import get_billing_period

    assert get_billing_period(2028, 2, 31) == (date(2028, 2, 1), date(2028, 2, 29))
    assert get_billing_period(2027, 1, 15) == (date(2026, 12, 16), date(2027, 1, 15))


def test_database_path_and_legacy_migration(tmp_path):
    assert Path(resolve_database_url("sqlite:///./print_factory.db").database) == BACKEND_DIR / "print_factory.db"

    legacy_path = tmp_path / "legacy.db"
    with sqlite3.connect(legacy_path) as legacy:
        legacy.execute("CREATE TABLE work_orders (id INTEGER PRIMARY KEY, date DATE)")
        legacy.execute("INSERT INTO work_orders (id, date) VALUES (1, '2026-08-24')")

    engine = create_engine(f"sqlite:///{legacy_path.as_posix()}")
    ensure_schema(engine)
    with sqlite3.connect(legacy_path) as migrated:
        columns = {row[1] for row in migrated.execute("PRAGMA table_info(work_orders)")}
        assert "client_order_no" in columns
        assert migrated.execute("SELECT COUNT(*) FROM work_orders").fetchone()[0] == 1
    backups = list((tmp_path / "backups").glob("*.db"))
    assert len(backups) == 1
    with sqlite3.connect(backups[0]) as backup:
        old_columns = {row[1] for row in backup.execute("PRAGMA table_info(work_orders)")}
        assert "client_order_no" not in old_columns
    engine.dispose()

def test_merge_keeps_batch_snapshots_and_rejects_reuse(client):
    headers = login(client)
    cid = create_client(client, headers)
    base = "/api/reconciliation"
    def issue(day):
        oid = create_pending_order(client, headers, cid, day)
        r = client.post(base + "/confirm", headers=headers,
                        json={"client_id": cid, "month": "2026-10", "work_order_ids": [oid]})
        assert r.status_code == 200, r.text
        return r.json()["statement_id"]
    a, b = issue("2026-10-01"), issue("2026-10-02")
    originals = client.get(base + "/statements").json()
    merged = client.post(base + "/statements/merge", headers=headers, json={"ids": [a,b]})
    assert merged.status_code == 200, merged.text
    report = merged.json()
    assert report["total"] == "240.00" and report["sources"] == [a,b]
    assert len(report["lines"]) == 2
    assert client.post(base + "/statements/merge", headers=headers, json={"ids":[a,b]}).status_code == 409
    after = {r["id"]:r for r in client.get(base + "/statements").json()}
    for old in originals:
        assert after[old["id"]]["lines"] == old["lines"]
        assert after[old["id"]]["merged_into"] == report["id"]

def test_order_edit_history_and_stale_revision(client):
    h = login(client)
    cid = create_client(client, h)
    path = "/api/work-orders/"
    created = client.post(path, headers=h, json={"date":"2026-11-25","item_name":"原稿","quantity":10,"client_id":cid}).json()
    url = path + str(created["id"])
    payload = {"expected_revision":created["revision"], "quantity":12}
    result = client.patch(url, headers=h, json=payload)
    assert result.status_code == 200, result.text
    assert result.json()["updated_at"] and result.json()["revision"] > created["revision"]
    assert client.patch(url, headers=h, json={**payload,"quantity":13}).status_code == 409
    assert client.get(url).json()["quantity"] == 12
    history = client.get(url+"/history").json()
    assert [e["action"] for e in history] == ["修改","建立"]
    assert history[0]["changes"]["quantity"] == ["10","12"]
