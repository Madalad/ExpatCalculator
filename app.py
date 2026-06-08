import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.script import TaxCalculator

st.set_page_config(page_title="ExpatCalculator", layout="wide")

CURRENCY_SYMBOLS = {"USD": "$", "GBP": "£"}
GREEN = "color: #2e7d32"
RED   = "color: #c62828"


@st.cache_resource
def get_calculator():
    return TaxCalculator()


@st.cache_data
def run_comparison(annual_income: float, currency: str, lifestyle: str):
    return get_calculator().compare_locations(annual_income, currency, lifestyle)


def color_columns(df, green_cols, red_cols):
    """Apply font colors to entire columns, skipping zeros."""
    styles = pd.DataFrame("", index=df.index, columns=df.columns)
    for col in green_cols:
        if col in df.columns:
            styles[col] = df[col].apply(lambda v: GREEN if v != 0 else "")
    for col in red_cols:
        if col in df.columns:
            styles[col] = df[col].apply(lambda v: RED if v != 0 else "")
    return styles


def bold_last_row(df):
    """Apply bold font to the last row (used for totals)."""
    styles = pd.DataFrame("", index=df.index, columns=df.columns)
    styles.iloc[-1] = "font-weight: bold"
    return styles


def color_rows(df, row_colors, value_cols=None):
    """Apply font colors per row to value_cols only; row_colors is aligned to df.index."""
    styles = pd.DataFrame("", index=df.index, columns=df.columns)
    target_cols = [c for c in (value_cols if value_cols is not None else df.columns) if c in df.columns]
    for i, color in enumerate(row_colors):
        if color:
            for col in target_cols:
                styles.at[df.index[i], col] = color
    return styles


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Settings")
    annual_income = st.number_input("Annual Income", min_value=0, value=100_000, step=5_000)
    currency = st.selectbox("Currency", ["USD", "GBP"])
    lifestyle = st.radio(
        "Lifestyle", ["low", "medium", "high"], index=1, format_func=str.capitalize
    )

sym = CURRENCY_SYMBOLS[currency]
input_to_usd = TaxCalculator.INPUT_CURRENCY_TO_USD[currency]
comparison = run_comparison(annual_income, currency, lifestyle)
money_fmt  = lambda x: f"{sym}{x:,.0f}"
abbrev_fmt = lambda x: f"{sym}{x/1000:.1f}k"

# ── Comparison DataFrame ──────────────────────────────────────────────────────

rows = []
for loc, data in comparison.items():
    rows.append({
        "Location":               loc.replace("_", " ").title(),
        "_key":                   loc,
        "Take-Home (Annual)":     data["take_home_input"],
        "Take-Home (Monthly)":    data["take_home_input"] / 12,
        "Cost of Living (Annual)":  data["col_annual_input"],
        "Cost of Living (Monthly)": data["col_monthly_input"],
        "Surplus (Annual)":       data["annual_surplus"],
        "Surplus (Monthly)":      data["monthly_surplus"],
        "Tax Rate":               data["tax_result"].effective_tax_rate,
        "Cap. Gains Rate":        data["capital_gains_rate"],
    })

df = (
    pd.DataFrame(rows)
    .sort_values("Take-Home (Annual)", ascending=False)
    .reset_index(drop=True)
)

OVERVIEW_GREEN = ["Take-Home (Annual)", "Take-Home (Monthly)", "Surplus (Annual)", "Surplus (Monthly)"]
OVERVIEW_RED   = ["Cost of Living (Annual)", "Cost of Living (Monthly)", "Tax Rate"]

# ── Page ──────────────────────────────────────────────────────────────────────

st.markdown("<style>h3 { text-align: center; }</style>", unsafe_allow_html=True)
st.title("ExpatCalculator")
st.caption(f"Income: {sym}{annual_income:,} {currency} | Lifestyle: {lifestyle.capitalize()}")

tab_overview, tab_detail = st.tabs(["Overview", "Location Detail"])

# ── Overview ──────────────────────────────────────────────────────────────────

with tab_overview:
    money_cols = [
        "Take-Home (Annual)", "Take-Home (Monthly)",
        "Cost of Living (Annual)", "Cost of Living (Monthly)",
        "Surplus (Annual)", "Surplus (Monthly)",
    ]
    display_df = df.drop(columns=["_key"]).copy()
    formatters = {col: money_fmt for col in money_cols}
    formatters["Tax Rate"]        = lambda x: f"{x * 100:.1f}%"
    formatters["Cap. Gains Rate"] = lambda x: f"{x * 100:.0f}%"

    st.dataframe(
        display_df.style
            .format(formatters)
            .apply(color_columns, green_cols=OVERVIEW_GREEN, red_cols=OVERVIEW_RED, axis=None),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Take-Home vs Cost of Living")
        locs     = df["Location"].tolist()
        th       = df["Take-Home (Annual)"].tolist()
        col_vals = df["Cost of Living (Annual)"].tolist()
        y_top    = max(max(th), max(col_vals)) * 1.18

        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            name="Take-Home", x=locs, y=th,
            marker_color="#66bb6a",
            text=[abbrev_fmt(v) for v in th],
            textposition="outside", textfont_size=11,
        ))
        fig1.add_trace(go.Bar(
            name="Cost of Living", x=locs, y=col_vals,
            marker_color="#ef5350",
            text=[abbrev_fmt(v) for v in col_vals],
            textposition="outside", textfont_size=11,
        ))
        fig1.update_layout(
            barmode="group",
            yaxis=dict(tickprefix=sym, tickformat=",.0f", range=[0, y_top]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(t=60, b=20, l=10, r=10),
        )
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        st.subheader("Annual Surplus")
        sorted_df = df.sort_values("Surplus (Annual)")
        locs_s = sorted_df["Location"].tolist()
        surp   = sorted_df["Surplus (Annual)"].tolist()
        y_pad  = (max(surp) - min(surp)) * 0.18
        y_rng  = [min(surp) - y_pad, max(surp) + y_pad]

        fig2 = go.Figure(go.Bar(
            x=locs_s, y=surp,
            marker_color=["#66bb6a" if v >= 0 else "#ef5350" for v in surp],
            text=[abbrev_fmt(v) for v in surp],
            textposition="outside", textfont_size=11,
        ))
        fig2.update_layout(
            yaxis=dict(tickprefix=sym, tickformat=",.0f", range=y_rng),
            margin=dict(t=40, b=20, l=10, r=10),
        )
        st.plotly_chart(fig2, use_container_width=True)

# ── Location Detail ───────────────────────────────────────────────────────────

with tab_detail:
    loc_display_to_key = {row["Location"]: row["_key"] for _, row in df.iterrows()}
    selected_display   = st.selectbox("Select Location", list(loc_display_to_key.keys()))
    selected_key       = loc_display_to_key[selected_display]

    data       = comparison[selected_key]
    tax        = data["tax_result"]
    col_result = data["col_result"]

    to_input     = 1 / (tax.exchange_rate_usd * input_to_usd)
    gross        = tax.gross_income         * to_input
    income_tax_v = tax.income_tax           * to_input
    social_v     = tax.social_contributions * to_input
    total_tax_v  = tax.total_tax            * to_input
    take_home_v  = tax.take_home_pay        * to_input
    col_annual   = col_result.annual_total  / input_to_usd
    col_monthly  = col_result.monthly_total / input_to_usd
    surplus_ann  = take_home_v - col_annual

    # ── Build tables ──────────────────────────────────────────────────────────
    tax_spec = [
        ("Gross Income",         money_fmt(gross),                           ""),
        ("Income Tax",           money_fmt(income_tax_v),                    RED if income_tax_v else ""),
        ("Social Contributions", money_fmt(social_v),                        RED if social_v else ""),
        ("Total Tax",            money_fmt(total_tax_v),                     RED if total_tax_v else ""),
        ("Effective Tax Rate",   f"{tax.effective_tax_rate * 100:.1f}%",     RED if tax.effective_tax_rate else ""),
        ("Cap. Gains Tax Rate",  f"{data['capital_gains_rate'] * 100:.0f}%", RED if data['capital_gains_rate'] else ""),
        ("Take-Home (Annual)",   money_fmt(take_home_v),                     GREEN if take_home_v else ""),
        ("Take-Home (Monthly)",  money_fmt(take_home_v / 12),                GREEN if take_home_v else ""),
    ]
    tax_df = pd.DataFrame({"Metric": [r[0] for r in tax_spec], "Value": [r[1] for r in tax_spec]})

    col_spec = [
        ("Housing",   col_result.housing   / input_to_usd, col_result.housing   / 12 / input_to_usd),
        ("Food",      col_result.food      / input_to_usd, col_result.food      / 12 / input_to_usd),
        ("Transport", col_result.transport / input_to_usd, col_result.transport / 12 / input_to_usd),
        ("Utilities", col_result.utilities / input_to_usd, col_result.utilities / 12 / input_to_usd),
        ("Other",     col_result.other     / input_to_usd, col_result.other     / 12 / input_to_usd),
        ("Total",     col_annual,                          col_monthly),
    ]
    col_df = pd.DataFrame({
        "Category": [r[0] for r in col_spec],
        "Annual":   [r[1] for r in col_spec],
        "Monthly":  [r[2] for r in col_spec],
    })
    col_row_colors = [RED if r[1] != 0 else "" for r in col_spec]

    # ── Surplus metrics ───────────────────────────────────────────────────────
    m1, m2 = st.columns(2)
    m1.metric("Annual Surplus", money_fmt(surplus_ann))
    m2.metric("Monthly Surplus", money_fmt(surplus_ann / 12))

    st.divider()

    # ── Breakdown tables side by side ─────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Tax Breakdown")
        st.dataframe(
            tax_df.style
                .apply(color_rows, row_colors=[r[2] for r in tax_spec], value_cols=["Value"], axis=None),
            use_container_width=True,
            hide_index=True,
        )

    with col_right:
        st.subheader("Cost of Living Breakdown")
        st.dataframe(
            col_df.style
                .format({"Annual": money_fmt, "Monthly": money_fmt})
                .apply(color_rows, row_colors=col_row_colors, value_cols=["Annual", "Monthly"], axis=None)
                .apply(bold_last_row, axis=None),
            use_container_width=True,
            hide_index=True,
        )
