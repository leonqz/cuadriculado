import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Weekly Highlights", layout="wide")
st.title("📅 Weekly Highlights")


@st.cache_data
def load_data():
    df = pd.read_csv("data/privatelabel_all.csv")
    df.columns = [
        "Item", "Week", "Regular Price", "Special Price",
        "Units Sold Last Week", "Units Sold This Week",
        "Promo Spend", "Incremental Revenue", "Promo ROI"
    ]
    for col in ["Regular Price", "Special Price", "Promo Spend", "Incremental Revenue"]:
        df[col] = df[col].replace('[\$,]', '', regex=True).astype(float)
    return df

df = load_data()



# ========== Section 2: Private Label Promo Data ==========

# ========== TABS ==========
tab1, tab2 = st.tabs(["📆 Week Analysis", "📦 Item Analysis"])

# ========== TAB 1: Weekly Analysis ==========
with tab1:
    st.subheader("📆 Week-by-Week Performance")


    # Week selector
    selected_week = st.selectbox("📆 Select Week", sorted(df["Week"].unique()))
    week_df = df[df["Week"] == selected_week].copy()


    # Sort and slice
    # Choose and rename display columns with line breaks
    columns_to_keep = {
        "Item": "Item",
        "Regular Price": "Reg Price",
        "Special Price": "Special Price",
        "Units Sold Last Week": "Units Sold\nLast Week",
        "Units Sold This Week": "Units Sold\nThis Week",
        "Promo Spend": "Promo Spend",
        "Incremental Revenue": "Incremental Revenue",
        "Promo ROI": "ROI"
    }
    view_option = st.selectbox("📈 View", ["Top Performers", "Bottom Performers", "All"])


    # Let user choose sort column
    sort_metric = st.selectbox(
        "📊 Sort table by",
        options=["ROI", "Revenue $", "Profit $", "Spend $"],
        index=0
    )


    # Filter, sort, rename columns
    display_df = (
        week_df.sort_values("Promo ROI", ascending=(view_option == "Bottom Performers"))
        .head(10)
        .drop(columns=["Week"])
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
                "Incremental Revenue": "${:.0f}",
                "ROI": "{:.2f}"
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

    scatter = (
        alt.Chart(week_df)
        .mark_circle(size=100, opacity=0.7)
        .encode(
            x=alt.X("Incremental Revenue:Q", title="Revenue"),
            y=alt.Y("Profit:Q", title="Profit"),
            tooltip=["Item", "Incremental Revenue", "Profit", "Promo ROI"],
            color=alt.Color("Promo ROI:Q", scale=alt.Scale(scheme="redyellowgreen"))
        )
        .properties(height=420)
        .interactive()
    )

    st.altair_chart(scatter, use_container_width=True)

# ========== TAB 2: Item Analysis ==========
with tab2:
    st.subheader("📦 Item Performance Over Time")

    df["Revenue_Potential"] = df["Units Sold Last Week"] * df["Regular Price"]

    summary = df.groupby("Item").agg(
        Promo_Count=("Week", "count"),
        Avg_ROI=("Promo ROI", "mean"),
        Total_Revenue=("Incremental Revenue", "sum"),
        Avg_Revenue=("Incremental Revenue", "mean"),
        Avg_Spend=("Promo Spend", "mean"),
        Total_Revenue_Potential=("Revenue_Potential", "sum")
    
    ).reset_index()

    # Cap ROI values for color scaling
    summary["ROI_Capped"] = summary["Avg_ROI"].clip(lower=-1, upper=1.5)

        # Second scatterplot: Avg Revenue vs Avg Spend
    st.markdown("### 💵 Avg Revenue vs Avg Spend per Item")

    scatter2 = (
        alt.Chart(summary)
        .mark_circle(size=100, opacity=0.75)
        .encode(
            x=alt.X("Avg_Spend:Q", title="Average Promo Spend ($)"),
            y=alt.Y("Avg_Revenue:Q", title="Average Incremental Revenue ($)"),
            size=alt.Size("Total_Revenue_Potential:Q", scale=alt.Scale(range=[30, 400])),
            tooltip=["Item", "Avg_Spend", "Avg_Revenue", "Promo_Count", "Avg_ROI", "Total_Revenue_Potential"],
            color=alt.Color(
            "ROI_Capped:Q",
            scale=alt.Scale(scheme="redyellowgreen", domainMid=0),
            legend=alt.Legend(title="Average ROI")
    )
        )
        .properties(height=400)
        .interactive()
    )

    # ROI vs Promo Count scatter
    scatter3 = (
        alt.Chart(summary)
        .mark_circle(size=100, opacity=0.75)
        .encode(
            x=alt.X("Promo_Count:Q", title="Number of Promotions"),
            y=alt.Y("Avg_ROI:Q", title="Average ROI"),
            size=alt.Size("Total_Revenue_Potential:Q", scale=alt.Scale(range=[30, 400])),
            color=alt.Color(
                "ROI_Capped:Q",
                scale=alt.Scale(scheme="redyellowgreen", domainMid=0),
                legend=alt.Legend(title="Avg ROI (capped)")
            ),
            tooltip=["Item", "Promo_Count", "Avg_ROI", "Total_Revenue"]
        )
        .properties(height=400)
        .interactive()
    )
    
    st.markdown("### 📊 Item-Level ROI Analysis")

    col1, col2 = st.columns(2)

    with col1:
        st.altair_chart(scatter2, use_container_width=True)

    with col2:
        st.altair_chart(scatter3, use_container_width=True)



    st.markdown("### 📋 Historical Detail for a Selected Item")

    selected_item = st.selectbox("Select an Item", options=summary["Item"].unique())

    item_history = df[df["Item"] == selected_item].copy()
    item_history["Profit"] = item_history["Incremental Revenue"] - item_history["Promo Spend"]

    # Columns to show
    cols = [
        "Week",
        "Regular Price",
        "Special Price",
        "Promo Spend",
        "Incremental Revenue",
        "Profit",
        "Promo ROI"
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
        "Promo ROI": float(display_df["Promo ROI"].mean())
    }


    totals_df = pd.DataFrame([totals])

    # Combine item history + totals
    display_with_totals = pd.concat([display_df, totals_df], ignore_index=True)

    # Display with formatting
    st.dataframe(
        display_with_totals.style.format({
            "Regular Price": "${:.2f}",
            "Special Price": "${:.2f}",
            "Promo Spend": "${:,.0f}",
            "Incremental Revenue": "${:,.0f}",
            "Profit": "${:,.0f}",
            "Promo ROI": "{:.2f}"
        }),
        use_container_width=True
    )