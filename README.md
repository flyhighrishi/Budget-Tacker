# 💸 Personal Wealth Intelligence Workspace

A clean, tab-reorganized personal finance application built using **Streamlit**, **Python**, and **SQLite**. This system implements a structured cash flow hierarchy—accounting for fixed debt commitments, structural utility parameters, and recurring tax provisions—before dividing your remaining disposable income into automated spending and investment pools.


## 🗂️ Application Workspace Layout

To eliminate UI clutter, the application workspace is organized into five dedicated functional modules using a tabbed layout:

1. **📊 Monthly Overview Dashboard:** A high-level control terminal displaying your structural capital architecture, holistic salary pie charts, and active sinking fund milestone tracking.
2. **🔮 Predictive Cash Flow Runway:** A forward-looking projection model that simulates cash flow trends 6 months into the future based on a variable spending velocity slider.
3. **🛡️ Tax Optimization Matrix:** An automated tracker mapped to local tax exemption thresholds (e.g., Section 80C) that flags shortfall gaps and gives deployment advice.
4. **🛒 Local Transaction Ledger:** A transactional log backed by a permanent, local SQLite database featuring real-time budget burn progress bars.
5. **📈 Payday Execution Room:** A recurring checklist ensuring all automated index ETFs, fixed-income tranches, and goal sinking provisions are executed and archived monthly.

---

## 🛠️ Tech Stack & Dependencies

- **Framework:** [Streamlit](https://streamlit.io/) (Local UI rendering)
- **Data Architecture:** [Pandas](https://pandas.pydata.org/)
- **Visual Analytics:** [Plotly Express](https://plotly.com/python/)
- **Storage Layer:** [SQLite3](https://docs.python.org/3/library/sqlite3.html) (Local file-based persistence: `wealth.db`)

---

## 🚀 Getting Started

### 1. Installation
Ensure you have Python 3.8+ installed. Install the necessary calculation and visualization dependencies via terminal: 
//bash
pip install streamlit pandas plotly
**2. File Organization**

Place your application script inside your project directory. Your workspace layout should look like this:PlaintextBudget-Tracker/
├── app.py          # Main application script
├── README.md       # Project documentation
└── wealth.db       # Automatically generated local database file
**3. Execution**
Launch the local environment server by invoking the Streamlit module through your python terminal path:
Bash
python -m streamlit run app.py
The dashboard will securely initialize and open at http://localhost:8501.
**📈 Underlying Cash Flow Logic**

The application follows a strict financial pipeline to ensure accurate disposable income tracking:$$\text{Gross Monthly Salary} \longrightarrow \text{Minus Fixed EMIs \& Tax Provisions} \longrightarrow \text{Net Disposable Pool}$$
The Net Disposable Pool is then split using the 50/30/20 Rule:
**50% Essentials Bucket**: Automatically absorbs fixed base utility entries (electricity and water bills).
**30% Discretionary Bucket:** Automatically absorbs calculated goal sinking fund contributions before displaying your remaining "guilt-free" spending money.
**20% Investing Bucket:** Divided into Equity, Debt, and Liquid pools according to your target risk profile strategy.
**🔒 Security & Local Data Privacy**

This platform is designed as a local-first, private workspace. All financial details, liabilities, asset classes, and transaction items are stored entirely on your own machine inside the local encrypted wealth.db file. No data is transmitted to external servers.