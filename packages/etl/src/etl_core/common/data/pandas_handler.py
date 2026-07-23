import pandas as pd


def merge_union_on_keys(
    df_principal: pd.DataFrame, df_secondary: pd.DataFrame, keys: list[str]
) -> pd.DataFrame:
    if not df_principal.empty and not df_secondary.empty:
        df_missing = df_secondary.merge(df_principal[keys], on=keys, how="left", indicator=True)
        df_missing = df_missing[df_missing["_merge"] == "left_only"].drop(columns=["_merge"])
        return pd.concat([df_principal, df_missing], ignore_index=True)
    return df_principal if not df_principal.empty else df_secondary
