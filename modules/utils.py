import pandas as pd

def try_parse_dates(series: pd.Series):
    try:
        return pd.to_datetime(series, errors="coerce")
    except Exception:
        return series

def is_timeseries(series: pd.Series) -> bool:
    try:
        s = pd.to_datetime(series, errors="coerce")
        return s.notna().mean() > 0.7
    except Exception:
        return False

def outer_merge_on_date(dfs):
    """
    Safely outer merge a list of dataframes on 'date',
    coercing all date columns to datetime64 and ensuring unique column names.
    """
    if not dfs:
        return None

    # Normalize 'date' column types
    for i, df in enumerate(dfs):
        if "date" not in df.columns:
            continue
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        dfs[i] = df

    base = dfs[0]
    for df in dfs[1:]:
        try:
            base = pd.merge(base, df, on="date", how="outer")
        except ValueError:
            # Force datetime for both sides
            base["date"] = pd.to_datetime(base["date"], errors="coerce")
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            base = pd.merge(base, df, on="date", how="outer")
    return base.sort_values("date").reset_index(drop=True)