from my_marketplace_etl.adapters.postgres.upsert_query import build_upsert_query


def test_postgres_upsert_query_generates_on_conflict_with_excluded():
    rows = [{"order_id": "1", "seller_id": "a", "status": "PAID"}]
    query, params = build_upsert_query(
        table_name="orders",
        rows=rows,
        conflict_columns=["order_id", "seller_id"],
        update_columns=["status"],
    )
    assert 'INSERT INTO "orders"' in query
    assert "ON CONFLICT" in query
    assert 'EXCLUDED."status"' in query
    assert "$1" in query
    assert params == ("1", "a", "PAID")


def test_postgres_upsert_query_returns_empty_for_no_rows():
    query, params = build_upsert_query("orders", [], ["order_id"], ["status"])
    assert query == ""
    assert params == ()
