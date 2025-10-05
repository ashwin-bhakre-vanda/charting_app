import os
import pandas as pd
import numpy as np
import requests
from typing import Optional, Dict, List

BASE = os.getenv("VANDA_BASE_URL", "https://api.vandaxasset.com")
_API_KEY = os.getenv("VANDA_XASSET_API_KEY", os.getenv("VANDA_API_KEY",""))

def set_key(key: str):
    global _API_KEY
    _API_KEY = key
    os.environ["VANDA_XASSET_API_KEY"] = key

def have_key() -> bool:
    return bool(_API_KEY)

def _headers() -> Dict[str,str]:
    return {"x-api-key": _API_KEY} if _API_KEY else {}

def _mock_ts(n=250, name="xasset_value"):
    rng = np.random.default_rng(0)
    idx = pd.date_range(end=pd.Timestamp.today().normalize(), periods=n, freq="D")
    return pd.DataFrame({"date": idx, name: rng.normal(0,1,n).cumsum()})

def filter_list(asset: Optional[str]=None, geography: Optional[str]=None, sector: Optional[str]=None) -> pd.DataFrame:
    params = {}
    if asset: params["asset"] = asset
    if geography: params["geography"] = geography
    if sector: params["sector"] = sector
    try:
        r = requests.get(f"{BASE}/filter-list", params=params, headers=_headers(), timeout=30)
        r.raise_for_status()
        return pd.DataFrame(r.json())
    except Exception:
        return _mock_ts()

def field_mappings(model: Optional[str]=None) -> pd.DataFrame:
    params = {}
    if model: params["model"] = model
    try:
        r = requests.get(f"{BASE}/field-mappings", params=params, headers=_headers(), timeout=30)
        r.raise_for_status()
        return pd.DataFrame(r.json())
    except Exception:
        return pd.DataFrame()

def fields_for_series(series_id: str) -> List[str]:
    try:
        df = field_mappings()
        if df.empty:
            return []
        if "series_id" not in df.columns:
            for c in ["_id","timeseries_id","series","id"]:
                if c in df.columns:
                    df = df.rename(columns={c:"series_id"})
                    break
        candidates = [c for c in df.columns if c.lower() in ("field","field_name","name")]
        if "series_id" in df.columns:
            sub = df[df["series_id"].astype(str).str.upper()==str(series_id).upper()]
        else:
            sub = df
        fields = []
        for c in candidates:
            fields += sub[c].dropna().astype(str).unique().tolist()
        return list(dict.fromkeys(fields))
    except Exception:
        return []

def timeseries(series_id: str,
               field_name: Optional[str]=None,
               start_date: Optional[str]=None,
               end_date: Optional[str]=None,
               label: Optional[str]=None,
               frequency: Optional[str]=None,
               rolling_sum: Optional[str]=None,
               z_score: Optional[str]=None) -> pd.DataFrame:
    params = {"series_id": series_id}
    if field_name: params["field_name"] = field_name
    if start_date: params["start_date"] = start_date
    if end_date: params["end_date"] = end_date
    if frequency: params["frequency"] = frequency
    if rolling_sum: params["rolling_sum"] = rolling_sum
    if z_score: params["z_score"] = z_score

    try:
        r = requests.get(f"{BASE}/timeseries", params=params, headers=_headers(), timeout=60)
        r.raise_for_status()
        df = pd.DataFrame(r.json())
        if "date" not in df.columns:
            for c in ["time","timestamp","dt"]:
                if c in df.columns:
                    df = df.rename(columns={c:"date"})
                    break
        value_cols = [c for c in df.columns if c != "date"]
        if not value_cols:
            return pd.DataFrame()
        out_label = label or f"{series_id}{'·'+field_name if field_name else ''} (XAsset)"
        z_cols = [c for c in value_cols if 'z' in c.lower()]
        col = z_cols[0] if z_cols else value_cols[0]
        return df[["date", col]].rename(columns={col: out_label})
    except Exception:
        return _mock_ts(name=label or f"{series_id} (mock)")
