import pandas as pd
from typing import Literal
from rapidfuzz import process
from . import vanda_xasset_api as xa

def load_catalog_xasset() -> pd.DataFrame:
    fl = xa.filter_list()
    fm = xa.field_mappings()
    dfs = []
    if isinstance(fl, pd.DataFrame) and not fl.empty:
        fl["source"] = "VandaXAsset"
        dfs.append(fl)
    if isinstance(fm, pd.DataFrame) and not fm.empty:
        fm["source"] = "VandaXAsset"
        dfs.append(fm)
    if dfs:
        cat = pd.concat

def unified_search(keyword: str, source: Literal["All","VandaXAsset","VandaTrack"]="All") -> pd.DataFrame:
    keyword = (keyword or "").strip()
    frames = []
    if source in ["All","VandaXAsset"]:
        xcat = load_catalog_xasset()
        if not xcat.empty and keyword:
            mask = xcat.astype(str).apply(lambda c: c.str.contains(keyword, case=False, na=False))
            xcat = xcat.loc[mask.any(axis=1)]
        if not xcat.empty:
            frames.append(xcat)
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    keep = [c for c in ["series_id","description","asset","geography","sector","model_id","field_name","source"] if c in out.columns]
    if keep:
        out = out[keep + [c for c in out.columns if c not in keep]]
    return out