import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime, timedelta

# ==========================================
# 1. PAGE SETUP & HYBRID RESPONSIVE CSS
# ==========================================
st.set_page_config(page_title="Universal Wealth Workspace", layout="wide")

# This media query chunk automatically overrides layouts depending on screen width
st.markdown("""
    <style>
        /* Baseline Layout Cleanup */
        .block-container {
            padding-top: 0.75rem !important;
            padding-bottom: 0.5rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        header[data-testid="stHeader"] {
            height: 1.2rem !important;
        }
        
        /* DESKTOP VIEWPORTS (Screens wider than 768px) */
        @media (min-width: 769px) {
            [data-testid="stMetricValue"] {
                font-size: 2.2rem !important;
            }
            [data-testid="stMetricLabel"] {
                font-size: 1rem !important;
            }
            h1 { font-size: 2.5rem !important; }
            h2 { font-size: 1.8rem !important; }
            h3 { font-size: 1.4rem !important; }
        }

        /* MOBILE VIEWPORTS (Screens 768px or narrower) */
        @media (max-width: 768px) {
            .block-container {
                padding-left: 0.5rem !important;
                padding-right: 0.5rem !important;
            }
            [data-testid="stMetricValue"] {
                font-size: 5.5vw !important;
                font-weight: bold;
            }
            [data-testid="stMetricLabel"] {
                font-size: 3.2vw !important;
            }
            h1 { font-size: 6.5vw !important; }
            h2 { font-size: 5.5vw !important; }
            h3 { font-size: 4.8vw !important; }
            
            /* Squeeze padding for mobile touchscreen thumb taps */
            button[data-baseweb="tab"] {
                padding-left: 8px !important;
                padding-right: 8px !important;
                font-size: 3.4vw !important;
            }
            
            /* Force horizontal columns to break and stack vertically on mobile */
            [data-testid="stHorizontalBlock"] {
                flex-direction: column !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. LOCAL PERSISTENT STORAGE (SQLITE)
# ==========================================
DB_FILE = "wealth.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            description TEXT,
            category TEXT,
            amount REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historical_snapshots (
            month TEXT PRIMARY KEY,
            net_salary REAL,
            structural_outflows REAL,
            total_invested REAL,
            portfolio_value REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            target REAL,
            saved REAL,
            target_date TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def seed_default_data():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM historical_snapshots")
    if cursor.fetchone()[0] == 0:
        mock_history = [
            ("2026-01", 150000.0, 44000.0, 21200.0, 480000.0),
            ("2026-02", 150000.0, 44000.0, 21200.0, 502000.0),
            ("2026-03", 150000.0, 44000.0, 21200.0, 515000.0),
            ("2026-04", 150000.0, 44000.0, 21200.0, 540000.0),
        ]
        cursor.executemany("INSERT OR REPLACE INTO historical_snapshots VALUES (?,?,?,?,?)", mock_history)
    
    cursor.execute("SELECT COUNT(*) FROM goals")
    if cursor.fetchone()[0] == 0:
        mock_goals = [
            ("Nepal Milestone Travel (Dec 2026)", 150000.0, 50000.0, "2026-12-01"),
            ("Home Capital Buffer", 500000.0, 160000.0, "2027-06-01")
        ]
        cursor.executemany("INSERT OR REPLACE INTO goals (name, target, saved, target_date) VALUES (?, ?, ?, ?)", mock_goals)
    conn.commit()
    conn.close()

seed_default_data()

if "portfolio_holdings" not in st.session_state:
    st.session_state.portfolio_holdings = {
        "Equity": 380000.0,
        "Debt/Fixed Income": 120000.0,
        "Emergency/Liquid": 40000.0
    }

if "sip_checklist" not in st.session_state:
    st.session_state.sip_checklist = {}

# ==========================================
# 3. CONTROLLER UTILITIES
# ==========================================
def load_expenses_from_db():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM expenses ORDER BY date DESC", conn)
    conn.close()
    return df

def save_expense_to_db(date_str, desc, cat, amt):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO expenses (date, description, category, amount) VALUES (?, ?, ?, ?)", (date_str, desc, cat, amt))
    conn.commit()
    conn.close()

def load_goals_from_db():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM goals", conn)
    conn.close()
    return df.to_dict(orient="records")

def save_goal_to_db(name, target, saved, date_str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO goals (name, target, saved, target_date) VALUES (?, ?, ?, ?)", (name, target, saved, date_str))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_target_weights(risk_profile):
    if risk_profile == "Conservative":
        return {"Equity": 0.25, "Debt/Fixed Income": 0.55, "Emergency/Liquid": 0.20}
    elif risk_profile == "Moderate":
        return {"Equity": 0.55, "Debt/Fixed Income": 0.35, "Emergency/Liquid": 0.10}
    else:
        return {"Equity": 0.75, "Debt/Fixed Income": 0.15, "Emergency/Liquid": 0.10}

# ==========================================
# 4. CONTROL DECK PARAMETER ENTRY
# ==========================================
st.sidebar.header("🎯 Master Control Deck")
gross_salary = st.sidebar.number_input("Monthly Net Salary (INR):", min_value=0, value=150000, step=5000)

st.sidebar.subheader("🪓 Loan EMIs")
home_loan_emi = st.sidebar.number_input("Home Loan EMI (INR):", min_value=0, value=35000, step=1000)
personal_loan_emi = st.sidebar.number_input("Personal Loan EMI (INR):", min_value=0, value=8000, step=500)

st.sidebar.subheader("🚰 Fixed Bills & Taxes")
electricity_bill = st.sidebar.number_input("Avg Electricity / Month:", min_value=0, value=3500, step=500)
water_bill = st.sidebar.number_input("Avg Water / Month:", min_value=0, value=500, step=100)
annual_property_tax = st.sidebar.number_input("Annual Property Tax:", min_value=0, value=12000, step=1000)

# Computational Inferences
monthly_property_tax_cushion = annual_property_tax / 12
total_fixed_structural_outflow = home_loan_emi + personal_loan_emi + monthly_property_tax_cushion
disposable_income_pool = max(0, gross_salary - total_fixed_structural_outflow)
total_monthly_utilities = electricity_bill + water_bill

risk_profile = st.sidebar.selectbox("Risk Profile Strategy:", ["Conservative", "Moderate", "Aggressive"], index=1)

# Dynamic Target Milestones Parser
active_milestones = load_goals_from_db()
total_monthly_goal_sinking = 0.0
current_date = datetime.today()
calculated_goals_list = []

for goal in active_milestones:
    target_date = datetime.strptime(goal["target_date"], "%Y-%m-%d")
    months_remaining = max(1, (target_date.year - current_date.year) * 12 + (target_date.month - current_date.month))
    runrate = max(0.0, goal["target"] - goal["saved"]) / months_remaining
    total_monthly_goal_sinking += runrate
    
    calculated_goals_list.append({
        "Name": goal["name"],
        "Target (INR)": goal["target"],
        "Saved (INR)": goal["saved"],
        "Months Remaining": months_remaining,
        "Runrate/Mo": runrate
    })

# Allocation Slices Engine
essentials_target = disposable_income_pool * 0.50
gross_discretionary = disposable_income_pool * 0.30
investing_target = disposable_income_pool * 0.20
net_discretionary_guilt_free = max(0.0, gross_discretionary - total_monthly_goal_sinking)

# ==========================================
# 5. USER WORKSPACE DECK & TABS
# ==========================================
st.title("💸 Personal Finance Workspace")

tab_dashboard, tab_runway, tab_tax, tab_ledger, tab_payday = st.tabs([
    "📊 Summary", "🔮 Runway", "🛡️ Tax", "🛒 Ledger", "📈 Payday"
])

# ------------------------------------------
# TAB 1: MONTHLY OVERVIEW DASHBOARD
# ------------------------------------------
with tab_dashboard:
    st.subheader("Current Month Framework Split")
    
    # 🌟 Laptop/Mobile Adaptive Metrics: Automatically divides or collapses safely
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("Fixed Debts", f"₹{total_fixed_structural_outflow:,.0f}")
    m_col2.metric("Needs (50%)", f"₹{essentials_target:,.0f}")
    m_col3.metric("Goal Sinking", f"₹{total_monthly_goal_sinking:,.0f}")
    m_col4.metric("Guilt-Free Cash", f"₹{net_discretionary_guilt_free:,.0f}")
    
    st.markdown("---")
    
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("#### Capital Distribution Architecture")
        alloc_map = {
            "Structural EMIs": home_loan_emi + personal_loan_emi,
            "Property Tax Provision": monthly_property_tax_cushion,
            "Utility Outlays": total_monthly_utilities,
            "Remaining Essentials": max(0.0, essentials_target - total_monthly_utilities),
            "Goal Savings": total_monthly_goal_sinking,
            "Wants Allocation": net_discretionary_guilt_free,
            "Investments Tranche": investing_target
        }
        fig_budget = px.pie(names=list(alloc_map.keys()), values=list(alloc_map.values()), color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_budget.update_layout(margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_budget, use_container_width=True)
        
    with chart_col2:
        st.markdown("#### Sinking Fund Registry")
        if calculated_goals_list:
            goals_df = pd.DataFrame(calculated_goals_list)
            st.dataframe(goals_df[["Name", "Target (INR)", "Saved (INR)", "Runrate/Mo"]], use_container_width=True, hide_index=True)
            for g in calculated_goals_list:
                pct = min(g["Saved (INR)"] / g["Target (INR)"], 1.0)
                st.caption(f"**{g['Name']}**: {pct*100:.1f}% (Required: ₹{g['Runrate/Mo']:,.0f}/mo)")
                st.progress(pct)
        else:
            st.info("No active milestones tracked in memory.")

    st.markdown("---")
    st.subheader("✨ Add Milestones On-The-Go")
    with st.form("milestone_form_universal", clear_on_submit=True):
        new_g_name = st.text_input("Goal Identity Name")
        new_g_target = st.number_input("Target Amount (INR)", min_value=0.0, value=50000.0, step=5000.0)
        new_g_saved = st.number_input("Initial Saved Buffer (INR)", min_value=0.0, value=0.0, step=1000.0)
        new_g_date = st.date_input("Target Deadline", datetime.today() + timedelta(days=365))
        
        if st.form_submit_button("Add Milestone to Architecture", use_container_width=True):
            if new_g_name:
                formatted_date = new_g_date.strftime('%Y-%m-%d')
                if save_goal_to_db(new_g_name, new_g_target, new_g_saved, formatted_date):
                    st.success("✨ New milestone saved successfully!")
                    st.rerun()
                else:
                    st.error("❌ Duplicate goal entry identifier detected.")

# ------------------------------------------
# TAB 2: PREDICTIVE CASH FLOW RUNWAY
# ------------------------------------------
with tab_runway:
    st.subheader("6-Month Liquidity Path Projections")
    
    expenses_df = load_expenses_from_db()
    current_month_str = datetime.today().strftime('%Y-%m')
    current_month_expenses = expenses_df[expenses_df['date'].str.startswith(current_month_str)] if not expenses_df.empty else pd.DataFrame()
    avg_monthly_discretionary_spend = current_month_expenses[current_month_expenses['category'] == "Discretionary (Wants)"]['amount'].sum() if not current_month_expenses.empty else 15000.0
    
    spending_multiplier = st.slider("Simulate Variable Spending Velocity:", min_value=0.5, max_value=2.0, value=1.0, step=0.1)
    simulated_spend = avg_monthly_discretionary_spend * spending_multiplier
    
    runway_projection = []
    simulated_liquid_cash = st.session_state.portfolio_holdings["Emergency/Liquid"]
    
    for i in range(1, 7):
        future_date = datetime.today() + timedelta(days=i*30)
        month_label = future_date.strftime('%b %Y')
        monthly_inflow = gross_salary
        total_monthly_outflow = total_fixed_structural_outflow + total_monthly_utilities + total_monthly_goal_sinking + simulated_spend + investing_target
        
        simulated_liquid_cash += (monthly_inflow - total_monthly_outflow)
        runway_projection.append({"Month": month_label, "Projected Liquid Buffer": max(0.0, simulated_liquid_cash), "Safety Threshold Baseline": 30000.0})
        
    runway_df = pd.DataFrame(runway_projection)
    fig_runway = px.line(runway_df, x="Month", y=["Projected Liquid Buffer", "Safety Threshold Baseline"], color_discrete_sequence=["#00CC96", "#EF553B"])
    fig_runway.update_layout(margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_runway, use_container_width=True)
    
    if runway_df.iloc[-1]["Projected Liquid Buffer"] < 30000.0:
        st.error("🚨 **Runway Alert:** Combined expenditures will breach minimal safety limits within 6 months.")
    else:
        st.success("✅ **Runway Stable:** Cash liquidity reserves remain protected.")

# ------------------------------------------
# TAB 3: TAX OPTIMIZATION MATRIX
# ------------------------------------------
with tab_tax:
    st.subheader("Tax Optimization Shield")
    
    max_80c_limit = 150000.0
    current_80c = st.number_input("Current FY Section 80C Contributions:", min_value=0.0, value=85000.0, step=5000.0)
    
    remaining_room = max(0.0, max_80c_limit - current_80c)
    st.progress(min(current_80c / max_80c_limit, 1.0))
    st.caption(f"**Exemption Space Used:** ₹{current_80c:,.0f} / ₹{max_80c_limit:,.0f}")
    
    st.markdown("---")
    st.markdown("#### 🧠 Optimization Instructions")
    target_debt_allocation = investing_target * get_target_weights(risk_profile)["Debt/Fixed Income"]
    if remaining_room > 0:
        st.info(f"**Action Plan:** Tax limit shortfall is **₹{remaining_room:,.0f}**. Route this month's fixed income strategy tranche (**₹{target_debt_allocation:,.0f}**) directly into PPF/ELSS setups.")
    else:
        st.success("🎉 Section 80C optimization constraints completed for this year tracking loop.")

# ------------------------------------------
# TAB 4: LOCAL TRANSACTION LEDGER
# ------------------------------------------
with tab_ledger:
    st.subheader("Secure SQLite Ingestion Engine")
    
    l_col1, l_col2 = st.columns([1, 2])
    with l_col1:
        with st.expander("📝 Log a New Transaction", expanded=True):
            with st.form("ledger_form_universal", clear_on_submit=True):
                tx_date = st.date_input("Date", datetime.today())
                tx_desc = st.text_input("Merchant/Item Description")
                tx_cat = st.selectbox("Category", ["Essentials (Needs)", "Discretionary (Wants)"])
                tx_amt = st.number_input("Amount (INR)", min_value=0.0, step=50.0)
                
                if st.form_submit_button("Commit Entry", use_container_width=True) and tx_desc:
                    save_expense_to_db(tx_date.strftime('%Y-%m-%d'), tx_desc, tx_cat, tx_amt)
                    st.success("Logged successfully!")
                    st.rerun()
                    
    with l_col2:
        st.markdown("#### Historical Expenses Log")
        live_df = load_expenses_from_db()
        if not live_df.empty:
            st.dataframe(live_df[["date", "description", "amount"]], use_container_width=True, hide_index=True)
            
            grp = live_df.groupby("category")["amount"].sum().reset_index()
            spent_ess = grp[grp["category"] == "Essentials (Needs)"]["amount"].values[0] if "Essentials (Needs)" in grp["category"].values else 0.0
            spent_wnt = grp[grp["category"] == "Discretionary (Wants)"]["amount"].values[0] if "Discretionary (Wants)" in grp["category"].values else 0.0
            
            st.markdown("---")
            st.write(f"**Essentials Budget Velocity:** Spent ₹{spent_ess:,.0f} of ₹{essentials_target:,.0f}")
            st.progress(min(spent_ess / essentials_target, 1.0) if essentials_target > 0 else 0.0)
            
            st.write(f"**Discretionary Budget Velocity:** Spent ₹{spent_wnt:,.0f} of ₹{net_discretionary_guilt_free:,.0f}")
            st.progress(min(spent_wnt / net_discretionary_guilt_free, 1.0) if net_discretionary_guilt_free > 0 else 0.0)
        else:
            st.info("Database transaction ledger is empty.")

# ------------------------------------------
# TAB 5: PAYDAY EXECUTION ROOM
# ------------------------------------------
with tab_payday:
    st.subheader("Investment Deployment Terminal")
    
    weights_map = get_target_weights(risk_profile)
    
    st.markdown("#### Core System Task Matrix")
    st.session_state.sip_checklist["Equity SIP Target"] = st.checkbox(f"Core Equity ETFs — Target: ₹{investing_target * weights_map['Equity']:,.0f}", value=st.session_state.sip_checklist.get("Equity SIP Target", False))
    st.session_state.sip_checklist["Debt SIP Target"] = st.checkbox(f"Tax Safe Debt Sweep — Target: ₹{investing_target * weights_map['Debt/Fixed Income']:,.0f}", value=st.session_state.sip_checklist.get("Debt SIP Target", False))
    st.session_state.sip_checklist["Liquid Buffer Topup"] = st.checkbox(f"Liquid Cash Cushion — Target: ₹{investing_target * weights_map['Emergency/Liquid']:,.0f}", value=st.session_state.sip_checklist.get("Liquid Buffer Topup", False))
    
    st.markdown("#### Milestone Runrate Sweeps")
    for goal in calculated_goals_list:
        st.session_state.sip_checklist[goal["Name"]] = st.checkbox(f"Sweep for *{goal['Name']}* ➡️ Route: **₹{goal['Runrate/Mo']:,.0f}**", value=st.session_state.sip_checklist.get(goal["Name"], False))
        
    st.markdown("---")
    done_count = sum(st.session_state.sip_checklist.values())
    total_count = len(st.session_state.sip_checklist)
    st.metric("Total Executed Items", f"{done_count} / {total_count}")
    
    if done_count == total_count and total_count > 0:
        st.balloons()
        st.success("All strategic targets executed successfully!")
        
    if st.button("Archive Snapshot Entry Record", use_container_width=True):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        month_key = datetime.today().strftime('%Y-%m')
        portfolio_total = sum(st.session_state.portfolio_holdings.values())
        
        cursor.execute("""
            INSERT OR REPLACE INTO historical_snapshots (month, net_salary, structural_outflows, total_invested, portfolio_value)
            VALUES (?, ?, ?, ?, ?)
        """, (month_key, gross_salary, total_fixed_structural_outflow, investing_target, portfolio_total))
        conn.commit()
        conn.close()
        st.success(f"Snapshot locked for {month_key}!")