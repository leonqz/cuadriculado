import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="BetterBasket - Shopper",
    page_icon="data/betterbasket_icon_blue.png",
    layout="wide"
)

st.image("data/econo_logo.png", width=400)
st.title("Econo HQ Cuadriculado Dashboard")

st.markdown("#### Showing data for:")

# Define columns with tight spacing
col1, col2, col3 = st.columns([1, 1, 1])

# Multi-select using checkboxes styled like buttons
with col1:
    jc_selected = st.checkbox("All (Juancarlos)", value=True)
with col2:
    enid_selected = st.checkbox("Juancarlos", value=True)
with col3:
    coming_soon = st.checkbox("Enid (Coming Soon)", value=False, disabled=True)

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

def load_weekly_data():
    df = pd.read_csv("data/weekly_df.csv")
    return df

weekly_df = load_weekly_data()

# Sidebar glossary
# Sidebar glossary
st.sidebar.markdown("### 📘 Need help? Metric Glossary")
st.sidebar.markdown("""
**Promo Spend**  
💸 The total cost of offering the discount (i.e., the discount per unit × units sold).

**Added / Incremental Revenue**  
📈 The extra revenue generated during the promotion compared to the prior period.

**ROI (Return on Investment)**  
📊 Measures efficiency: incremental revenue ÷ promo spend.

**Breakeven Lift**  
⚖️ The unit sales increase needed during the promo to make the same profit as before.

**Lift**  
🚀 The multiple of unit sales this promo achieved vs. the previous non-promo period.

**Lift Delta**  
📉 The difference between actual lift and breakeven lift — positive = exceeded breakeven.
""")

# ✅ Make sure this is executed before any tabs or UI use `df`
df = load_data()
# ========== Section 2: Private Label Promo Data ==========

# ========== TABS ==========
tab1, tab2 = st.tabs(["📆 Week Analysis", "📦 Item Analysis"])

# ========== TAB 1: Weekly Analysis ==========
with tab1:
    st.subheader("📆 Week-by-Week Performance")
    df["Promo Period"] = df["promo_period"].str.replace("_", "-")
    df["Lift Delta"] = df["Lift"] - df["Breakeven_Lift"]

    # Sort by Promo_Start_Week but display Promo Period
    sorted_periods = (
        df[["Promo Period", "Promo_Start_Week"]]
        .drop_duplicates()
        .sort_values("Promo_Start_Week")
    )["Promo Period"].tolist()


    # Create 3 columns side by side
    col1, col2, col3 = st.columns(3)

    # Place each selectbox inside one of the columns
    with col1:
        selected_week = st.selectbox("📆 Select Cuadriculado", sorted_periods)
        week_df = df[df["Promo Period"] == selected_week].copy()


    with col2:
        sort_metric = st.selectbox(
            "📊 Sort table by",
            options=["ROI", "Lift Delta", "Lift", "Incremental Revenue", "Promo Spend"],
            index=0
        )

    with col3:
        view_option = st.selectbox("📈 View", ["Top Performers", "Bottom Performers", "All"])



    # First calculate weighted margin % per item
    week_df["Margin %"] = (
        (week_df["Units Sold This Period"] * (week_df["Special Price"] - week_df["Unit_Cost"])) /
        (week_df["Units Sold This Period"] * week_df["Special Price"])
    ).fillna(0)

    # Then calculate the weighted average margin across all promos
    weighted_margin_pct = (
        (week_df["Margin %"] * week_df["Units Sold This Period"] * week_df["Special Price"]).sum()
        / (week_df["Units Sold This Period"] * week_df["Special Price"]).sum()   
    )

        # Calculate overall metrics
    total_units = week_df["Units Sold This Period"].sum()
    total_profit = ((week_df["Special Price"] - week_df["Unit_Cost"]) * week_df["Units Sold This Period"]).sum()

    total_lift = week_df["Lift"].mean()
    total_spend = week_df["Promo Spend"].sum()
    overall_roi = week_df["ROI"].mean()


        # Define item segments
    star_items = week_df[(week_df["ROI"] > 1.2) & (week_df["Lift"] > 1.5)]
    risk_items = week_df[(week_df["ROI"] < 0.5) & (week_df["Lift"] < 1)]
    tradeoff_items = week_df[(week_df["ROI"] < 1) & (week_df["Lift"] > 1.5)]
    sleeper_items = week_df[(week_df["ROI"] > 1) & (week_df["Lift"] < 1)]

    # Choose examples
    star = star_items.sort_values("ROI", ascending=False).head(1)
    risk = risk_items.sort_values("ROI").head(1)
    tradeoff = tradeoff_items.sort_values("Lift").head(1)
    sleeper = sleeper_items.sort_values("ROI").head(1)


    # Sort and slice
    # Choose and rename display columns with line breaks
    columns_to_keep = {
        "Item": "Item",
        "Regular Price": "Reg Price",
        "Special Price": "Special Price",
        "Unit_Cost": "Unit Cost",
        "Margin %": "Margin %",
        "Units Sold Last Period": "Units Sold\nLast Period",
        "Units Sold This Period": "Units Sold\nThis Period",
        "Promo Spend": "Promo Spend",
        "Incremental Revenue": "Incremental Revenue",
        "ROI": "ROI",
        "Lift": "Lift",
        "Breakeven_Lift": "Breakeven Lift",
        "Lift Delta": "Lift Delta"
    }




    # Thresholds for commentary
    high_margin = weighted_margin_pct > 0.2
    strong_lift = total_lift > 1.5
    efficient_spend = overall_roi > 1

    # Conversational summary
    st.markdown("### 📊 Weekly Summary Overview")

    summary_text = f"""
    This week, the average margin across all promoted items was **{weighted_margin_pct:.1%}** — {"a healthy profit margin" if high_margin else "on the lower side, so something to watch"}. The average **unit sales lift** was **{total_lift:.2f}**, meaning sales were {"stronger than usual" if strong_lift else "relatively flat"} during promotions. We spent a total of **${total_spend:,.0f}** on promotions, and the average **ROI** came out to **{overall_roi:.2f}**, which is {"a solid return" if efficient_spend else "below breakeven — there may be room to optimize"}.
    """

    st.markdown(summary_text)

    if not star.empty:
        s = star.iloc[0]
        st.success(
            f"⭐ **Star Item:** {s['Item']} had an ROI of {s['ROI']:.2f}, lift of {s['Lift']:.2f}, and margin of {s['Margin %']:.1%} — a highly effective promotion."
        )

    if not risk.empty:
        r = risk.iloc[0]
        st.warning(
            f"⚠️ **Risk Item:** {r['Item']} underperformed with an ROI of {r['ROI']:.2f} and lift of {r['Lift']:.2f}, suggesting the promo cost more than it delivered."
        )



        # Download CSV
    @st.cache_data
    def convert_df_to_csv(df):
        return df.to_csv(index=False).encode("utf-8")


    def remove_outliers(df, col):
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        return df[(df[col] >= lower) & (df[col] <= upper)]



    # Thresholds
    roi_threshold = 1.0
    lift_threshold = 1.5




    # Calculate Lift (already assumed present in week_df)
    week_df["Lift"] = week_df["Units Sold This Period"] / week_df["Units Sold Last Period"]
    week_df["Profit"] = week_df["Incremental Revenue"] - week_df["Promo Spend"]
    week_df["Total_Revenue"] = week_df["Units Sold This Period"] * week_df["Regular Price"]

    # Apply to both ROI and Lift
    filtered_df = remove_outliers(week_df, "ROI")
    filtered_df = remove_outliers(filtered_df, "Lift")


    # Compute min/max to include thresholds
    x_min = min(filtered_df["ROI"].min(), roi_threshold * 0.95)
    x_max = max(filtered_df["ROI"].max(), roi_threshold * 1.05)
    y_min = min(filtered_df["Lift"].min(), lift_threshold * 0.95)
    y_max = max(filtered_df["Lift"].max(), lift_threshold * 1.05)

    # Main scatter chart
    scatter = alt.Chart(filtered_df).mark_circle(size=100, opacity=0.75).encode(
        x=alt.X("ROI:Q", title="Promo ROI", scale=alt.Scale(domain=[x_min, x_max])),
        y=alt.Y("Lift:Q", title="Unit Sales Lift", scale=alt.Scale(domain=[y_min, y_max])),
        size=alt.Size("Total_Revenue:Q", scale=alt.Scale(range=[30, 400]), title="Total Revenue"),
        color=alt.Color("Profit:Q", scale=alt.Scale(scheme="redyellowgreen"), title="Profit"),
        tooltip=["Item", "ROI", "Lift", "Incremental Revenue", "Promo Spend", "Profit"]
    )

    # Vertical guide (ROI threshold)
    vline = alt.Chart(pd.DataFrame({"x": [roi_threshold]})).mark_rule(
        color="#FFD700", strokeDash=[4, 4], strokeWidth=2
    ).encode(x="x:Q")

    # Horizontal guide (Lift threshold)
    hline = alt.Chart(pd.DataFrame({"y": [lift_threshold]})).mark_rule(
        color="#FFD700", strokeDash=[4, 4], strokeWidth=2
    ).encode(y="y:Q")


    # Add some padding
    pad_x = (x_max - x_min) * 0.05
    pad_y = (y_max - y_min) * 0.05

        # Corner labels
    annotations = pd.DataFrame({
        "x": [x_max - pad_x, x_min + pad_x, x_max - pad_x, x_min + pad_x],
        "y": [y_max - pad_y, y_max - pad_y, y_min + pad_y, y_min + pad_y],
        "label": [
            "✅ STAR: Efficient and high lift promo",
            "⚠️ TRADEOFF: High lift but costly promo",
            "🤔 SLEEPER: Efficient, but low lift",
            "🚫 RISK: Promo likely failed"
        ],
        "align": ["right", "left", "right", "left"],
        "baseline": ["top", "top", "bottom", "bottom"]
    })

    labels = alt.Chart(annotations).mark_text(
        fontSize=12,
        fontWeight="bold",
        color="gray"
    ).encode(
        x="x:Q",
        y="y:Q",
        text="label:N"
    ).transform_calculate(
        align="datum.align",
        baseline="datum.baseline"
    )
    # Final chart with everything
    final_chart = (scatter + vline + hline + labels).properties(
        title="📊 Promo Performance Quadrants"
    )

    st.altair_chart(final_chart, use_container_width=True)


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
                "Unit Cost": "${:.2f}",
                "Units Sold\nLast Period": "{:.0f}",
                "Units Sold\nThis Period": "{:.0f}",
                "Lift": "{:.1f}",
                "Breakeven Lift": "{:.1f}",
                "Lift Delta": "{:.1f}",
                "Incremental Revenue": "${:.0f}",
                "ROI": "{:.1f}",
                "Margin %": "{:.1%}"



            })
            .map(color_roi, subset=["ROI"])
            .map(color_roi, subset=["Lift Delta"])
        , use_container_width=False
    )
    csv_data = convert_df_to_csv(display_df)



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
        Total_Revenue_Potential=("Revenue_Potential", "sum"),
        Avg_Lift=("Lift", "mean")

    ).reset_index()

    summary["ROI_Capped"] = summary["Avg_ROI"].clip(lower=-1, upper=1.5)

    # Layout: 2 columns
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📈 Unit Lift vs Number of Promotions")
        scatter3 = (
            alt.Chart(summary)
            .mark_circle(size=100, opacity=0.75)
            .encode(
                x=alt.X("Promo_Count:Q", title="Number of Promotions"),
                y=alt.Y("Avg_Lift:Q", title="Average Unit Lift"),
                size=alt.Size("Total_Revenue_Potential:Q", scale=alt.Scale(range=[30, 400])),
                color=alt.Color("ROI_Capped:Q", scale=alt.Scale(scheme="redyellowgreen", domainMid=0),
                                legend=alt.Legend(title="Avg ROI (capped)")),
                tooltip=["Item", "Promo_Count", "Avg_Lift", "Avg_ROI", "Total_Revenue"]
            )
            .properties(height=400)
            .interactive()
        )
        st.altair_chart(scatter3, use_container_width=True)

    with col2:
        st.markdown("### 💵 Avg Added Revenue vs Avg Promo Spend per Item")
        scatter2 = (
            alt.Chart(summary)
            .mark_circle(size=100, opacity=0.75)
            .encode(
                x=alt.X("Avg_Spend:Q", title="Average Promo Spend ($)"),
                y=alt.Y("Avg_Revenue:Q", title="Average Added Revenue ($)"),
                size=alt.Size("Total_Revenue_Potential:Q", scale=alt.Scale(range=[30, 400])),
                color=alt.Color("ROI_Capped:Q", scale=alt.Scale(scheme="redyellowgreen", domainMid=0),
                                legend=alt.Legend(title="Average ROI")),
                tooltip=["Item", "Avg_Spend", "Avg_Revenue", "Promo_Count", "Avg_ROI", "Total_Revenue_Potential"]
            )
            .properties(height=400)
            .interactive()
        )
        st.altair_chart(scatter2, use_container_width=True)




    st.markdown("### 📋 Historical Detail for a Selected Item")

    nonzero_items = summary[summary["Total_Revenue_Potential"] > 0]["Item"].unique()
    selected_item = st.selectbox("Select an Item", options=nonzero_items)

    item_history = df[df["Item"] == selected_item].copy()
    item_history["Profit"] = item_history["Incremental Revenue"] - item_history["Promo Spend"]

    # Columns to show
    cols = [
        "Promo Period",
        "Regular Price",
        "Special Price",
        "Unit_Cost",
        "Promo Spend",
        "Incremental Revenue",
        "ROI",
        "Lift",
        "Breakeven_Lift",
        "Lift Delta"
    ]

    display_df = item_history[cols].copy()

    # Make sure numeric total values are floats (some may get inferred as strings)
    totals = {
        "Week": "TOTAL",
        "Regular Price": None,
        "Special Price": None,
        "Promo Spend": float(display_df["Promo Spend"].sum()),
        "Incremental Revenue": float(display_df["Incremental Revenue"].sum()),
        "ROI": float(display_df["ROI"].mean()),
        "Lift": float(display_df["Lift"].mean()),
        "Breakeven_Lift": float(display_df["Breakeven_Lift"].mean()),
        "Lift Delta": float(display_df["Lift Delta"].mean())
    }


    totals_df = pd.DataFrame([totals])

    # Combine item history + totals
    display_with_totals = pd.concat([display_df, totals_df], ignore_index=True)

    # Calculate recommendation
    num_promos = len(item_history)
    avg_roi = totals["ROI"]

    # Filter for selected item
    item_weekly = weekly_df[weekly_df["Item_Description"] == selected_item].copy()
    item_weekly_sorted = item_weekly.sort_values("week_number")

    # Find last non-promo week (i.e., where there was no discount)
    non_promo_weeks = item_weekly_sorted[item_weekly_sorted["promo_spend"] == 0]

    if not non_promo_weeks.empty:
        latest_row = non_promo_weeks.iloc[-1]

        latest_units = latest_row["units_sold"]
        latest_cost = latest_row["Unit_Cost"]

        # Get most recent Special Price from a promo week
        recent_promo_price = item_history.sort_values("Promo_Start_Week")["Special Price"].dropna().iloc[-1]

        latest_price = recent_promo_price  # Use promo price for projection
        latest_margin_per_unit = latest_price - latest_cost

        # Use average lift from past promos
        avg_lift = item_history["Lift"].mean()

        # Projected performance
        projected_units = latest_units * avg_lift
        projected_profit = projected_units * latest_margin_per_unit
        projected_revenue = projected_units * latest_price


    if num_promos >= 3 and avg_roi >= 0.5:
        recommendation = f"""✅ **Run another promo — consider a deeper discount.**  
        Previous promos saw an average lift of **{avg_lift:.2f}x**, which would project **${projected_revenue:,.0f}** in revenue and **{projected_units:,.0f}** in units sold next time.""" 
    elif num_promos < 3 and avg_roi >= 0.5:
        recommendation = f"""📈 **High potential — test another promotion soon.**  
        With an average lift of **{avg_lift:.2f}x**, which would project **${projected_revenue:,.0f}** in revenue and **{projected_units:,.0f}** in units sold next time.""" 
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
            "Unit_Cost": "${:.2f}",
            "Promo Spend": "${:,.0f}",
            "Incremental Revenue": "${:,.0f}",
            "Profit": "${:,.0f}",
            "ROI": "{:.2f}",
            "Lift": "{:.1f}",
            "Breakeven_Lift": "{:.1f}",
            "Lift Delta": "{:.1f}",
            }),
        use_container_width=True
    )

    st.markdown("### 📊 Weekly Unit Sales for Selected Item")

    # Filter weekly_df to just the selected item
    item_weekly = weekly_df[weekly_df["Item_Description"] == selected_item].copy()

    # Label promo vs non-promo weeks
    item_weekly["Promo Status"] = item_weekly["promo_flag"].map({True: "Promo", False: "No Promo"})

    # Bar chart of units sold by week
    unit_chart = (
        alt.Chart(item_weekly)
        .mark_bar()
        .encode(
            x=alt.X("week_number:O", title="Week"),
            y=alt.Y("units_sold:Q", title="Units Sold"),
            color=alt.Color("Promo Status:N", scale=alt.Scale(domain=["Promo", "No Promo"], range=["#4CAF50", "#B0BEC5"])),
            tooltip=["week_number", "units_sold", "Promo Status", "Regular_Price", "Special_Price"]
        )
        .properties(height=300)
    )

    st.altair_chart(unit_chart, use_container_width=True)