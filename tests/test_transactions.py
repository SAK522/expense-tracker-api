import pytest

PROTECTED_ROUTES = [
    ("get", "/transactions"),
    ("post", "/transactions"),
    ("get", "/transactions/1"),
    ("put", "/transactions/1"),
    ("delete", "/transactions/1"),
    ("get", "/summary"),
]


def _tx(**overrides):
    data = {"amount": "450.00", "type": "expense", "category": "Food",
            "note": "Lunch", "date": "2026-11-10"}
    data.update(overrides)
    return data


@pytest.mark.parametrize("method,path", PROTECTED_ROUTES)
def test_every_protected_route_rejects_missing_token(client, method, path):
    r = getattr(client, method)(path)
    assert r.status_code == 401


def test_create_and_get_transaction(client, auth_headers):
    r = client.post("/transactions", json=_tx(), headers=auth_headers)
    assert r.status_code == 201
    tx = r.json()
    assert tx["amount"] == "450.00" and tx["category"] == "Food"

    r = client.get(f"/transactions/{tx['id']}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["id"] == tx["id"]


def test_invalid_transactions_rejected(client, auth_headers):
    for bad in (_tx(amount="-5"), _tx(amount="0"), _tx(type="gift"), _tx(category=""), _tx(date="not-a-date")):
        assert client.post("/transactions", json=bad, headers=auth_headers).status_code == 422


def test_list_filters_by_month_category_and_type(client, auth_headers):
    client.post("/transactions", json=_tx(date="2026-11-01"), headers=auth_headers)
    client.post("/transactions", json=_tx(date="2026-11-30", category="Travel"), headers=auth_headers)
    client.post("/transactions", json=_tx(date="2026-10-31"), headers=auth_headers)
    client.post("/transactions", json=_tx(type="income", category="Salary", amount="50000"), headers=auth_headers)

    assert len(client.get("/transactions", headers=auth_headers).json()) == 4
    assert len(client.get("/transactions?month=2026-11", headers=auth_headers).json()) == 3
    assert len(client.get("/transactions?month=2026-10", headers=auth_headers).json()) == 1
    assert len(client.get("/transactions?category=food", headers=auth_headers).json()) == 2  # case-insensitive
    assert len(client.get("/transactions?type=income", headers=auth_headers).json()) == 1
    assert client.get("/transactions?month=2026-13", headers=auth_headers).status_code == 422


def test_update_transaction(client, auth_headers):
    tx = client.post("/transactions", json=_tx(), headers=auth_headers).json()
    r = client.put(f"/transactions/{tx['id']}", json={"amount": "500.50", "note": None}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["amount"] == "500.50"
    assert r.json()["note"] is None
    assert r.json()["category"] == "Food"  # untouched fields stay the same


def test_delete_transaction(client, auth_headers):
    tx = client.post("/transactions", json=_tx(), headers=auth_headers).json()
    assert client.delete(f"/transactions/{tx['id']}", headers=auth_headers).status_code == 204
    assert client.get(f"/transactions/{tx['id']}", headers=auth_headers).status_code == 404


def test_ownership_guard_blocks_other_users(client, auth_headers, other_headers):
    tx = client.post("/transactions", json=_tx(), headers=auth_headers).json()
    tx_id = tx["id"]

    # Arjun can't see, edit, or delete Priya's transaction — it looks like it doesn't exist.
    assert client.get(f"/transactions/{tx_id}", headers=other_headers).status_code == 404
    assert client.put(f"/transactions/{tx_id}", json={"amount": "1"}, headers=other_headers).status_code == 404
    assert client.delete(f"/transactions/{tx_id}", headers=other_headers).status_code == 404
    assert client.get("/transactions", headers=other_headers).json() == []

    # And Priya's data is unchanged.
    assert client.get(f"/transactions/{tx_id}", headers=auth_headers).json()["amount"] == "450.00"


def test_summary_totals(client, auth_headers, other_headers):
    client.post("/transactions", json=_tx(type="income", category="Salary", amount="50000", date="2026-11-01"), headers=auth_headers)
    client.post("/transactions", json=_tx(amount="450.00", date="2026-11-10"), headers=auth_headers)
    client.post("/transactions", json=_tx(amount="1200.50", date="2026-11-20"), headers=auth_headers)
    client.post("/transactions", json=_tx(amount="999", date="2026-10-15"), headers=auth_headers)
    # Another user's data must not leak into Priya's summary.
    client.post("/transactions", json=_tx(amount="77777", date="2026-11-05"), headers=other_headers)

    s = client.get("/summary?month=2026-11", headers=auth_headers).json()
    assert s["total_income"] == "50000.00"
    assert s["total_expense"] == "1650.50"
    assert s["balance"] == "48349.50"
    assert s["transaction_count"] == 3
    assert s["start_date"] == "2026-11-01" and s["end_date"] == "2026-11-30"

    all_time = client.get("/summary", headers=auth_headers).json()
    assert all_time["total_expense"] == "2649.50"
    assert all_time["transaction_count"] == 4

    ranged = client.get("/summary?start_date=2026-11-10&end_date=2026-11-20", headers=auth_headers).json()
    assert ranged["total_expense"] == "1650.50" and ranged["total_income"] == "0.00"


def test_summary_empty_and_bad_params(client, auth_headers):
    s = client.get("/summary", headers=auth_headers).json()
    assert s["balance"] == "0.00" and s["transaction_count"] == 0
    assert client.get("/summary?month=2026-11&start_date=2026-11-01", headers=auth_headers).status_code == 422
    assert client.get("/summary?start_date=2026-12-01&end_date=2026-11-01", headers=auth_headers).status_code == 422
