import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

st.set_page_config(page_title="Energy Analysis Tool", layout="wide")

# Google Analytics (G-2Z50C9EQP7)
st.markdown("""
<!-- Global site tag (gtag.js) - Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-2Z50C9EQP7"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-2Z50C9EQP7');
</script>
""", unsafe_allow_html=True)

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
        return pd.read_csv(file)
    else:
        return pd.read_excel(file)

@st.cache_data
def preprocess_data(df):
    df = df.loc[:, ~df.columns.str.contains('^Unnamed', case=False)]
    df.columns = [str(col).strip().lower() for col in df.columns]

    fuzzy_map = {
        'datetime': ['datetime', 'reading time'],
        'date': ['date', 'reading date', 'day'],
        'time': ['time', 'hour'],
        'kwh': ['kwh', 'energy use', 'usage', 'power', 'value (kwh)', 'reading', 'consumption kwh']
    }

    col_map = {}
    for std_col, options in fuzzy_map.items():
        for opt in options:
            matches = [col for col in df.columns if opt in col]
            for match in matches:
                if std_col == 'kwh' and pd.api.types.is_numeric_dtype(df[match]) and df[match].notna().any():
                    col_map[std_col] = match
                    break
                elif std_col != 'kwh' and df[match].notna().any():
                    col_map[std_col] = match
                    break
            if std_col in col_map:
                break

    if 'datetime' in col_map and ('date' not in col_map or 'time' not in col_map):
        df['datetime'] = pd.to_datetime(df[col_map['datetime']], errors='coerce')
        df['date'] = df['datetime'].dt.date
        df['time'] = df['datetime'].dt.strftime('%H:%M')
    elif 'date' in col_map and 'time' in col_map:
        date_strs = df[col_map['date']].astype(str).values
        time_strs = df[col_map['time']].astype(str).values
        datetime_strs = [f"{d} {t}" for d, t in zip(date_strs, time_strs)]
        df['datetime'] = pd.to_datetime(datetime_strs, errors='coerce')
    else:
        st.error("Could not identify 'date' and 'time' columns or a combined 'datetime' column.")
        st.stop()

    if 'kwh' not in col_map:
        st.error("Could not identify a valid numeric 'kWh' column.")
        st.stop()

    df.rename(columns={col_map['kwh']: 'kwh'}, inplace=True)
    df = df.dropna(subset=['datetime', 'kwh'])
    df = df[~df['datetime'].duplicated()]
    df = df.sort_values(by='datetime')
    df.set_index('datetime', inplace=True)

    df['hour_minute'] = df.index.strftime('%H:%M')
    df['sort_key'] = pd.to_datetime(df['hour_minute'], format='%H:%M')
    df['sort_label'] = df['sort_key'].dt.strftime('%H:%M')

    return df

if uploaded_file:
    df_raw = load_data(uploaded_file)
    df = preprocess_data(df_raw)

    time_order = pd.date_range("05:00", "23:30", freq="30min").strftime("%H:%M").tolist() + \
                 pd.date_range("00:00", "04:30", freq="30min").strftime("%H:%M").tolist()

    st.sidebar.subheader("Optional Filters")
    valid_dates = df.index.dropna()
    date_min = valid_dates.min().date()
    date_max = valid_dates.max().date()

    include_range = st.sidebar.date_input("Include only this date range", [date_min, date_max], min_value=date_min, max_value=date_max)
    if len(include_range) == 2:
        df = df[(df.index.date >= include_range[0]) & (df.index.date <= include_range[1])]

    exclude_range = st.sidebar.date_input("Exclude data in this date range (e.g. COVID)", [], min_value=date_min, max_value=date_max)
    if len(exclude_range) == 2:
        df = df[~((df.index.date >= exclude_range[0]) & (df.index.date <= exclude_range[1]))]

    apply_filter = st.sidebar.checkbox("Filter anomalies from daily profile (10th–90th percentile)", value=True)

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
    st.pyplot(fig1)

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

    # ------------------ Plot 3A: Average Daily Profile (5am to 5am) ------------------
    st.subheader("3A. Average Daily Profile (5am to 5am)")
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

    filtered_profile_series = pd.Series(filtered_means, index=time_order) * 2

    fig3a, ax3a = plt.subplots(figsize=(10, 4))
    if apply_filter:
        filtered_profile_series.plot(ax=ax3a, label='Average Profile', color='#8B635C', linestyle='--')
        filtered_profile_series.rolling(4, center=True).mean().plot(ax=ax3a, linestyle='-', label='Trend Line', color='#0F432F')
    else:
        profile_series = grouped.mean().reindex(time_order) * 2
        profile_series.plot(ax=ax3a, label='Average Profile', color='#0F432F')
        profile_series.rolling(4, center=True).mean().plot(ax=ax3a, linestyle='--', label='Trend Line', color='#8B635C')

    ax3a.set_ylabel("Energy (kWh)")
    ax3a.set_xlabel("Time of Day (starting 5am)")
    ax3a.set_title("Average Daily Profile")
    ax3a.set_xticks([i for i, t in enumerate(time_order) if t.endswith(':00')])
    ax3a.set_xticklabels([t for t in time_order if t.endswith(':00')], rotation=45)
    ax3a.legend()
    st.pyplot(fig3a)

    # ------------------ Plot 3B: Maximum Daily Profile (Hourly Scaled) ------------------
    st.subheader("3B. Maximum Daily Profile (5am to 5am)")
    grouped_max = df.groupby('sort_label')['kwh']

    max_profile_values = []
    for label in time_order:
        if label in grouped_max.groups:
            values = grouped_max.get_group(label)
            if apply_filter:
                q10 = values.quantile(0.10)
                q90 = values.quantile(0.90)
                values = values[(values >= q10) & (values <= q90)]
            max_profile_values.append(values.max() * 2 if not values.empty else None)
        else:
            max_profile_values.append(None)

    max_profile = pd.Series(max_profile_values, index=time_order)

    fig3b, ax3b = plt.subplots(figsize=(10, 4))
    max_profile.plot(ax=ax3b, color='#0F432F', label='Maximum Profile')
    ax3b.set_ylabel("Energy (kWh)")
    ax3b.set_xlabel("Time of Day (starting 5am)")
    ax3b.set_title("Maximum Daily Profile")
    ax3b.set_xticks([i for i, t in enumerate(time_order) if t.endswith(':00')])
    ax3b.set_xticklabels([t for t in time_order if t.endswith(':00')], rotation=45)
    ax3b.legend()
    st.pyplot(fig3b)

    # ------------------ Plot 4: Diversity Curve (Normalised to 95th Percentile in Filtered Range) ------------------
    st.subheader("4. Diversity Curve")
    scaling_factor = 2 if apply_filter else 1

    if apply_filter:
        all_filtered_values = []
        for label in time_order:
            if label in grouped.groups:
                values = grouped.get_group(label)
                q10 = values.quantile(0.10)
                q90 = values.quantile(0.90)
                filtered = values[(values >= q10) & (values <= q90)]
                all_filtered_values.extend(filtered)
        reference_peak = pd.Series(all_filtered_values).quantile(0.95) * scaling_factor
        diversity_curve = filtered_profile_series / reference_peak
        base_series = filtered_profile_series
    else:
        profile_series = df.groupby('sort_label')['kwh'].mean().reindex(time_order)
        base_series = profile_series * scaling_factor
        reference_peak = df['kwh'].quantile(0.95) * scaling_factor
        diversity_curve = base_series / reference_peak

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

    hourly_index = pd.date_range("2000-01-01 05:00", periods=len(base_series), freq="30min")
    hourly_series_dt = pd.Series(base_series.values, index=hourly_index)
    hourly_resampled = hourly_series_dt.resample("1H").mean()
    hourly_order = pd.date_range("2000-01-01 05:00", "2000-01-02 04:00", freq="1H")
    hourly_resampled = hourly_resampled.reindex(hourly_order).fillna(0)
    hourly_diversity = (hourly_resampled / reference_peak).round(3)

    time_labels = hourly_order.strftime("%H:%M").tolist()
    diversity_values = hourly_diversity.values.tolist()

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

    diversity_csv = pd.DataFrame([diversity_values], columns=time_labels, index=["Diversity Factor"])
    csv = diversity_csv.to_csv(index=False).encode('utf-8')
    st.download_button(label="Download CSV", data=csv, file_name='diversity_factors.csv', mime='text/csv')
