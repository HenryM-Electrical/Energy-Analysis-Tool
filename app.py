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

    # Optional date range filters
    st.sidebar.subheader("Optional Filters")
    date_min = df.index.min().date()
    date_max = df.index.max().date()

    if st.sidebar.button("Reset Date Filters"):
        st.experimental_rerun()

    include_range = st.sidebar.date_input("Include only this date range", [date_min, date_max], min_value=date_min, max_value=date_max)
    if len(include_range) == 2:
        df = df[(df.index.date >= include_range[0]) & (df.index.date <= include_range[1])]

    exclude_range = st.sidebar.date_input("Exclude data in this date range (e.g. COVID)", [], min_value=date_min, max_value=date_max)
    if len(exclude_range) == 2:
        df = df[~((df.index.date >= exclude_range[0]) & (df.index.date <= exclude_range[1]))]

    # Anomaly filter toggle using 10th–90th percentile logic
    apply_filter = st.checkbox("Filter anomalies from daily profile (10th–90th percentile)", value=True)

    # ------------------ Plot 1: Energy by Day of Week ------------------
    df['weekday'] = df.index.day_name()
    daily = df.groupby('weekday')['kwh'].sum()
    ordered_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    daily = daily.reindex(ordered_days)
    st.subheader("1. Energy Consumption by Day of Week")
    fig1, ax1 = plt.subplots(figsize=(10, 4))
    ax1.bar(daily.index, daily.values, color='#0F432F')
    ax1.set_ylabel("kWh")
    ax1.set_title("Energy Consumption by Day of Week")
    ax1.set_xticklabels(daily.index, rotation=45)
    st.pyplot(fig1)  # Streamlit's built-in bar_chart does not support manual colour styling

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
    ax2.bar(monthly.index, monthly.values, width=0.6, color='#0F432F')
    ax2.set_ylabel("kWh")
    ax2.set_title("Monthly Energy Consumption")
    ax2.set_xticklabels(monthly.index, rotation=45)
    st.pyplot(fig2)

    # ------------------ Plot 3: Average Daily Profile (5am to 5am) ------------------
    st.subheader("3. Average Daily Profile (5am to 5am)")
    df['hour_minute'] = df.index.strftime('%H:%M')
    df['sort_key'] = pd.to_datetime(df['hour_minute'], format='%H:%M')
    df['sort_label'] = df['sort_key'].dt.strftime('%H:%M')

    time_order = pd.date_range("05:00", "23:30", freq="30min").strftime("%H:%M").tolist() + \
                 pd.date_range("00:00", "04:30", freq="30min").strftime("%H:%M").tolist()

    # Improved per-bin filtering
    grouped = df.groupby('sort_label')['kwh']
    filtered_means = []
    for label in time_order:
        if label in grouped.groups:
            values = grouped.get_group(label)
            q10 = values.quantile(0.10)
            q90 = values.quantile(0.90)
            filtered = values[(values >= q10) & (values <= q90)]
            filtered_means.append(filtered.mean())
        else:
            filtered_means.append(None)

    filtered_profile_series = pd.Series(filtered_means, index=time_order)

    fig3, ax3 = plt.subplots(figsize=(10, 4))
    if apply_filter:
        filtered_profile_series.plot(ax=ax3, label='Filtered Profile (10–90%)', color='#8B635C', linestyle='--')
        filtered_profile_series.rolling(4, center=True).mean().plot(ax=ax3, linestyle='-', label='Trend Line', color='#0F432F')
    else:
        profile_data = df.groupby('sort_label')['kwh'].agg(['mean'])
        profile_series = profile_data['mean'].reindex(time_order)
        profile_series.plot(ax=ax3, label='Unfiltered Profile', color='#0F432F')
        profile_series.rolling(4, center=True).mean().plot(ax=ax3, linestyle='--', label='Trend Line', color='#8B635C')

    ax3.set_ylabel("kWh")
    ax3.set_xlabel("Time of Day (starting 5am)")
    ax3.set_title("Average Daily Profile")
    ax3.set_xticks([i for i, t in enumerate(time_order) if t.endswith(':00')])
    ax3.set_xticklabels([t for t in time_order if t.endswith(':00')], rotation=45)
    ax3.legend()
    st.pyplot(fig3)

    # ------------------ Plot 4: Diversity Curve (Normalised to 95th Percentile in Filtered Range) ------------------
    st.subheader("4. Diversity Curve")

    # Set reference peak based on filter setting
    if apply_filter:
        all_filtered_values = []
        for label in time_order:
            if label in grouped.groups:
                values = grouped.get_group(label)
                q10 = values.quantile(0.10)
                q90 = values.quantile(0.90)
                filtered = values[(values >= q10) & (values <= q90)]
                all_filtered_values.extend(filtered)
        reference_peak = pd.Series(all_filtered_values).quantile(0.95)
        diversity_curve = filtered_profile_series / reference_peak
    else:
        profile_data = df.groupby('sort_label')['kwh'].agg(['mean'])
        profile_series = profile_data['mean'].reindex(time_order)
        reference_peak = df['kwh'].quantile(0.95)
        diversity_curve = profile_series / reference_peak

    fig4, ax4 = plt.subplots(figsize=(10, 4))
    diversity_curve.plot(ax=ax4, label='Diversity Curve', color='#0F432F')
    ax4.set_ylabel("Diversity Factor")
    ax4.set_xlabel("Time of Day (starting 5am)")
    ax4.set_title("Diversity Curve")
    ax4.set_ylim(0, diversity_curve.max() * 1.1)
    ax4.set_xticks([i for i, t in enumerate(time_order) if t.endswith(':00')])
    ax4.set_xticklabels([t for t in time_order if t.endswith(':00')], rotation=45)
    ax4.legend()
    st.pyplot(fig4)

    # ------------------ Table: Hourly Diversity Factors ------------------
    st.subheader("5. Hourly Diversity Factors Table")

    # Use datetime-aware index for resampling
    filtered_datetime_index = pd.date_range("2000-01-01 05:00", periods=len(filtered_profile_series), freq="30min")
    filtered_profile_series_dt = pd.Series(filtered_profile_series.values, index=filtered_datetime_index)
    hourly_resampled = filtered_profile_series_dt.resample("1H").mean()

    hourly_order = pd.date_range("2000-01-01 05:00", "2000-01-02 04:00", freq="1H")
    hourly_resampled = hourly_resampled.reindex(hourly_order).fillna(0)

    # Use correct reference peak from filtered data
    hourly_diversity = (hourly_resampled / reference_peak).round(3)

    # Create DataFrame
    time_labels = hourly_order.strftime("%H:%M").tolist()
    diversity_values = hourly_diversity.values.tolist()

    # HTML table with reduced font size and brand colours
    time_cells = ''.join([f"<td>{t}</td>" for t in time_labels])
    diversity_cells = ''.join([f"<td>{v}</td>" for v in diversity_values])

    table_html = """
    <style>
        .diversity-table {
            font-size: 12px;
            border-collapse: collapse;
            color: #040926;
        }
        .diversity-table th, .diversity-table td {
            padding: 4px 6px;
            border: 1px solid #D0CCD0;
            text-align: center;
        }
        .diversity-table th {
            background-color: #93A29B;
        }
        .diversity-table td {
            background-color: #FFFFFF;
        }
    </style>
    <table class='diversity-table'>
        <tr><th>Time</th>""" + time_cells + """</tr>
        <tr><th>Diversity Factor</th>""" + diversity_cells + """</tr>
    </table>
    """

    st.markdown(table_html, unsafe_allow_html=True)



    # Offer CSV download
    diversity_csv = pd.DataFrame([diversity_values], columns=time_labels, index=["Diversity Factor"])
    csv = diversity_csv.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name='diversity_factors.csv',
        mime='text/csv',
    )


