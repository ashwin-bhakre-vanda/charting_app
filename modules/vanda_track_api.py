import os
import pandas as pd
import numpy as np
import requests
from typing import Optional, Union, List, Dict

# === API Base URLs ===
VT_BASE_TICKERS = "https://www.vandatrack.com/tickers/api/"
VT_BASE_OPTIONS = "https://www.vandatrack.com/option/api/"

# === Global API Key Handling ===
_API_KEY = os.getenv("VANDATRACK_API_KEY", "")

def set_key(key: str):
    """Save API key for the session."""
    global _API_KEY
    _API_KEY = key
    os.environ["VANDATRACK_API_KEY"] = key

def have_key() -> bool:
    return bool(_API_KEY)

# === Helpers ===
def _mock_ts(n=250, name="mock_series"):
    rng = np.random.default_rng(42)
    idx = pd.date_range(end=pd.Timestamp.today().normalize(), periods=n, freq="D")
    return pd.DataFrame({"date": idx, name: rng.normal(0, 1, n).cumsum()})

def _build_params(base_params: Dict) -> Dict:
    """Attach auth and defaults."""
    p = base_params.copy()
    p.setdefault("auth_token", _API_KEY)
    p.setdefault("saved_list", "false")
    p.setdefault("pagination", "false")
    return p

# === RETAIL FLOW ===
def retail_flow(
    tickers: Optional[Union[str, List[str]]] = None,
    flow_type: str = "net",
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    label: Optional[str] = None
) -> pd.DataFrame:
    if not have_key():
        raise ValueError("No VandaTrack API key set. Please save it in the sidebar.")

    url = VT_BASE_TICKERS
    if isinstance(tickers, str):
        tickers = [tickers.strip()]
    elif tickers is None:
        tickers = []

    params_base = {
        "tickers": tickers,
        "saved_list": "false",
        "from_date": from_date or "2014-01-01",
        "to_date": to_date or pd.Timestamp.today().strftime("%Y-%m-%d"),
        "auth_token": _API_KEY,
    }

    flow_types = [flow_type] if flow_type in ["net", "buy", "sell"] else ["net", "buy", "sell"]
    flows = {}

    for ftype in flow_types:
        params = params_base.copy()
        params["type"] = ftype
        try:
            print(f"Calling VandaTrack with tickers={tickers}, type={ftype}")  # debug
            r = requests.get(url, params=params, timeout=60)
            r.raise_for_status()
            data = r.json()

            # Expect structure: { "NVDA": { "YYYY-MM-DD": value, ... } }
            if isinstance(data, dict):
                # Handle one ticker
                if len(data) == 1 and isinstance(next(iter(data.values())), dict):
                    tkr, series = next(iter(data.items()))
                    df = pd.DataFrame(
                        list(series.items()), columns=["date", ftype]
                    )
                    df["date"] = pd.to_datetime(df["date"], errors="coerce")
                    flows[ftype] = df
                    continue

                # Handle multiple tickers
                frames = []
                for tkr, series in data.items():
                    if isinstance(series, dict):
                        dft = pd.DataFrame(list(series.items()), columns=["date", ftype])
                        dft["ticker"] = tkr
                        frames.append(dft)
                if frames:
                    df = pd.concat(frames, ignore_index=True)
                    df["date"] = pd.to_datetime(df["date"], errors="coerce")
                    flows[ftype] = df
                    continue

            # fallback for list-based structure
            if isinstance(data, list) and data and isinstance(data[0], dict):
                df = pd.DataFrame(data)
                if "date" in df.columns:
                    df["date"] = pd.to_datetime(df["date"], errors="coerce")
                    df = df.rename(columns={"value": ftype})
                    flows[ftype] = df[["date", ftype]]

        except Exception as e:
            print(f"[WARN] retail_flow {ftype} failed: {e}")

    if not flows:
        return _mock_ts(name=label or f"{tickers or 'Aggregate'} (mock)")

    combined = None
    for ftype, df in flows.items():
        combined = df if combined is None else pd.merge(combined, df, on="date", how="outer")

    combined = combined.sort_values("date").reset_index(drop=True)
    label_prefix = label or (",".join(tickers) if tickers else "Aggregate Retail Flow")
    combined = combined.rename(columns={c: f"{label_prefix} {c}" for c in combined.columns if c != "date"})
    return combined



# === OPTIONS FLOW ===
def options_flow(
    tickers: Optional[Union[str, List[str]]] = None,
    callput: str = "put",
    moneyness: str = "OTM",
    size: str = "small",
    thematic_list: Optional[List[str]] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    label: Optional[str] = None
) -> pd.DataFrame:
    """
    Fetch options flow data (call/put, moneyness, size).
      - tickers: list or string (optional; omit for aggregate)
      - callput: 'call' or 'put'
      - moneyness: 'ITM', 'OTM', etc.
      - size: 'small', 'medium', 'large'
      - thematic_list: e.g. ['ADRs', 'All ETFs'] for aggregated option data
    """
    if not have_key():
        return _mock_ts(name=label or "Options Flow (mock)")

    params = _build_params({
        "from_date": from_date or "2014-01-01",
        "to_date": to_date or pd.Timestamp.today().strftime("%Y-%m-%d"),
        "callput": callput,
        "moneyness": moneyness,
        "size": size,
    })

    if thematic_list:
        params["thematic_list"] = thematic_list
        default_label = f"Aggregate Options Flow ({callput}, {moneyness}, {size})"
    elif tickers:
        if isinstance(tickers, str):
            tickers = [s.strip() for s in tickers.split(",") if s.strip()]
        params["tickers"] = tickers
        default_label = f"{','.join(tickers)} ({callput},{moneyness},{size}) (Options)"
    else:
        default_label = f"Aggregate Options Flow ({callput},{moneyness},{size})"

    try:
        r = requests.get(VT_BASE_OPTIONS, params=params, timeout=60)
        r.raise_for_status()
        data = r.json()

        # Empty or invalid response
        if not data or isinstance(data, (str, int, float)):
            raise ValueError(f"Empty or invalid response: {type(data)}")

        # Handle multi-ticker dicts
        if isinstance(data, dict):
            frames = []
            for tkr, values in data.items():
                if isinstance(values, list):
                    df_tkr = pd.DataFrame(values)
                elif isinstance(values, dict):
                    df_tkr = pd.DataFrame([values])
                else:
                    continue
                if not df_tkr.empty:
                    df_tkr["ticker"] = tkr
                    frames.append(df_tkr)
            df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            raise ValueError(f"Unexpected data type: {type(data)}")

        if df.empty:
            raise ValueError("Empty DataFrame after parsing")

        # Fix date column
        if "date" not in df.columns:
            for c in ["time", "timestamp", "dt"]:
                if c in df.columns:
                    df = df.rename(columns={c: "date"})
                    break

        if "date" not in df.columns:
            raise ValueError("No date column found in response")

        # Identify numeric value columns
        value_cols = [c for c in df.columns if c.lower() not in ["date", "ticker", "symbol", "type"]]
        if not value_cols:
            raise ValueError("No value columns found")

        col = value_cols[0]
        label_final = label or default_label
        df = df[["date", col]].rename(columns={col: label_final})
        return df

    except Exception as e:
        print(f"[WARN] options_flow failed: {e}")
        return _mock_ts(name=label or default_label)