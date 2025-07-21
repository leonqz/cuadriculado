import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Promo Insights",
    page_icon="📈",  # This can be an emoji or a custom image (see below)
    layout="wide"
)

st.title("📅 Weekly Highlights")


@st.cache_data
def load_data():
    df = pd.read_csv("data/promo_summary.csv")
    df.rename(columns={
        "Promo_Revenue": "Promo Revenue",
        "Incremental_Revenue": "Incremental Revenue",
        "Promo_Spend": "Promo Spend",
        "ROI": "ROI",
        "Promo_Units": "Units Sold This Period",
        "Baseline_Units": "Units Sold Last Period",
        "Regular_Price": "Regular Price",
        "Special_Price": "Special Price",
        "Promo_Start_Week": "Promo_Start_Week",
        "Item_Description": "Item"
    }, inplace=True)

    for col in ["Regular Price", "Special Price", "Promo Spend", "Incremental Revenue"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df

# ✅ Make sure this is executed before any tabs or UI use `df`
df = load_data()
# ========== Section 2: Private Label Promo Data ==========

# ========== TABS ==========
tab1, tab2 = st.tabs(["📆 Week Analysis", "📦 Item Analysis"])

# ========== TAB 1: Weekly Analysis ==========
with tab1:
    st.subheader("📆 Week-by-Week Performance")
    df["Promo Period"] = df["promo_period"].str.replace("_", "-")

    # Sort by Promo_Start_Week but display Promo Period
    sorted_periods = (
        df[["Promo Period", "Promo_Start_Week"]]
        .drop_duplicates()
        .sort_values("Promo_Start_Week")
    )["Promo Period"].tolist()


    # Week selector
    selected_week = st.selectbox("📆 Select Cuadriculado", sorted_periods)
    week_df = df[df["Promo Period"] == selected_week].copy()


    # Sort and slice
    # Choose and rename display columns with line breaks
    columns_to_keep = {
        "Item": "Item",
        "Regular Price": "Reg Price",
        "Special Price": "Special Price",
        "Units Sold Last Period": "Units Sold\nLast Period",
        "Units Sold This Period": "Units Sold\nThis Period",
        "Promo Spend": "Promo Spend",
        "Incremental Revenue": "Incremental Revenue",
        "ROI": "ROI",
        "Lift": "Lift",
        "Breakeven_Lift": "Breakeven Lift"

    }
    view_option = st.selectbox("📈 View", ["Top Performers", "Bottom Performers", "All"])


    # Let user choose sort column
    sort_metric = st.selectbox(
        "📊 Sort table by",
        options=["ROI", "Incremental Revenue", "Profit", "Promo Spend"],
        index=0
    )


    # Filter, sort, rename columns
    display_df = (
        week_df.sort_values("ROI", ascending=(view_option == "Bottom Performers"))
        .head(10)
        .drop(columns=["Promo_Start_Week"])
        .loc[:, list(columns_to_keep.keys())]
        .rename(columns=columns_to_keep)
    )

    # Apply sorting
    ascending = view_option == "Bottom Performers"
    display_df = display_df.sort_values(by=sort_metric, ascending=ascending)

    # Limit rows for Top/Bottom, keep all for "All"
    if view_option in ["Top Performers", "Bottom Performers"]:
        display_df = display_df.head(10)


    # Define ROI color function
    def color_roi(val):
        try:
            return "color: green" if val > 0 else "color: red"
        except:
            return ""

    # Show table
    st.markdown(f"### {'🔝' if view_option == 'Top Performers' else '🔻'} {view_option} (Week {selected_week})")
    st.dataframe(
        display_df.style
            .format({
                "Reg Price": "${:.2f}",
                "Special Price": "${:.2f}",
                "Promo Spend": "${:.0f}",
                "Units Sold\nLast Period": "{:.0f}",
                "Units Sold\nThis Period": "{:.0f}",
                "Incremental Revenue": "${:.0f}",
                "ROI": "{:.2f}",
                "Lift": "{:.1f}",
                "Breakeven Lift": "{:.1f}"

            })
            .map(color_roi, subset=["ROI"]),
        use_container_width=False
    )

    # Download CSV
    @st.cache_data
    def convert_df_to_csv(df):
        return df.to_csv(index=False).encode("utf-8")

    csv_data = convert_df_to_csv(display_df)
    # Revenue vs Profit scatterplot
    st.markdown("### 💰 Revenue vs Profit (This Week)")

    week_df["Profit"] = week_df["Incremental Revenue"] - week_df["Promo Spend"]
    week_df["Total_Revenue"] = week_df["Units Sold This Period"] * week_df["Regular Price"]

    x_min, x_max = week_df["Incremental Revenue"].min(), week_df["Incremental Revenue"].max()
    y_min, y_max = week_df["Profit"].min(), week_df["Profit"].max()

    scatter = (
        alt.Chart(week_df)
        .mark_circle(opacity=0.7)
        .encode(
            x=alt.X("Incremental Revenue:Q", scale=alt.Scale(domain=[x_min, x_max]), title="Revenue"),
            y=alt.Y("Profit:Q", scale=alt.Scale(domain=[y_min, y_max]), title="Profit"),
            size=alt.Size("Total_Revenue:Q", scale=alt.Scale(range=[30, 400]), title="Total Revenue ($)"),
            color=alt.Color("ROI:Q", scale=alt.Scale(scheme="redyellowgreen"), title="ROI"),
            tooltip=["Item", "Incremental Revenue", "Profit", "ROI", "Total_Revenue"]
        )
        .properties(height=420)
        .interactive()
    )

    st.altair_chart(scatter, use_container_width=True)

# ========== TAB 2: Item Analysis ==========
with tab2:
    # One subheader for the full section
    st.subheader("📦 Item Performance Over Time")

    # Compute features and build summary as before
    df["Revenue_Potential"] = df["Units Sold Last Period"] * df["Regular Price"]

    summary = df.groupby("Item").agg(
        Promo_Count=("Promo Period", "count"),
        Avg_ROI=("ROI", "mean"),
        Total_Revenue=("Incremental Revenue", "sum"),
        Avg_Revenue=("Incremental Revenue", "mean"),
        Avg_Spend=("Promo Spend", "mean"),
        Total_Revenue_Potential=("Revenue_Potential", "sum")
    ).reset_index()

    summary["ROI_Capped"] = summary["Avg_ROI"].clip(lower=-1, upper=1.5)

    # Layout: 2 columns
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 💵 Avg Revenue vs Avg Promo Spend per Item")
        scatter2 = (
            alt.Chart(summary)
            .mark_circle(size=100, opacity=0.75)
            .encode(
                x=alt.X("Avg_Spend:Q", title="Average Promo Spend ($)"),
                y=alt.Y("Avg_Revenue:Q", title="Average Incremental Revenue ($)"),
                size=alt.Size("Total_Revenue_Potential:Q", scale=alt.Scale(range=[30, 400])),
                color=alt.Color("ROI_Capped:Q", scale=alt.Scale(scheme="redyellowgreen", domainMid=0),
                                legend=alt.Legend(title="Average ROI")),
                tooltip=["Item", "Avg_Spend", "Avg_Revenue", "Promo_Count", "Avg_ROI", "Total_Revenue_Potential"]
            )
            .properties(height=400)
            .interactive()
        )
        st.altair_chart(scatter2, use_container_width=True)

    with col2:
        st.markdown("### 📈 ROI vs Number of Promotions")
        scatter3 = (
            alt.Chart(summary)
            .mark_circle(size=100, opacity=0.75)
            .encode(
                x=alt.X("Promo_Count:Q", title="Number of Promotions"),
                y=alt.Y("Avg_ROI:Q", title="Average ROI"),
                size=alt.Size("Total_Revenue_Potential:Q", scale=alt.Scale(range=[30, 400])),
                color=alt.Color("ROI_Capped:Q", scale=alt.Scale(scheme="redyellowgreen", domainMid=0),
                                legend=alt.Legend(title="Avg ROI (capped)")),
                tooltip=["Item", "Promo_Count", "Avg_ROI", "Total_Revenue"]
            )
            .properties(height=400)
            .interactive()
        )
        st.altair_chart(scatter3, use_container_width=True)




    st.markdown("### 📋 Historical Detail for a Selected Item")

    selected_item = st.selectbox("Select an Item", options=summary["Item"].unique())

    item_history = df[df["Item"] == selected_item].copy()
    item_history["Profit"] = item_history["Incremental Revenue"] - item_history["Promo Spend"]

    # Columns to show
    cols = [
        "Promo Period",
        "Regular Price",
        "Special Price",
        "Promo Spend",
        "Incremental Revenue",
        "Profit",
        "ROI"
    ]

    display_df = item_history[cols].copy()

    # Make sure numeric total values are floats (some may get inferred as strings)
    totals = {
        "Week": "TOTAL",
        "Regular Price": None,
        "Special Price": None,
        "Promo Spend": float(display_df["Promo Spend"].sum()),
        "Incremental Revenue": float(display_df["Incremental Revenue"].sum()),
        "Profit": float(display_df["Profit"].sum()),
        "ROI": float(display_df["ROI"].mean())
    }


    totals_df = pd.DataFrame([totals])

    # Combine item history + totals
    display_with_totals = pd.concat([display_df, totals_df], ignore_index=True)

        # Calculate recommendation
    num_promos = len(item_history)
    avg_roi = totals["ROI"]

    if num_promos >= 3 and avg_roi >= 0.5:
        recommendation = "✅ Run another promo — consider a deeper discount."
    elif num_promos < 3 and avg_roi >= 0.5:
        recommendation = "📈 High potential — test another promotion soon."
    elif num_promos < 3 and avg_roi < 0.5:
        recommendation = "⚠️ Be cautious — early signs of low ROI."
    else:  # num_promos >= 3 and avg_roi < 0.5
        recommendation = "🚫 Avoid promoting again — consistently low ROI."

    # Display recommendation above the table
    st.markdown(f"### 🤖 Recommendation for **{selected_item}**")
    st.info(recommendation)

    # Display with formatting
    st.dataframe(
        display_with_totals.style.format({
            "Regular Price": "${:.2f}",
            "Special Price": "${:.2f}",
            "Promo Spend": "${:,.0f}",
            "Incremental Revenue": "${:,.0f}",
            "Profit": "${:,.0f}",
            "ROI": "{:.2f}"
        }),
        use_container_width=True
    )