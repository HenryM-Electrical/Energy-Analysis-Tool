import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

st.set_page_config(page_title="Energy Analysis Tool", layout="wide")
st.title("🔌 Energy Consumption Analysis Tool")

st.markdown("""
Paste or upload your data with the following columns:
- **Date** (e.g. 2025-03-30)
- **Time** (e.g. 14:00)
- **kWh Value** (numeric)
""")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv", "xlsx"])

@st.cache_data

def load_data(file):
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
    return df

if uploaded_file:
    df = load_data(uploaded_file)

    # Standardize column names
    df.columns = [col.strip().lower() for col in df.columns]
    df.rename(columns={
        'value (kwh)': 'kwh',
        'date': 'date',
        'time': 'time'
    }, inplace=True)

    # Combine datetime
    df['datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'].astype(str))
    df = df.sort_values(by='datetime')
    df.set_index('datetime', inplace=True)

    # Optional date range filter
    st.sidebar.subheader("Optional Filters")
    date_min = df.index.min().date()
    date_max = df.index.max().date()
    date_range = st.sidebar.date_input("Exclude data in this date range (e.g. COVID)", [], min_value=date_min, max_value=date_max)

    if len(date_range) == 2:
        df = df[~((df.index.date >= date_range[0]) & (df.index.date <= date_range[1]))]

    # Optional anomaly filter
    apply_filter = st.checkbox("Filter anomalies from daily profile (based on standard deviation)", value=True)

    # ------------------ Plot 1: Energy by Day of Week ------------------
    st.subheader("1. Energy Consumption by Day of Week")
    df['weekday'] = df.index.day_name()
    daily = df.groupby('weekday')['kwh'].sum()
    ordered_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    daily = daily.reindex(ordered_days)
    st.bar_chart(daily)

    # ------------------ Plot 2: Energy Consumption by Month (Histogram Style) ------------------
    st.subheader("2. Energy Consumption by Month")
    df['month'] = df.index.month_name()
    monthly = df.groupby('month')['kwh'].sum()
    month_order = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]
    monthly = monthly.reindex(month_order)

    fig2, ax2 = plt.subplots(figsize=(10, 4))
    ax2.bar(monthly.index, monthly.values, width=0.6)
    ax2.set_ylabel("kWh")
    ax2.set_title("Monthly Energy Consumption")
    ax2.set_xticklabels(monthly.index, rotation=45)
    st.pyplot(fig2)

    # ------------------ Plot 3: Average Daily Profile (5am to 5am) ------------------
    st.subheader("3. Average Daily Profile (5am to 5am)")
    df['hour_minute'] = df.index.strftime('%H:%M')
    df['sort_key'] = pd.to_datetime(df['hour_minute'], format='%H:%M')
    df['sort_label'] = df['sort_key'].dt.strftime('%H:%M')

    # Reorder starting from 05:00
    time_order = pd.date_range("05:00", "23:30", freq="30min").strftime("%H:%M").tolist() + \
                 pd.date_range("00:00", "04:30", freq="30min").strftime("%H:%M").tolist()

    profile_data = df.groupby('sort_label')['kwh'].agg(['mean', 'std'])
    profile_series = profile_data['mean']
    profile_series = profile_series.reindex(time_order)

    if apply_filter:
        z_scores = np.abs(stats.zscore(profile_series.dropna()))
        profile_series.loc[profile_series.dropna().index[z_scores >= 2.5]] = np.nan

    fig3, ax3 = plt.subplots(figsize=(10, 4))
    profile_series.plot(ax=ax3, label='Average Load Profile')
    profile_series.rolling(4, center=True).mean().plot(ax=ax3, linestyle='--', label='Trend Line')
    ax3.set_ylabel("kWh")
    ax3.set_xlabel("Time of Day (starting 5am)")
    ax3.set_title("Average Daily Profile")
    ax3.legend()
    st.pyplot(fig3)

    # ------------------ Plot 4: Diversity Curve ------------------
    st.subheader("4. Diversity Curve (Normalised to Max Demand)")
    diversity_curve = profile_series / profile_series.max()

    fig4, ax4 = plt.subplots(figsize=(10, 4))
    diversity_curve.plot(ax=ax4, label='Diversity Curve (0.0 - 1.0)', color='green')
    ax4.set_ylabel("Normalised Load")
    ax4.set_xlabel("Time of Day (starting 5am)")
    ax4.set_title("Diversity Curve")
    ax4.set_ylim(0, 1.05)
    ax4.legend()
    st.pyplot(fig4)

else:
    st.info("Please upload a CSV or Excel file to get started.")
