def build_upsert_query(
    table_name: str,
    rows: list[dict],
    conflict_columns: list[str],
    update_columns: list[str],
) -> tuple[str, tuple]:
    if not rows:
        return "", ()

    columns = list(rows[0].keys())
    n_columns = len(columns)
    placeholders = []
    for _ in rows:
        group = ", ".join(["?" for _ in range(n_columns)])
        placeholders.append(f"({group})")
    all_values_template = ", ".join(placeholders)
    all_values = tuple(value for row in rows for value in row.values())
    insert_columns = ", ".join(columns)
    conflict_clause = ", ".join(conflict_columns)
    if update_columns:
        update_clause = ", ".join([f"{col} = excluded.{col}" for col in update_columns])
        on_conflict = f"ON CONFLICT ({conflict_clause}) DO UPDATE SET {update_clause}"
    else:
        on_conflict = f"ON CONFLICT ({conflict_clause}) DO NOTHING"
    query = f"""
        INSERT INTO {table_name} ({insert_columns})
        VALUES {all_values_template}
        {on_conflict}
    """
    return query, all_values
