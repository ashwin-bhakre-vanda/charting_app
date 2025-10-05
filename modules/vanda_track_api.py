import os
import pandas as pd
import numpy as np
import requests
from typing import Optional

VT_BASE_TICKERS = os.getenv("VANDATRACK_TICKERS_URL", "https://www.vandatrack.com/tickers/api/")
VT_BASE_OPTIONS = os.getenv("VANDATRACK_OPTIONS_URL", "https://www.vandatrack.com/option/api/")
_API_KEY = os.getenv("VANDATRACK_API_KEY","")

def set_key(key: str):
    global _API_KEY
    _API_KEY = key
    os.environ["VANDATRACK_API_KEY"] = key

def have_key() -> bool:
    return bool(_API_KEY)

def _mock_ts(n=250, name="retail_flow"):
    rng = np.random.default_rng(1)
    idx = pd.date_range(end=pd.Timestamp.today().normalize(), periods=n, freq="D")
    return pd.DataFrame({"date": idx, name: rng.normal(0,1,n).cumsum()})

def _build_params(flow_type: str, from_date: Optional[str], to_date: Optional[str]):
    return {
        "type": flow_type,
        "from_date": from_date or "2019-01-01",
        "to_date": to_date or pd.Timestamp.today().strftime("%Y-%m-%d"),
        "auth_token": _API_KEY,
        "saved_list": "false",
        "pagination": "false"
    }

def retail_flow(tickers: Optional[str], flow_type: str="net", from_date: Optional[str]=None, to_date: Optional[str]=None, label: Optional[str]=None) -> pd.DataFrame:
    if not have_key():
        return _mock_ts(name=label or ("Aggregate Retail Flow (net)" if not tickers else f"{tickers} retail (mock)"))
    params = _build_params(flow_type, from_date, to_date)
    default_label = ""
    if tickers and tickers.strip():
        params["tickers"] = tickers.strip()
        default_label = f"{tickers}·{flow_type} (Retail)"
    else:
        # aggregate mode: omit tickers param entirely
        default_label = f"Aggregate Retail Flow ({flow_type})"
    try:
        r = requests.get(VT_BASE_TICKERS, params=params, timeout=60)
        r.raise_for_status()
        df = pd.DataFrame(r.json())
        if "date" not in df.columns:
            for c in ["time","timestamp","dt"]:
                if c in df.columns:
                    df = df.rename(columns={c:"date"})
                    break
        value_cols = [c for c in df.columns if c not in ["date","ticker","symbol","type"]]
        if not value_cols:
            return pd.DataFrame()
        out_label = label or default_label
        return df[["date", value_cols[0]]].rename(columns={value_cols[0]: out_label})
    except Exception:
        return _mock_ts(name=label or default_label)

def options_flow(tickers: Optional[str], metric: str="net", from_date: Optional[str]=None, to_date: Optional[str]=None, label: Optional[str]=None) -> pd.DataFrame:
    if not have_key():
        return _mock_ts(name=label or ("Aggregate Options Flow (net)" if not tickers else f"{tickers} options (mock)"))
    params = _build_params(metric, from_date, to_date)
    default_label = ""
    if tickers and tickers.strip():
        params["tickers"] = tickers.strip()
        default_label = f"{tickers}·{metric} (Options)"
    else:
        # aggregate mode
        default_label = f"Aggregate Options Flow ({metric})"
    try:
        r = requests.get(VT_BASE_OPTIONS, params=params, timeout=60)
        r.raise_for_status()
        df = pd.DataFrame(r.json())
        if "date" not in df.columns:
            for c in ["time","timestamp","dt"]:
                if c in df.columns:
                    df = df.rename(columns={c:"date"})
                    break
        value_cols = [c for c in df.columns if c not in ["date","ticker","symbol","type"]]
        if not value_cols:
            return pd.DataFrame()
        out_label = label or default_label
        return df[["date", value_cols[0]]].rename(columns={value_cols[0]: out_label})
    except Exception:
        return _mock_ts(name=label or default_label)