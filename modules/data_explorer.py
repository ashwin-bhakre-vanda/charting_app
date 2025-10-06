import pandas as pd
from typing import Literal
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
        cat = pd.concat(dfs, ignore_index=True)
        if "series_id" not in cat.columns:
            for c in ["_id", "timeseries_id", "series", "id"]:
                if c in cat.columns:
                    cat = cat.rename(columns={c: "series_id"})
                    break
        return cat
    return pd.DataFrame()

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
    return pd.concat(frames, ignore_index=True)
