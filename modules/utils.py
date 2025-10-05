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
    base = None
    for df in dfs:
        if df is None or df.empty:
            continue
        if "date" not in df.columns:
            continue
        if base is None:
            base = df.copy()
        else:
            base = pd.merge(base, df, on="date", how="outer")
    return base if base is not None else pd.DataFrame()