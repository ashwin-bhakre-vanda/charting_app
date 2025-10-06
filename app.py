import os
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import date
import plotly.graph_objects as go

from modules import vanda_xasset_api as xa
from modules import vanda_track_api as vt
from modules.data_explorer import unified_search
from modules.chart_config import add_item, remove_item, clear_items, get_items
from modules.utils import outer_merge_on_date

st.set_page_config(page_title="Vanda Chart Studio (v6+)", layout="wide")

# ---------- Sidebar: API Keys ----------
with st.sidebar:
    st.title("Vanda Chart Studio")
    st.caption("Enterprise — VandaXAsset + VandaTrack")

    with st.expander("🔐 API Credentials", expanded=False):

        # --- XAsset Key ---
        xa_key = st.text_input("VandaXAsset API Key", type="password")
        if xa_key and "VANDA_XASSET_API_KEY" not in st.session_state:
            st.session_state["VANDA_XASSET_API_KEY"] = xa_key
            xa.set_key(xa_key)
            st.success("XAsset key saved for this session.")
        if "VANDA_XASSET_API_KEY" in st.session_state:
            xa.set_key(st.session_state["VANDA_XASSET_API_KEY"])

        st.divider()

        # --- VandaTrack Key ---
        vt_key = st.text_input("VandaTrack API Key", type="password")
        if vt_key and "VANDATRACK_API_KEY" not in st.session_state:
            st.session_state["VANDATRACK_API_KEY"] = vt_key
            vt.set_key(vt_key)
            st.success("VandaTrack key saved for this session.")
        if "VANDATRACK_API_KEY" in st.session_state:
            vt.set_key(st.session_state["VANDATRACK_API_KEY"])

st.title("📊 Vanda Chart Studio — v6+")
st.write("VandaXAsset advanced options + VandaTrack overlays, with mixed chart types, dual axes, and per-series colors.")

# ---------- Search & Add to Chart ----------
st.subheader("🔎 Data Explorer")
c1, c2 = st.columns([2, 1])
with c1:
    kw = st.text_input("Search keyword (ticker, term, or model)", placeholder="e.g. AAPL, retail flow, positioning")
with c2:
    st.write(" ")
    do_search = st.button("Search", type="primary")

source_sel = "All"
if do_search and kw.strip():
    with st.spinner("Searching catalogs…"):
        res = unified_search(kw.strip(), source=source_sel)
    if res is None or res.empty:
        st.warning("No results. Try another term or change source.")
    else:
        st.caption("Results (click a row, then choose how to add):")
        st.dataframe(res.head(200), use_container_width=True)
        st.markdown("**Add selection to chart**")
        series_id = st.text_input(
            "Series ID (from results)",
            value=res.iloc[0]["series_id"] if "series_id" in res.columns and not res.empty else ""
        )
        api_source = st.selectbox("API Source", ["VandaXAsset", "VandaTrack"])
        label = st.text_input("Display label (optional)", value=f"{series_id} ({api_source})")

        if api_source == "VandaXAsset":
            st.markdown("#### ⚙️ Advanced Options (XAsset)")
            freq_map = {
                "Daily": "daily", "Weekly": "weekly", "Monthly": "monthly", "Quarterly": "quarterly",
                "Day-over-Day (DoD)": "dod", "Week-over-Week (WoW)": "wow",
                "Month-over-Month (MoM)": "mom", "Year-over-Year (YoY)": "yoy"
            }
            freq_display = st.selectbox("Frequency", list(freq_map.keys()), index=0)
            freq = freq_map[freq_display]

            rolling_map = {"None": None, "1M": "1m", "3M": "3m", "6M": "6m", "12M": "12m"}
            rolling_display = st.selectbox("Rolling Sum", list(rolling_map.keys()), index=0)
            rolling_sum = rolling_map[rolling_display]

            z_map = {"Raw": None, "Z-Score All Years": "all", "Z-Score 2Y": "2y", "Z-Score 5Y": "5y"}
            z_display = st.selectbox("Type", list(z_map.keys()), index=0)
            z_score = z_map[z_display]

            fields = xa.fields_for_series(series_id) or []
            if fields:
                field_name = st.selectbox("Field", fields)
            else:
                field_name = st.text_input("Field (manual)")

            start = st.date_input("Start", value=date(2022, 1, 1))
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
                    "z_score": z_score,
                })
                st.success(f"Added: {label}")

        else:  # VandaTrack
            vt_kind = st.selectbox("Endpoint", ["Retail", "Options"])
            vt_type = st.selectbox("Metric", ["net", "buy", "sell"])
            start = st.date_input("Start", value=date(2022, 1, 1))
            end = st.date_input("End", value=date.today())
            if st.button("➕ Add to Chart (VandaTrack)"):
                add_item({
                    "api": "track",
                    "endpoint": vt_kind.lower(),
                    "ticker": series_id,
                    "type": vt_type,
                    "from": str(start),
                    "to": str(end),
                    "label": label or None,
                })
                st.success(f"Added: {label}")

# ---------- Quick Add by Series ID ----------
st.subheader("⚡ Quick Add by Series ID")
series_id_quick = st.text_input("Series ID / Ticker", placeholder="e.g. USEQCOMB or AAPL")
source_quick = st.selectbox("Source", ["VandaXAsset", "VandaTrack"])
label_quick = st.text_input("Label (optional)", value="")

if source_quick == "VandaXAsset":
    freq_map = {
        "Daily": "daily", "Weekly": "weekly", "Monthly": "monthly", "Quarterly": "quarterly",
        "Day-over-Day (DoD)": "dod", "Week-over-Week (WoW)": "wow",
        "Month-over-Month (MoM)": "mom", "Year-over-Year (YoY)": "yoy"
    }
    freq_display = st.selectbox("Frequency", list(freq_map.keys()), index=0)
    freq = freq_map[freq_display]

    rolling_map = {"None": None, "1M": "1m", "3M": "3m", "6M": "6m", "12M": "12m"}
    rolling_display = st.selectbox("Rolling Sum", list(rolling_map.keys()), index=0)
    rolling_sum = rolling_map[rolling_display]

    z_map = {"Raw": None, "Z-Score All Years": "all", "Z-Score 2Y": "2y", "Z-Score 5Y": "5y"}
    z_display = st.selectbox("Type", list(z_map.keys()), index=0)
    z_score = z_map[z_display]

    fields = xa.fields_for_series(series_id_quick) if series_id_quick else []
    if fields:
        field_name_q = st.selectbox("Field", fields)
    else:
        field_name_q = st.text_input("Field (manual)")

    start_q = st.date_input("Start", value=date(2022, 1, 1))
    end_q = st.date_input("End", value=date.today())

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
            "z_score": z_score,
        })
        st.success(f"Added {series_id_quick or '(no id)'} (XAsset)")

else:  # VandaTrack
    vt_kind_q = st.selectbox("Endpoint", ["Retail", "Options"])
    vt_type_q = st.selectbox("Metric", ["net", "buy", "sell"])
    start_q = st.date_input("Start", value=date(2022, 1, 1))
    end_q = st.date_input("End", value=date.today())
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
            "label": label_auto,
        })
        st.success(f"Added {label_auto}")

# ---------- Chart Configuration ----------
st.subheader("🧩 Chart Configuration")
items = get_items()
if not items:
    st.info("No series added yet. Use Search or Quick Add to add datasets.")
else:
    for idx, it in enumerate(items):
        cols = st.columns([6, 3, 1])
        with cols[0]:
            st.write(f"**{it.get('label','Unnamed')}**")
        with cols[1]:
            st.write(" ")
        with cols[2]:
            if st.button("Remove", key=f"rm_{idx}"):
                remove_item(idx)
    if st.button("Clear All"):
        clear_items()

# ---------- Render Combined Chart ----------
st.subheader("📈 Render Combined Chart")

# Initialize chart settings (type, axis, color)
if "chart_settings" not in st.session_state:
    st.session_state["chart_settings"] = {}

# Default color palette (fallbacks)
DEFAULT_COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
]

# Settings panel
if items:
    st.markdown("### 🎨 Chart Settings per Series")
    for i, it in enumerate(items):
        label = it.get("label", f"Series {i+1}")
        settings = st.session_state["chart_settings"].get(label, {"type": "Line", "axis": "Left", "color": DEFAULT_COLORS[i % len(DEFAULT_COLORS)]})

        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            new_type = st.selectbox(
                f"{label} display as:",
                ["Line", "Bar", "Scatter"],
                key=f"chart_type_{label}",
                index=["Line", "Bar", "Scatter"].index(settings["type"]),
            )
        with c2:
            new_axis = st.selectbox(
                "Y-axis", ["Left", "Right"],
                key=f"chart_axis_{label}",
                index=["Left", "Right"].index(settings["axis"]),
            )
        with c3:
            new_color = st.color_picker("Color", key=f"chart_color_{label}", value=settings["color"])

        st.session_state["chart_settings"][label] = {"type": new_type, "axis": new_axis, "color": new_color}

normalize = st.checkbox("Normalize to Z-score per series (client-side)", value=False)
show_markers = st.checkbox("Show markers on lines", value=False)

if st.button("Render Combined Chart", type="primary"):
    if not items:
        st.warning("Add at least one series first.")
    else:
        dfs = []
        for it in items:
            try:
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
                else:
                    if it.get("endpoint") == "retail":
                        df = vt.retail_flow(
                            tickers=it.get("ticker"),
                            flow_type=it.get("type", "net"),
                            from_date=it.get("from"),
                            to_date=it.get("to"),
                            label=it.get("label"),
                        )
                    else:
                        df = vt.options_flow(
                            tickers=it.get("ticker"),
                            callput=it.get("callput", "put"),
                            moneyness=it.get("moneyness", "OTM"),
                            size=it.get("size", "small"),
                            from_date=it.get("from"),
                            to_date=it.get("to"),
                            label=it.get("label"),
                        )
                dfs.append(df)
            except Exception as e:
                st.warning(f"Failed to fetch data for {it.get('label')}: {e}")

        merged = outer_merge_on_date(dfs)
        if merged is None or merged.empty:
            st.warning("No data to plot.")
        else:
            # ensure date col
            if "date" in merged.columns:
                merged["date"] = pd.to_datetime(merged["date"], errors="coerce")
            else:
                merged.rename(columns={merged.columns[0]: "date"}, inplace=True)
                merged["date"] = pd.to_datetime(merged["date"], errors="coerce")

            merged = merged.sort_values("date")

            # normalize if requested
            if normalize:
                for c in merged.columns:
                    if c == "date":
                        continue
                    s = merged[c]
                    if pd.api.types.is_numeric_dtype(s):
                        std = s.std(skipna=True)
                        merged[c] = (s - s.mean(skipna=True)) / (std if std else 1.0)

            # build figure
            fig = go.Figure()

            # add each series with its chart type / axis / color
            for col in [c for c in merged.columns if c != "date"]:
                settings = st.session_state["chart_settings"].get(col, None)
                if settings is None:
                    # fallback settings if not set (e.g., label mismatch)
                    idx = len(fig.data) % len(DEFAULT_COLORS)
                    settings = {"type": "Line", "axis": "Left", "color": DEFAULT_COLORS[idx]}

                chart_type = settings["type"].lower()
                axis_side = settings["axis"].lower()
                color = settings["color"]

                axis_ref = "y" if axis_side == "left" else "y2"

                if chart_type == "bar":
                    fig.add_trace(
                        go.Bar(x=merged["date"], y=merged[col], name=col, yaxis=axis_ref, marker_color=color)
                    )
                elif chart_type == "scatter":
                    fig.add_trace(
                        go.Scatter(x=merged["date"], y=merged[col],
                                   mode="markers", name=col, yaxis=axis_ref,
                                   marker=dict(color=color))
                    )
                else:  # line
                    mode = "lines+markers" if show_markers else "lines"
                    fig.add_trace(
                        go.Scatter(x=merged["date"], y=merged[col],
                                   mode=mode, name=col, yaxis=axis_ref,
                                   line=dict(color=color),
                                   marker=dict(color=color))
                    )

            # dual y-axes if any series is on right
            use_right = any(v.get("axis") == "Right" for v in st.session_state["chart_settings"].values())
            layout_args = dict(
                title="Combined Chart",
                legend_title="Series",
                xaxis_title="Date",
                yaxis_title="Left Axis",
                template="plotly_white",
                hovermode="x unified",
                height=650,
                barmode="group",
            )
            if use_right:
                layout_args["yaxis2"] = dict(
                    title="Right Axis",
                    overlaying="y",
                    side="right",
                    showgrid=False,
                )

            fig.update_layout(**layout_args)
            fig.update_traces(marker_line_width=0)

            st.plotly_chart(fig, use_container_width=True)

            st.download_button(
                "Download CSV (merged)",
                merged.to_csv(index=False).encode("utf-8"),
                file_name="combined_data.csv",
                mime="text/csv",
            )
            st.download_button(
                "Download HTML chart",
                fig.to_html(include_plotlyjs="cdn"),
                file_name="combined_chart.html",
                mime="text/html",
            )
