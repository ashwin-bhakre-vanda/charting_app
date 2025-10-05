import os
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import date

from modules import vanda_xasset_api as xa
from modules import vanda_track_api as vt
from modules.data_explorer import unified_search
from modules.chart_config import add_item, remove_item, clear_items, get_items
from modules.utils import outer_merge_on_date

st.set_page_config(page_title="Vanda Chart Studio (v6)", layout="wide")

# ---------- Sidebar: API Keys ----------
with st.sidebar:
    st.title("Vanda Chart Studio")
    st.caption("Enterprise — VandaXAsset + VandaTrack")

    with st.expander("🔐 API Credentials", expanded=False):
        xa_key = st.text_input("VandaXAsset API Key", type="password", value=os.getenv("VANDA_XASSET_API_KEY",""))
        if st.button("Save XAsset Key"):
            xa.set_key(xa_key)
            st.success("XAsset key saved for this session.")

        vt_key = st.text_input("VandaTrack API Key", type="password", value=os.getenv("VANDATRACK_API_KEY",""))
        if st.button("Save VandaTrack Key"):
            vt.set_key(vt_key)
            st.success("VandaTrack key saved for this session.")

    source_sel = st.radio("Search Source", ["All","VandaXAsset","VandaTrack"], horizontal=True)
    st.divider()

st.title("📊 Vanda Chart Studio — v6")
st.write("Full VandaXAsset advanced options + VandaTrack multi-series overlay.")

# ---------- Search & Add to Chart ----------
st.subheader("🔎 Data Explorer")
c1, c2 = st.columns([2,1])
with c1:
    kw = st.text_input("Search keyword (ticker, term, or model)", placeholder="e.g. AAPL, retail flow, positioning")
with c2:
    st.write(" "); st.write(" ")
    do_search = st.button("Search", type="primary")

if do_search and kw.strip():
    with st.spinner("Searching catalogs…"):
        res = unified_search(kw.strip(), source=source_sel)
    if res is None or res.empty:
        st.warning("No results. Try another term or change source.")
    else:
        st.caption("Results (click a row, then choose how to add):")
        st.dataframe(res.head(200), use_container_width=True)
        st.markdown("**Add selection to chart**")
        series_id = st.text_input("Series ID (from results)", value=res.iloc[0]["series_id"] if "series_id" in res.columns and not res.empty else "")
        api_source = st.selectbox("API Source", ["VandaXAsset","VandaTrack"])
        label = st.text_input("Display label (optional)", value=f"{series_id} ({api_source})")

        if api_source == "VandaXAsset":
            st.markdown("#### ⚙️ Advanced Options (XAsset)")

            freq_map = {
                "Daily": "daily", "Weekly": "weekly", "Monthly": "monthly", "Quarterly": "quarterly",
                "Day-over-Day (DoD)": "dod", "Week-over-Week (WoW)": "wow",
                "Month-over-Month (MoM)": "mom", "Year-over-Year (YoY)": "yoy"
            }
            freq_display = st.selectbox("Frequency", list(freq_map.keys()), index=0, key="fx1")
            freq = freq_map[freq_display]

            rolling_map = {"None": None, "1M": "1m", "3M": "3m", "6M": "6m", "12M": "12m"}
            rolling_display = st.selectbox("Rolling Sum", list(rolling_map.keys()), index=0, key="rs1")
            rolling_sum = rolling_map[rolling_display]

            z_map = {"Raw": None, "Z-Score All Years": "all", "Z-Score 2Y": "2y", "Z-Score 5Y": "5y"}
            z_display = st.selectbox("Type", list(z_map.keys()), index=0, key="zs1")
            z_score = z_map[z_display]

            # Auto-populate fields
            fields = xa.fields_for_series(series_id) or []
            if fields:
                field_name = st.selectbox("Field", fields, key="fld1")
            else:
                field_name = st.text_input("Field (manual)", key="fld1_txt")

            start = st.date_input("Start", value=date(2022,1,1))
            end = st.date_input("End", value=date.today())

            if st.button("➕ Add to Chart (XAsset)"):
                add_item({
                    "api": "xasset",
                    "series_id": series_id,
                    "field_name": field_name or None,
                    "from": str(start),
                    "to": str(end),
                    "label": label or None,
                    "frequency": freq,
                    "rolling_sum": rolling_sum,
                    "z_score": z_score
                })
                st.success(f"Added: {label}")

        else:  # VandaTrack
            vt_kind = st.selectbox("Endpoint", ["Retail","Options"])
            vt_type = st.selectbox("Metric", ["net","buy","sell"])
            start = st.date_input("Start", value=date(2022,1,1), key="vt_start")
            end = st.date_input("End", value=date.today(), key="vt_end")
            if st.button("➕ Add to Chart (VandaTrack)"):
                add_item({
                    "api": "track",
                    "endpoint": vt_kind.lower(),
                    "ticker": series_id,
                    "type": vt_type,
                    "from": str(start),
                    "to": str(end),
                    "label": label or None
                })
                st.success(f"Added: {label}")

# ---------- Quick Add by Series ID ----------
st.subheader("⚡ Quick Add by Series ID")
series_id_quick = st.text_input("Series ID / Ticker", placeholder="e.g. USEQCOMB or AAPL")
source_quick = st.selectbox("Source", ["VandaXAsset", "VandaTrack"])
label_quick = st.text_input("Label (optional)", value="")

if source_quick == "VandaXAsset":
    st.markdown("#### ⚙️ Advanced Options (XAsset)")
    freq_map = {
        "Daily": "daily", "Weekly": "weekly", "Monthly": "monthly", "Quarterly": "quarterly",
        "Day-over-Day (DoD)": "dod", "Week-over-Week (WoW)": "wow",
        "Month-over-Month (MoM)": "mom", "Year-over-Year (YoY)": "yoy"
    }
    freq_display = st.selectbox("Frequency", list(freq_map.keys()), index=0, key="fx2")
    freq = freq_map[freq_display]

    rolling_map = {"None": None, "1M": "1m", "3M": "3m", "6M": "6m", "12M": "12m"}
    rolling_display = st.selectbox("Rolling Sum", list(rolling_map.keys()), index=0, key="rs2")
    rolling_sum = rolling_map[rolling_display]

    z_map = {"Raw": None, "Z-Score All Years": "all", "Z-Score 2Y": "2y", "Z-Score 5Y": "5y"}
    z_display = st.selectbox("Type", list(z_map.keys()), index=0, key="zs2")
    z_score = z_map[z_display]

    fields = xa.fields_for_series(series_id_quick) if series_id_quick else []
    if fields:
        field_name_q = st.selectbox("Field", fields, key="fld2")
    else:
        field_name_q = st.text_input("Field (manual)", key="fld2_txt")

    start_q = st.date_input("Start", value=date(2022,1,1), key="q_start")
    end_q = st.date_input("End", value=date.today(), key="q_end")

    if st.button("➕ Add to Chart (Quick - XAsset)"):
        add_item({
            "api": "xasset",
            "series_id": series_id_quick,
            "field_name": field_name_q or None,
            "from": str(start_q),
            "to": str(end_q),
            "label": label_quick or f"{series_id_quick} (XAsset)",
            "frequency": freq,
            "rolling_sum": rolling_sum,
            "z_score": z_score
        })
        st.success(f"Added {series_id_quick or '(no id)'} (XAsset)")

else:  # VandaTrack
    vt_kind_q = st.selectbox("Endpoint", ["Retail", "Options"], key="vt_kind_q")
    vt_type_q = st.selectbox("Metric", ["net", "buy", "sell"], key="vt_type_q")
    start_q = st.date_input("Start", value=date(2022,1,1), key="vt_start_q")
    end_q = st.date_input("End", value=date.today(), key="vt_end_q")
    ticker_value = series_id_quick.strip()
    label_auto = f"Aggregate {vt_kind_q} Flow ({vt_type_q})" if ticker_value == "" else (label_quick or f"{ticker_value} ({vt_kind_q})")
    if st.button("➕ Add to Chart (Quick - VandaTrack)"):
        add_item({
            "api": "track",
            "endpoint": vt_kind_q.lower(),
            "ticker": ticker_value if ticker_value else None,
            "type": vt_type_q,
            "from": str(start_q),
            "to": str(end_q),
            "label": label_auto
        })
        st.success(f"Added {label_auto}")

# ---------- Chart Configuration Panel ----------
st.subheader("🧩 Chart Configuration")
items = get_items()
if not items:
    st.info("No series added yet. Use Search or Quick Add to add datasets.")
else:
    for idx, it in enumerate(items):
        cols = st.columns([6,3,1])
        with cols[0]:
            st.write(it)
        with cols[1]:
            st.write(" ")
        with cols[2]:
            if st.button("Remove", key=f"rm_{idx}"):
                remove_item(idx)
                st.experimental_rerun()
    if st.button("Clear All"):
        clear_items()
        st.experimental_rerun()

# ---------- Render Chart ----------
st.subheader("📈 Render Combined Chart")
normalize = st.checkbox("Normalize to Z-score per series (client-side)", value=False)
show_markers = st.checkbox("Show markers", value=False)

if st.button("Render Combined Chart", type="primary"):
    if not items:
        st.warning("Add at least one series first.")
    else:
        dfs = []
        for it in items:
            if it["api"] == "xasset":
                df = xa.timeseries(
                    series_id=it["series_id"],
                    field_name=it.get("field_name"),
                    start_date=it.get("from"),
                    end_date=it.get("to"),
                    label=it.get("label"),
                    frequency=it.get("frequency"),
                    rolling_sum=it.get("rolling_sum"),
                    z_score=it.get("z_score"),
                )
                dfs.append(df)
            else:
                if it.get("endpoint") == "retail":
                    df = vt.retail_flow(
                        tickers=it.get("ticker"),
                        flow_type=it.get("type","net"),
                        from_date=it.get("from"),
                        to_date=it.get("to"),
                        label=it.get("label")
                    )
                else:
                    df = vt.options_flow(
                        tickers=it.get("ticker"),
                        metric=it.get("type","net"),
                        from_date=it.get("from"),
                        to_date=it.get("to"),
                        label=it.get("label")
                    )
                dfs.append(df)

        merged = outer_merge_on_date(dfs)
        if merged is None or merged.empty:
            st.warning("No data to plot.")
        else:
            if "date" in merged.columns:
                merged["date"] = pd.to_datetime(merged["date"], errors="coerce")
                merged = merged.sort_values("date")

            if normalize:
                for c in merged.columns:
                    if c == "date": continue
                    s = merged[c]
                    if pd.api.types.is_numeric_dtype(s):
                        std = s.std(skipna=True)
                        merged[c] = (s - s.mean(skipna=True)) / (std if std else 1.0)

            value_cols = [c for c in merged.columns if c != "date"]
            m = merged.melt(id_vars=["date"], value_vars=value_cols, var_name="Series", value_name="Value")

            fig = px.line(m, x="date", y="Value", color="Series")
            if show_markers:
                fig.update_traces(mode="lines+markers")
            fig.update_layout(title="Combined Chart", legend_title="Series")
            st.plotly_chart(fig, use_container_width=True)

            st.download_button("Download CSV (merged)",
                               merged.to_csv(index=False).encode("utf-8"),
                               file_name="combined_data.csv", mime="text/csv")
            st.download_button("Download HTML chart",
                               fig.to_html(include_plotlyjs="cdn"),
                               file_name="combined_chart.html", mime="text/html")


# ---------- Spreadsheet mode ----------
st.markdown("---")
st.subheader("🗂️ Spreadsheet mode (optional)")
file = st.file_uploader("Upload CSV/XLSX", type=["csv","xlsx"])
if file:
    if file.name.endswith(".csv"):
        df_up = pd.read_csv(file)
    else:
        df_up = pd.read_excel(file)
    st.dataframe(df_up.head(100), use_container_width=True)
    cols = list(df_up.columns)
    if cols:
        x = st.selectbox("X-axis", cols, index=0, key="up_x")
        ycols = st.multiselect("Y-axis (multi)", [c for c in cols if c != x], key="up_y")
        if ycols and st.button("Plot Uploaded Data"):
            mm = df_up.melt(id_vars=[x], value_vars=ycols, var_name="Series", value_name="Value")
            fig2 = px.line(mm, x=x, y="Value", color="Series")
            st.plotly_chart(fig2, use_container_width=True)
