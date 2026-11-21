"""
Global Sales Intelligence: interactive dashboard (Stage 4)
Run with:  streamlit run app.py
Needs global_superstore_clean.csv in the SAME folder as this file.

Business rules used everywhere (decided in Stages 2 and 3):
  - Orders are counted by UNIQUE Order ID, never by rows.
  - Return rate = returned unique orders / unique orders.
  - Profit margin = total Profit / total Sales of the group (not an average of row margins).
  - Negative profits and outliers are kept (they are real business results).
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------
# 1. PAGE SETUP
# ----------------------------------------------------------------------
st.set_page_config(page_title="Global Sales Intelligence", page_icon="📊", layout="wide")

DATA_FILE = Path(__file__).parent / "global_superstore_clean.csv"
REQUIRED = [
    "Order ID", "Order Date", "Ship Date", "Ship Mode", "Customer ID", "Customer Name",
    "Segment", "Country", "Country ISO3", "Market", "Region", "Category", "Sub-Category",
    "Product Name", "Sales", "Quantity", "Discount", "Profit", "Shipping Cost",
    "Order Priority", "Order Year", "Order Quarter", "Order Month", "Year-Month",
    "Shipping Days", "Is Loss", "Is Returned", "Person",
]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# ----------------------------------------------------------------------
# 2. LOAD DATA (cached so it is only read once)
# ----------------------------------------------------------------------
@st.cache_data(show_spinner="Loading data...")
def load_data(path):
    return pd.read_csv(path, parse_dates=["Order Date", "Ship Date"])


if not DATA_FILE.exists():
    st.error(f"Data file not found: **{DATA_FILE.name}**. "
             f"Put it in the same folder as app.py ({DATA_FILE.parent}).")
    st.stop()

data = load_data(DATA_FILE)
missing_cols = [c for c in REQUIRED if c not in data.columns]
if missing_cols:
    st.error(f"The CSV is missing these columns: {missing_cols}. "
             "Use the latest global_superstore_clean.csv downloaded from Colab (Cell 34).")
    st.stop()


# ----------------------------------------------------------------------
# 3. HELPER FUNCTIONS
# ----------------------------------------------------------------------
def summarise(d, by):
    """Sales, Profit, Quantity, unique Orders and Profit Margin % per group."""
    g = d.groupby(by).agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"),
                          Quantity=("Quantity", "sum"), Orders=("Order ID", "nunique"))
    g["Profit Margin %"] = np.where(g["Sales"] != 0, g["Profit"] / g["Sales"] * 100, np.nan)
    return g


def return_rate(d, by):
    """Return rate per group, using UNIQUE orders."""
    g = d.groupby(by).agg(Orders=("Order ID", "nunique"))
    returned = d[d["Is Returned"]].groupby(by)["Order ID"].nunique()
    g["Returned Orders"] = returned.reindex(g.index).fillna(0).astype(int)
    g["Return Rate %"] = g["Returned Orders"] / g["Orders"] * 100
    return g


def style(fig, title, height=420):
    fig.update_layout(title=title, template="plotly_white", height=height,
                      margin=dict(t=60, l=20, r=20, b=20), legend_title_text="")
    return fig


def table(df_, **kwargs):
    """Show a table with 2-decimal numbers."""
    st.dataframe(df_.round(2), width="stretch", **kwargs)


def money(x):
    return f"{x:,.0f}"


# ----------------------------------------------------------------------
# 4. SIDEBAR FILTERS
# ----------------------------------------------------------------------
st.sidebar.title("Filters")
st.sidebar.caption("All charts and numbers update to match these choices.")


def pick(label, column):
    options = sorted(data[column].dropna().unique().tolist())
    return st.sidebar.multiselect(label, options, default=options)


years = pick("Year", "Order Year")
markets = pick("Market", "Market")
categories = pick("Category", "Category")
segments = pick("Segment", "Segment")

country_pool = sorted(data.loc[data["Market"].isin(markets), "Country"].unique().tolist())
countries = st.sidebar.multiselect("Country (leave empty for all)", country_pool, default=[])

d_min, d_max = data["Order Date"].min().date(), data["Order Date"].max().date()
date_range = st.sidebar.date_input("Order date range", (d_min, d_max), min_value=d_min, max_value=d_max)

mask = (data["Order Year"].isin(years) & data["Market"].isin(markets)
        & data["Category"].isin(categories) & data["Segment"].isin(segments))
if countries:
    mask &= data["Country"].isin(countries)
if isinstance(date_range, tuple) and len(date_range) == 2:
    mask &= data["Order Date"].between(pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1]))
df = data[mask]

st.sidebar.divider()
st.sidebar.write(f"**{len(df):,}** order lines  \n**{df['Order ID'].nunique():,}** unique orders selected")
st.sidebar.download_button("Download filtered data (CSV)", df.to_csv(index=False).encode("utf-8"),
                           file_name="filtered_superstore.csv", mime="text/csv")

# ----------------------------------------------------------------------
# 5. HEADER AND KPIs
# ----------------------------------------------------------------------
st.title("Global Sales Intelligence")
st.caption("Global Superstore orders, 2011 to 2014. Margin = total profit / total sales. "
           "Orders and return rates are counted by unique order, not by row.")

if df.empty:
    st.warning("No data matches the current filters. Select at least one value in every filter.")
    st.stop()

n_orders = df["Order ID"].nunique()
sales, profit = df["Sales"].sum(), df["Profit"].sum()
returned_orders = df.loc[df["Is Returned"], "Order ID"].nunique()

k = st.columns(6)
k[0].metric("Total sales", money(sales))
k[1].metric("Total profit", money(profit))
k[2].metric("Profit margin", f"{profit / sales * 100:.2f}%" if sales else "n/a")
k[3].metric("Unique orders", f"{n_orders:,}")
k[4].metric("Avg order value", money(sales / n_orders))
k[5].metric("Return rate", f"{returned_orders / n_orders * 100:.2f}%")

tabs = st.tabs(["Overview", "Time", "Products", "Customers", "Geography",
                "Discounts", "Returns and shipping", "Forecast"])

# ----------------------------------------------------------------------
# TAB 1: OVERVIEW
# ----------------------------------------------------------------------
with tabs[0]:
    yearly = summarise(df, "Order Year")
    yearly["Sales Growth %"] = yearly["Sales"].pct_change() * 100
    yearly["Profit Growth %"] = yearly["Profit"].pct_change() * 100
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(yearly.reset_index(), x="Order Year", y=["Sales", "Profit"], barmode="group")
        fig.update_xaxes(type="category", title="Year")
        st.plotly_chart(style(fig, "Sales and profit by year"), width="stretch")
    with c2:
        mk = summarise(df, "Market").reset_index()
        fig = px.bar(mk, x="Market", y="Profit Margin %", color="Profit Margin %",
                     color_continuous_scale="RdYlGn", color_continuous_midpoint=0)
        st.plotly_chart(style(fig, "Profit margin % by market"), width="stretch")
    st.subheader("Yearly summary")
    table(yearly)
    st.caption("Growth % is blank for the first selected year, and compares neighbouring "
               "selected years only.")

# ----------------------------------------------------------------------
# TAB 2: TIME
# ----------------------------------------------------------------------
with tabs[1]:
    monthly = summarise(df, "Year-Month").reset_index()
    fig = px.line(monthly, x="Year-Month", y=["Sales", "Profit"], markers=True)
    fig.update_yaxes(title="Amount")
    st.plotly_chart(style(fig, "Monthly sales and profit"), width="stretch")

    c1, c2 = st.columns(2)
    with c1:
        seas = df.groupby(["Order Year", "Order Month"])["Sales"].sum().reset_index()
        fig = px.line(seas, x="Order Month", y="Sales", color=seas["Order Year"].astype(str), markers=True)
        fig.update_xaxes(tickmode="array", tickvals=list(range(1, 13)), ticktext=MONTHS, title="")
        st.plotly_chart(style(fig, "Monthly sales by year (seasonality)"), width="stretch")
    with c2:
        q = df.groupby(["Order Year", "Order Quarter"])["Sales"].sum().reset_index()
        q["Period"] = q["Order Year"].astype(str) + " Q" + q["Order Quarter"].astype(str)
        st.plotly_chart(style(px.bar(q, x="Period", y="Sales"), "Sales by quarter"),
                        width="stretch")

# ----------------------------------------------------------------------
# TAB 3: PRODUCTS
# ----------------------------------------------------------------------
with tabs[2]:
    c1, c2 = st.columns(2)
    with c1:
        cat = summarise(df, "Category").reset_index()
        fig = px.bar(cat, x="Category", y=["Sales", "Profit"], barmode="group")
        st.plotly_chart(style(fig, "Sales and profit by category"), width="stretch")
    with c2:
        sub = summarise(df, ["Category", "Sub-Category"]).reset_index().sort_values("Profit")
        fig = px.bar(sub, x="Profit", y="Sub-Category", color="Category", orientation="h")
        st.plotly_chart(style(fig, "Profit by sub-category (negative = loss)", 520),
                        width="stretch")

    fig = px.treemap(sub, path=["Category", "Sub-Category"], values="Sales",
                     color="Profit Margin %", color_continuous_scale="RdYlGn",
                     color_continuous_midpoint=0)
    st.plotly_chart(style(fig, "Sales by sub-category (colour = profit margin %)", 480),
                    width="stretch")

    st.subheader("Top and bottom products")
    n = st.slider("Number of products to show", 5, 25, 10)
    by = st.radio("Rank by", ["Profit", "Sales"], horizontal=True)
    prod = summarise(df, "Product Name").sort_values(by, ascending=False)
    c1, c2 = st.columns(2)
    c1.write(f"**Top {n} by {by.lower()}**")
    with c1:
        table(prod.head(n))
    c2.write(f"**Bottom {n} by {by.lower()}**")
    with c2:
        table(prod.tail(n).sort_values(by))

# ----------------------------------------------------------------------
# TAB 4: CUSTOMERS
# ----------------------------------------------------------------------
with tabs[3]:
    seg = summarise(df, "Segment")
    seg["Customers"] = df.groupby("Segment")["Customer ID"].nunique()
    seg["Avg Order Value"] = seg["Sales"] / seg["Orders"]
    c1, c2 = st.columns([1, 2])
    with c1:
        fig = px.pie(seg.reset_index(), names="Segment", values="Sales", hole=0.45)
        st.plotly_chart(style(fig, "Share of sales by segment", 360), width="stretch")
    with c2:
        st.write("**Segment summary**")
        table(seg)

    cust = df.groupby(["Customer ID", "Customer Name"]).agg(
        Sales=("Sales", "sum"), Profit=("Profit", "sum"), Orders=("Order ID", "nunique")).reset_index()
    cust["Profit Margin %"] = np.where(cust["Sales"] != 0, cust["Profit"] / cust["Sales"] * 100, np.nan)

    st.subheader("Customer rankings")
    metric = st.radio("Rank customers by", ["Sales", "Profit", "Orders"], horizontal=True)
    c1, c2 = st.columns(2)
    c1.write(f"**Top 10 by {metric.lower()}**")
    with c1:
        table(cust.sort_values(metric, ascending=False).head(10), hide_index=True)
    c2.write(f"**Bottom 10 by {metric.lower()}**")
    with c2:
        table(cust.sort_values(metric).head(10), hide_index=True)

    c1, c2 = st.columns(2)
    with c1:
        fig = px.histogram(cust, x="Orders", nbins=30)
        fig.update_layout(xaxis_title="Orders placed", yaxis_title="Customers")
        st.plotly_chart(style(fig, "Orders per customer"), width="stretch")
    with c2:
        cs = cust.sort_values("Sales", ascending=False)
        top_n = max(int(len(cs) * 0.10), 1)
        share = cs.head(top_n)["Sales"].sum() / cs["Sales"].sum() * 100
        st.metric("Sales share of top 10% of customers", f"{share:.1f}%")
        st.metric("Customers with a single order", f"{int((cust['Orders'] == 1).sum()):,} of {len(cust):,}")

# ----------------------------------------------------------------------
# TAB 5: GEOGRAPHY
# ----------------------------------------------------------------------
with tabs[4]:
    geo = summarise(df, ["Country", "Country ISO3"]).reset_index()
    metric = st.selectbox("Map shows", ["Sales", "Profit", "Profit Margin %", "Orders"], index=1)
    diverging = metric in ("Profit", "Profit Margin %")
    fig = px.choropleth(
        geo, locations="Country ISO3", color=metric, hover_name="Country",
        hover_data={"Country ISO3": False, "Sales": ":,.0f", "Profit": ":,.0f", "Orders": ":,"},
        color_continuous_scale="RdYlGn" if diverging else "Blues",
        color_continuous_midpoint=0 if diverging else None)
    st.plotly_chart(style(fig, f"{metric} by country", 520), width="stretch")

    c1, c2 = st.columns(2)
    with c1:
        st.write("**Top 10 countries by profit**")
        table(geo.set_index("Country").drop(columns="Country ISO3").sort_values("Profit", ascending=False).head(10))
    with c2:
        st.write("**10 countries with the lowest profit**")
        table(geo.set_index("Country").drop(columns="Country ISO3").sort_values("Profit").head(10))
    n_loss = int((geo["Profit"] < 0).sum())
    st.caption(f"{n_loss} of {len(geo)} selected countries have a total loss.")

    reg = summarise(df, "Region").reset_index().sort_values("Profit Margin %")
    fig = px.bar(reg, x="Profit Margin %", y="Region", orientation="h", color="Profit Margin %",
                 color_continuous_scale="RdYlGn", color_continuous_midpoint=0)
    st.plotly_chart(style(fig, "Profit margin % by region", 460), width="stretch")

# ----------------------------------------------------------------------
# TAB 6: DISCOUNTS
# ----------------------------------------------------------------------
with tabs[5]:
    bins = [-0.001, 0, 0.10, 0.20, 0.30, 0.40, 0.50, 1.0]
    labels = ["No discount", "0-10%", "10-20%", "20-30%", "30-40%", "40-50%", "Over 50%"]
    band = pd.cut(df["Discount"], bins=bins, labels=labels)
    disc = df.groupby(band, observed=True).agg(
        Order_Lines=("Order ID", "size"), Sales=("Sales", "sum"),
        Profit=("Profit", "sum"), Loss_Lines=("Is Loss", "sum"))
    disc["Profit Margin %"] = np.where(disc["Sales"] != 0, disc["Profit"] / disc["Sales"] * 100, np.nan)
    disc["% Lines Losing Money"] = disc["Loss_Lines"] / disc["Order_Lines"] * 100
    disc = disc.reset_index().rename(columns={"Discount": "Discount band"})

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(disc, x="Discount band", y="Profit Margin %", color="Profit Margin %",
                     color_continuous_scale="RdYlGn", color_continuous_midpoint=0)
        st.plotly_chart(style(fig, "Profit margin % by discount band"), width="stretch")
    with c2:
        fig = px.bar(disc, x="Discount band", y="% Lines Losing Money")
        st.plotly_chart(style(fig, "Share of order lines making a loss"), width="stretch")
    table(disc.drop(columns="Loss_Lines"), hide_index=True)
    st.caption("Bands exclude their lower edge and include their upper edge (10-20% = above 10% up to 20%). "
               "A link between discount and loss does not prove discounts cause the loss.")

    c1, c2 = st.columns(2)
    with c1:
        corr = df[["Sales", "Quantity", "Discount", "Profit", "Shipping Cost"]].corr()
        fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
        st.plotly_chart(style(fig, "Correlation (association only)", 440), width="stretch")
    with c2:
        sample = df.sample(min(5000, len(df)), random_state=42)
        fig = px.scatter(sample, x="Discount", y="Profit", color="Category", opacity=0.5)
        st.plotly_chart(style(fig, "Discount vs profit (random sample, max 5,000 lines)", 440),
                        width="stretch")

# ----------------------------------------------------------------------
# TAB 7: RETURNS AND SHIPPING
# ----------------------------------------------------------------------
with tabs[6]:
    st.subheader("Returns (by unique order)")
    dim = st.selectbox("Return rate by", ["Order Year", "Market", "Region", "Category",
                                          "Sub-Category", "Segment", "Ship Mode"], index=1)
    rr = return_rate(df, dim).reset_index().sort_values("Return Rate %", ascending=False)
    if dim == "Order Year":
        rr["Order Year"] = rr["Order Year"].astype(str)
    c1, c2 = st.columns([2, 1])
    with c1:
        fig = px.bar(rr, x="Return Rate %", y=dim, orientation="h")
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(style(fig, f"Return rate % by {dim.lower()}", 440), width="stretch")
    with c2:
        table(rr, hide_index=True)
    st.caption("The data does not say whether returned sales were refunded, so profit on returned "
               "orders may overstate real profit.")

    st.subheader("Shipping")
    ship = df.groupby("Ship Mode").agg(
        Order_Lines=("Order ID", "size"), Avg_Shipping_Days=("Shipping Days", "mean"),
        Avg_Shipping_Cost=("Shipping Cost", "mean"), Total_Shipping_Cost=("Shipping Cost", "sum"),
        Profit=("Profit", "sum")).reset_index()
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(ship, x="Ship Mode", y="Avg_Shipping_Days")
        fig.update_layout(yaxis_title="Average days")
        st.plotly_chart(style(fig, "Average shipping days by ship mode", 380), width="stretch")
    with c2:
        fig = px.box(df, x="Ship Mode", y="Shipping Cost")
        st.plotly_chart(style(fig, "Shipping cost by ship mode", 380), width="stretch")
    table(ship, hide_index=True)

    st.subheader("Regional managers")
    mgr = summarise(df, ["Person", "Region"]).join(return_rate(df, ["Person", "Region"])["Return Rate %"])
    fig = px.scatter(mgr.reset_index(), x="Sales", y="Profit Margin %", size="Orders",
                     color="Person", hover_name="Region")
    st.plotly_chart(style(fig, "Managers: sales vs profit margin % (bubble = orders)", 460),
                    width="stretch")
    table(mgr.sort_values("Sales", ascending=False))
    st.caption("Region EMEA is matched to the People sheet's AMEA (assumption made in Stage 2).")

# ----------------------------------------------------------------------
# TAB 8: FORECAST (reads the files created in Colab, Stage 5)
# ----------------------------------------------------------------------
with tabs[7]:
    BASE = Path(__file__).parent
    st.subheader("Sales forecast: total company, next 12 months")
    st.info("This tab always shows TOTAL company sales, so the sidebar filters do not change it. "
            "A forecast is an estimate that continues past patterns. It cannot know about price "
            "changes, competitors or the economy.")

    fc_file, hist_file = BASE / "forecast_next_12_months.csv", BASE / "monthly_history.csv"
    score_files = sorted(BASE.glob("forecast_backtest_score*.csv"))
    if not (fc_file.exists() and hist_file.exists()):
        st.warning("Forecast files not found. Put forecast_next_12_months.csv and monthly_history.csv "
                   "(created in Colab, Cell 40/42) in the same folder as app.py.")
    else:
        hist = pd.read_csv(hist_file, parse_dates=["Month"])
        fc = pd.read_csv(fc_file, parse_dates=["Month"])
        needed = {"Month", "Forecast", "Lower", "Upper"}
        if not needed.issubset(fc.columns) or not {"Month", "Sales"}.issubset(hist.columns):
            st.error("The forecast files do not have the expected columns. Re-run Colab Cell 40/42.")
        else:
            model_name = fc["Model"].iloc[0] if "Model" in fc.columns else "forecast model"
            has_alt = "Alt_Forecast" in fc.columns
            alt_name = fc["Alt_Model"].iloc[0] if "Alt_Model" in fc.columns else "second model"
            last12 = hist.tail(12)
            last12_total, fc_total = last12["Sales"].sum(), fc["Forecast"].sum()
            period = f"{fc['Month'].min():%b %Y} to {fc['Month'].max():%b %Y}"

            k = st.columns(4 if has_alt else 3)
            k[0].metric(f"Actual, {last12['Month'].min():%b %Y} to {last12['Month'].max():%b %Y}", money(last12_total))
            k[1].metric(f"Forecast, {period}", money(fc_total), f"{(fc_total / last12_total - 1) * 100:+.1f}% vs actual")
            k[2].metric("Main model", model_name)
            if has_alt:
                k[3].metric(f"Cross-check: {alt_name}", money(fc["Alt_Forecast"].sum()),
                            f"{(fc['Alt_Forecast'].sum() / last12_total - 1) * 100:+.1f}% vs actual")

            fig = go.Figure()
            fig.add_scatter(x=hist["Month"], y=hist["Sales"], name="Actual sales", line=dict(color="#1f77b4"))
            fig.add_scatter(x=fc["Month"], y=fc["Upper"], line=dict(width=0), showlegend=False, hoverinfo="skip")
            fig.add_scatter(x=fc["Month"], y=fc["Lower"], fill="tonexty", fillcolor="rgba(255,127,14,0.2)",
                            line=dict(width=0), name="Approximate range")
            fig.add_scatter(x=fc["Month"], y=fc["Forecast"], name=f"Forecast ({model_name})",
                            mode="lines+markers", line=dict(color="#ff7f0e"))
            if has_alt:
                fig.add_scatter(x=fc["Month"], y=fc["Alt_Forecast"], name=f"Cross-check ({alt_name})",
                                line=dict(color="#2ca02c", dash="dash"))
            fig.update_yaxes(title="Monthly sales")
            st.plotly_chart(style(fig, "Monthly sales: history and forecast", 480), width="stretch")
            st.caption("The range is approximate: forecast plus or minus 1.645 times the error seen in one "
                       "backtest year. It applies to single months, and it probably understates real uncertainty "
                       "because growth could change.")

            st.write("**Forecast by month**")
            show = fc.assign(Month=fc["Month"].dt.strftime("%Y-%m"))
            cols = ["Month", "Forecast", "Lower", "Upper"] + (["Alt_Forecast"] if has_alt else [])
            table(show[cols], hide_index=True)

            # ---- Growth what-if ----
            st.subheader("Growth what-if")
            yearly_h = hist.groupby(hist["Month"].dt.year)["Sales"].sum().to_frame("Sales")
            yearly_h["Growth %"] = yearly_h["Sales"].pct_change() * 100
            c1, c2 = st.columns([1, 2])
            with c1:
                st.write("**Actual yearly sales**")
                yearly_show = yearly_h.copy()
                yearly_show.index = yearly_show.index.astype(str)
                table(yearly_show)
            with c2:
                last_g = yearly_h["Growth %"].dropna().iloc[-1] if yearly_h["Growth %"].notna().any() else 0.0
                g = st.slider("Assumed sales growth for the next 12 months (%)", -20.0, 50.0,
                              float(round(last_g, 1)), 0.5)
                scen = last12["Sales"].values * (1 + g / 100)
                st.metric(f"Total sales at {g:+.1f}% growth", money(scen.sum()))
                comp = pd.DataFrame({"Month": fc["Month"].dt.strftime("%b"), "Last 12 months (actual)": last12["Sales"].values,
                                     "Scenario": scen}).melt("Month", var_name="Series", value_name="Sales")
                fig = px.bar(comp, x="Month", y="Sales", color="Series", barmode="group")
                st.plotly_chart(style(fig, "Scenario compared with the last 12 months", 340), width="stretch")
            st.caption("The scenario simply scales each of the last 12 months by the growth you choose. "
                       "The default is the most recent yearly growth.")

            # ---- Backtest scores ----
            if score_files:
                st.subheader("How accurate were the models?")
                scores_df = pd.read_csv(score_files[-1])
                table(scores_df, hide_index=True)
                st.caption("Backtest: the last 12 months were hidden, predicted, and compared with what happened. "
                           "Lower MAE, RMSE and MAPE is better. Total error % above 0 means over-predicted. "
                           "This uses one test year, so the ranking is only indicative.")
