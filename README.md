# 🔌 Energy Analysis Tool

A simple and powerful Streamlit app for analysing half-hourly (or similar) energy consumption data.

📍 **Try it live:** [https://energy-analysis-tool.streamlit.app/](https://energy-analysis-tool.streamlit.app/)

---

## 🚀 What It Does

This tool allows users to upload energy usage data and instantly visualise:

1. 📅 **Energy Consumption by Day of the Week**
2. 📆 **Energy Consumption by Month** (histogram style)
3. 🕒 **Average Daily Profile** (from 5am to 5am, with optional anomaly filtering and trend line)
4. 📈 **Maximum Daily Profile** (from 5am to 5am, shows peak value per time block)
5. 📉 **Diversity Curve** (normalised to 95th percentile of filtered or unfiltered data)
6. 🧮 **Hourly Diversity Factor Table** (auto-generated from the diversity curve, downloadable as CSV)
7. 🧹 Option to **filter anomalies** using 10th–90th percentile logic across all time-based plots
8. 📅 Optional **date range inclusion/exclusion filters** (e.g. exclude COVID period)

---

## 📄 Input Format

Upload a `.csv` or `.xlsx` file with the following three columns:

| Date       | Time    | Value (kWh) |
|------------|---------|--------------|
| 2025-03-30 | 14:00   | 12.5         |

- **Date**: Format like `YYYY-MM-DD`
- **Time**: Format like `HH:MM` (e.g. `14:00`)
- **Value (kWh)**: Numeric value representing energy consumption

> Column headers don't have to match exactly — the app uses fuzzy matching to standardise them.

---

## 🧪 Try It Online (No Setup Required)

Run it instantly in your browser via Streamlit Cloud:  
🔗 [https://energy-analysis-tool.streamlit.app/](https://energy-analysis-tool.streamlit.app/)

---

## 💻 Running It Locally

Follow these steps to run the app on your own machine:

<details>
<summary>Click to expand terminal setup steps</summary>

```bash
# Step 1: Clone the repository
git clone https://github.com/your-username/energy-analysis-tool.git
cd energy-analysis-tool

# Step 2: Create and activate virtual environment

# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Step 3: Install required packages
pip install -r requirements.txt

# Step 4: Launch the Streamlit app
streamlit run app.py
```
</details>

---

## 🧩 Example Dataset

Need test data? Try this downloadable 2-year sample with weekday/weekend trends and embedded anomalies:  
📥 [example_energy_data_2years_from_original.xlsx](https://energy-analysis-tool.streamlit.app/example_energy_data_2years_from_original.xlsx)

---

## 🌟 Recent Enhancements
✅ Maximum Daily Profile (Plot 3B) now reflects filtering toggle

✅ Diversity Table and curve logic fixed to avoid values > 1.0 when filtering is off

✅ Downloadable CSV for hourly diversity factors

✅ Footer-styled MIT license block with collapsible toggle

✅ Refined dark theme compatibility and styling polish

---

## ⚖️ License

MIT License © 2025 Henry Metcalfe
