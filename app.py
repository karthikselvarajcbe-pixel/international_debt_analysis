import streamlit as st
import pandas as pd
import plotly.express as px
from db import get_connection

st.set_page_config(layout="wide")

# ---------------- BACKGROUND ---------------- #
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
}
.stMetric {
    background: rgba(255,255,255,0.08);
    padding: 12px;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- DATABASE ---------------- #
def run_query(query):
    conn = get_connection()
    try:
        return pd.read_sql(query, conn)
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# ---------------- VISUAL ENGINE ---------------- #
def render_visual(qdf, query_name):

    if qdf.empty:
        st.warning("No data to visualize")
        return

    qdf = qdf.copy()

    # ✅ FIXED: safe numeric conversion
    for col in qdf.columns:
        try:
            qdf[col] = pd.to_numeric(qdf[col])
        except:
            pass

    num_cols = qdf.select_dtypes(include="number").columns.tolist()
    cat_cols = qdf.select_dtypes(exclude="number").columns.tolist()
    qname = query_name.lower()

    st.subheader("📊 Visualization")

    # ---------------- KPI (POWER BI CARD) ---------------- #
    if len(qdf) == 1 and len(num_cols) == 1:
        st.metric(label=qdf.columns[0], value=f"{qdf.iloc[0,0]:,.0f}")
        return

    # ---------------- MULTI KPI ---------------- #
    if len(qdf) == 1 and len(num_cols) > 1:
        cols = st.columns(len(num_cols))
        for i, col in enumerate(num_cols):
            cols[i].metric(col, f"{qdf.iloc[0][col]:,.0f}")
        return

    # ---------------- PIE (Contribution Queries) ---------------- #
    if ("percent" in qname or "contribution" in qname or "%" in qname):
        fig = px.pie(
            qdf,
            names=cat_cols[0],
            values=num_cols[0],
            hole=0.5,
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        st.plotly_chart(fig, use_container_width=True)
        return

    # ---------------- RANK / TOP ---------------- #
    if "top" in qname or "rank" in qname:
        fig = px.bar(
            qdf.sort_values(by=num_cols[0], ascending=True).head(10),
            x=num_cols[0],
            y=cat_cols[0],
            orientation="h",
            text_auto=True,
            color=num_cols[0],
            color_continuous_scale="viridis"
        )
        st.plotly_chart(fig, use_container_width=True)
        return

    # ---------------- CATEGORY ---------------- #
    if "category" in qname:
        fig = px.bar(
            qdf,
            x=cat_cols[0],
            y=num_cols[0],
            color=cat_cols[1],
            text_auto=True,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        st.plotly_chart(fig, use_container_width=True)
        return

    # ---------------- DISTRIBUTION ---------------- #
    if "min" in qname or "max" in qname or "avg" in qname:
        fig = px.bar(
            qdf.T,
            text_auto=True,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig, use_container_width=True)
        return

    # ---------------- TEXT ONLY ---------------- #
    if cat_cols and not num_cols:
        count_df = qdf[cat_cols[0]].value_counts().reset_index()
        count_df.columns = [cat_cols[0], "Count"]

        fig = px.bar(
            count_df,
            x=cat_cols[0],
            y="Count",
            text_auto=True,
            color="Count",
            color_continuous_scale="plasma"
        )
        st.plotly_chart(fig, use_container_width=True)
        return

    # ---------------- DEFAULT BAR ---------------- #
    fig = px.bar(
        qdf,
        x=cat_cols[0],
        y=num_cols[0],
        text_auto=True,
        color=num_cols[0],
        color_continuous_scale="rainbow"
    )
    st.plotly_chart(fig, use_container_width=True)


# ---------------- LOAD DATA ---------------- #
base_df = run_query("SELECT * FROM all_country")

YEAR = "2023"
if YEAR in base_df.columns:
    base_df[YEAR] = pd.to_numeric(base_df[YEAR], errors="coerce")

base_df = base_df.dropna(subset=[YEAR])

# ---------------- SIDEBAR ---------------- #
st.sidebar.title("🎛️ Filters")

country_filter = st.sidebar.multiselect(
    "Country", sorted(base_df["Country_Code"].dropna().unique())
)

indicator_filter = st.sidebar.multiselect(
    "Indicator", sorted(base_df["Series_Name"].dropna().unique())
)

df = base_df.copy()

if country_filter:
    df = df[df["Country_Code"].isin(country_filter)]

if indicator_filter:
    df = df[df["Series_Name"].isin(indicator_filter)]

# ---------------- TITLE ---------------- #
st.title("🌍 Global Debt Intelligence Dashboard")

# ---------------- KPI ---------------- #
total_debt = df[YEAR].sum()
avg_debt = df[YEAR].mean()
country_total = df.groupby("Country_Code")[YEAR].sum().reset_index()

top_country = country_total.sort_values(by=YEAR, ascending=False).iloc[0]

k1, k2, k3, k4 = st.columns(4)
k1.metric("🌍 Total Debt", f"{total_debt:,.0f}")
k2.metric("📊 Avg Debt", f"{avg_debt:,.0f}")
k3.metric("🏆 Top Country", top_country["Country_Code"])
k4.metric("💰 Top Value", f"{top_country[YEAR]:,.0f}")

# ---------------- TABS ---------------- #
tab1, tab2 = st.tabs(["📊 Dashboard", "🧠 Analysis"])

# ---------------- DASHBOARD ---------------- #
with tab1:

    top10 = country_total.sort_values(by=YEAR, ascending=False).head(10)

    st.plotly_chart(
        px.bar(top10, x="Country_Code", y=YEAR, color=YEAR, color_continuous_scale="viridis"),
        use_container_width=True
    )

    st.plotly_chart(
        px.pie(top10, names="Country_Code", values=YEAR, hole=0.5),
        use_container_width=True
    )

    indicator_df = df.groupby("Series_Name")[YEAR].sum().reset_index()

    st.plotly_chart(px.box(df, x="Series_Name", y=YEAR), use_container_width=True)

    st.plotly_chart(
        px.pie(indicator_df.head(10), names="Series_Name", values=YEAR, hole=0.5),
        use_container_width=True
    )

# ---------------- ANALYSIS ---------------- #
with tab2:

    st.subheader("🧾 Advanced Query Engine")

    queries = {
        "1. Distinct country names": "SELECT DISTINCT Long_Name FROM country_metadata;",
        "2. Total number of countries": "SELECT COUNT(*) AS total_countries FROM country_metadata;",
        "3. Total indicators": "SELECT COUNT(DISTINCT Series_Name) AS total_indicators FROM all_country;",
        "4. First 10 records": "SELECT * FROM all_country LIMIT 10;",
        "5. Total global debt": "SELECT SUM(`2023`) AS total_global_debt FROM all_country;",
        "6. Unique indicators": "SELECT DISTINCT Series_Name FROM all_country;",
        "7. Records per country": "SELECT Country_Code, COUNT(*) AS record_count FROM all_country GROUP BY Country_Code;",
        "8. Debt > 1B": "SELECT * FROM all_country WHERE `2023` > 1000000000;",
        "9. Min Max Avg": "SELECT MIN(`2023`) AS min_debt, MAX(`2023`) AS max_debt, AVG(`2023`) AS avg_debt FROM all_country;",
        "10. Total records": "SELECT COUNT(*) AS total_records FROM all_country;",
        "11. Total debt per country": "SELECT Country_Code, SUM(`2023`) AS total_debt FROM all_country GROUP BY Country_Code;",
        "12. Top 10 countries": "SELECT Country_Code, SUM(`2023`) AS total_debt FROM all_country GROUP BY Country_Code ORDER BY total_debt DESC LIMIT 10;",
        "13. Avg debt per country": "SELECT Country_Code, AVG(`2023`) AS avg_debt FROM all_country GROUP BY Country_Code;",
        "14. Debt per indicator": "SELECT Series_Name, SUM(`2023`) AS total_debt FROM all_country GROUP BY Series_Name;",
        "15. Highest indicator": "SELECT Series_Name, SUM(`2023`) AS total_debt FROM all_country GROUP BY Series_Name ORDER BY total_debt DESC LIMIT 1;",
        "16. Lowest country": "SELECT Country_Code, SUM(`2023`) AS total_debt FROM all_country GROUP BY Country_Code ORDER BY total_debt ASC LIMIT 1;",
        "17. Country + indicator": "SELECT Country_Code, Series_Name, SUM(`2023`) AS total_debt FROM all_country GROUP BY Country_Code, Series_Name;",
        "18. Indicator count": "SELECT Country_Code, COUNT(DISTINCT Series_Name) AS indicator_count FROM all_country GROUP BY Country_Code;",
        "19. Above global avg": "SELECT Country_Code, SUM(`2023`) AS total_debt FROM all_country GROUP BY Country_Code HAVING SUM(`2023`) > (SELECT AVG(total_debt) FROM (SELECT SUM(`2023`) AS total_debt FROM all_country GROUP BY Country_Code) x);",
        "20. Rank countries": "SELECT Country_Code, SUM(`2023`) AS total_debt, RANK() OVER (ORDER BY SUM(`2023`) DESC) AS rank_position FROM all_country GROUP BY Country_Code;",
        "21. Top indicators": "SELECT Series_Name, SUM(`2023`) AS total_debt FROM all_country GROUP BY Series_Name ORDER BY total_debt DESC LIMIT 5;",
        "22. % contribution": "SELECT Country_Code, SUM(`2023`) / (SELECT SUM(`2023`) FROM all_country) * 100 AS pct FROM all_country GROUP BY Country_Code;",
        "23. Top 3 per indicator": "SELECT * FROM (SELECT Series_Name, Country_Code, SUM(`2023`) AS total_debt, RANK() OVER (PARTITION BY Series_Name ORDER BY SUM(`2023`) DESC) AS rnk FROM all_country GROUP BY Series_Name, Country_Code) t WHERE rnk <= 3;",
        "24. Debt range": "SELECT Country_Code, MAX(`2023`) - MIN(`2023`) AS range_val FROM all_country GROUP BY Country_Code;",
        "25. Categorize debt": "SELECT Country_Code, SUM(`2023`) AS total_debt, CASE WHEN SUM(`2023`) > 1000000000 THEN 'High Debt' WHEN SUM(`2023`) > 100000000 THEN 'Medium Debt' ELSE 'Low Debt' END AS category FROM all_country GROUP BY Country_Code;",
        "26. Cumulative debt": "SELECT Country_Code, `2023`, SUM(`2023`) OVER (PARTITION BY Country_Code ORDER BY `2023`) AS cumulative_debt FROM all_country;",
        "27. Indicator above avg": "SELECT Series_Name, AVG(`2023`) AS avg_debt FROM all_country GROUP BY Series_Name HAVING avg_debt > (SELECT AVG(`2023`) FROM all_country);",
        "28. Countries >5%": "SELECT Country_Code, SUM(`2023`) AS total_debt FROM all_country GROUP BY Country_Code HAVING SUM(`2023`) > (SELECT SUM(`2023`) * 0.05 FROM all_country);",
        "29. Dominant indicator": "SELECT * FROM (SELECT Country_Code, Series_Name, SUM(`2023`) AS total_debt, RANK() OVER (PARTITION BY Country_Code ORDER BY SUM(`2023`) DESC) AS rnk FROM all_country GROUP BY Country_Code, Series_Name) t WHERE rnk = 1;",
        "30. Create view top 10": "SELECT Country_Code, SUM(`2023`) AS total_debt FROM all_country GROUP BY Country_Code ORDER BY total_debt DESC LIMIT 10;"
    }

    query_name = st.selectbox("Select Query", list(queries.keys()))

    if st.button("Run Query"):
        qdf = run_query(queries[query_name])
        st.dataframe(qdf, use_container_width=True)
        render_visual(qdf, query_name)