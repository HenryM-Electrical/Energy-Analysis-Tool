# 🔌 Energy Analysis Tool

A simple and powerful Streamlit app for analysing half-hourly (or similar) energy consumption data.

📍 **Try it live:** [https://energy-analysis-tool.streamlit.app/](https://energy-analysis-tool.streamlit.app/)

---

## 🚀 What It Does

This tool allows users to upload energy usage data and instantly visualise:

1. 📅 **Energy Consumption by Day of the Week**
2. 📆 **Energy Consumption by Month** (histogram format)
3. 🕒 **Average Daily Profile** (from 5am to 5am, with optional trend line)
4. 📉 **Diversity Curve** (normalised to max demand, between 0.0 and 1.0)
5. ✅ Option to **filter anomalies** in the daily profile using z-score filtering

---

## 📄 Input Format

Upload a `.csv` or `.xlsx` file with the following three columns:

| Date       | Time    | Value (kWh) |
|------------|---------|--------------|
| 2025-03-30 | 14:00   | 12.5         |

- **Date**: Format like `YYYY-MM-DD`
- **Time**: Format like `HH:MM` (e.g. `14:00`)
- **Value (kWh)**: Numeric value representing energy consumption

> Column headers don't have to match exactly — the app will standardise them automatically.

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
