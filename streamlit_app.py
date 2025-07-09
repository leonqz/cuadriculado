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



# ========== Section 2: Private Label Promo Data ==========


df = load_data()

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

