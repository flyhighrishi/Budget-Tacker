import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime, timedelta

# ==========================================
# 1. PAGE CONFIGURATION & LAYOUT OPTIMIZATION
# ==========================================
st.set_page_config(page_title="Personal Wealth Engine v4", layout="wide")

st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
        }
        header[data-testid="stHeader"] {
            height: 1.5rem !important;
        }
        div[data-testid="stTabNavTabs"] {
            padding-top: 0rem !important;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATABASE LAYER & CORE INITIALIZATION
# ==========================================
DB_FILE = "wealth.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Expense ledger table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            description TEXT,
            category TEXT,
            amount REAL
        )
    """)
    # Historical net worth snapshot table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historical_snapshots (
            month TEXT PRIMARY KEY,
            net_salary REAL,
            structural_outflows REAL,
            total_invested REAL,
            portfolio_value REAL
        )
    """)
    # 🆕 Permanent Goals Table
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
    # Seed historical mock data if empty
    cursor.execute("SELECT COUNT(*) FROM historical_snapshots")
    if cursor.fetchone()[0] == 0:
        mock_history = [
            ("2026-01", 150000.0, 44000.0, 21200.0, 480000.0),
            ("2026-02", 150000.0, 44000.0, 21200.0, 502000.0),
            ("2026-03", 150000.0, 44000.0, 21200.0, 515000.0),
            ("2026-04", 150000.0, 44000.0, 21200.0, 540000.0),
        ]
        cursor.executemany("INSERT OR REPLACE INTO historical_snapshots VALUES (?,?,?,?,?)", mock_history)
    
    # Seed starter goals if table is empty
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
# 3. DATABASE READING & WRITING UTILITIES
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
# 4. SIDEBAR MASTER CONTROL DECK
# ==========================================
st.sidebar.header("🎯 Master Control Deck")
gross_salary = st.sidebar.number_input("Monthly Net Salary (INR):", min_value=0, value=150000, step=5000)

st.sidebar.subheader("🪓 Monthly Loan EMIs")
home_loan_emi = st.sidebar.number_input("Home Loan EMI (INR):", min_value=0, value=35000, step=1000)
personal_loan_emi = st.sidebar.number_input("Personal Loan EMI (INR):", min_value=0, value=8000, step=500)

st.sidebar.subheader("🚰 Fixed Utilities & Taxes")
electricity_bill = st.sidebar.number_input("Avg Electricity Bill / Month (INR):", min_value=0, value=3500, step=500)
water_bill = st.sidebar.number_input("Avg Water Bill / Month (INR):", min_value=0, value=500, step=100)
annual_property_tax = st.sidebar.number_input("Annual Property Tax (INR):", min_value=0, value=12000, step=1000)

# Struct Calculations
monthly_property_tax_cushion = annual_property_tax / 12
total_fixed_structural_outflow = home_loan_emi + personal_loan_emi + monthly_property_tax_cushion
disposable_income_pool = max(0, gross_salary - total_fixed_structural_outflow)
total_monthly_utilities = electricity_bill + water_bill

risk_profile = st.sidebar.selectbox("Risk Appetite Strategy:", ["Conservative", "Moderate", "Aggressive"], index=1)

# Fetch Dynamic Milestones list from DB
active_milestones = load_goals_from_db()

# Goal runtime processing
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
        "Saved Pool (INR)": goal["saved"],
        "Months Left": months_remaining,
        "Required Runrate / Mo": runrate
    })

# Framework Budget outputs
essentials_target = disposable_income_pool * 0.50
gross_discretionary = disposable_income_pool * 0.30
investing_target = disposable_income_pool * 0.20
net_discretionary_guilt_free = max(0.0, gross_discretionary - total_monthly_goal_sinking)

# ==========================================
# 5. WORKSPACE TABS DECK
# ==========================================
st.title("💸 Personal Finance Workspace & Intelligence Center")
st.markdown("---")

tab_dashboard, tab_runway, tab_tax, tab_ledger, tab_payday = st.tabs([
    "📊 Monthly Overview Dashboard",
    "🔮 Predictive Cash Flow Runway",
    "🛡️ Tax Optimization Matrix",
    "🛒 Local Transaction Ledger",
    "📈 Payday Execution Room"
])

# ------------------------------------------
# TAB 1: MONTHLY OVERVIEW DASHBOARD
# ------------------------------------------
with tab_dashboard:
    st.subheader("Current Month Capital Architecture")
    
    d_col1, d_col2, d_col3, d_col4 = st.columns(4)
    d_col1.metric("Fixed Structural Outflows", f"₹{total_fixed_structural_outflow:,.2f}")
    d_col2.metric("Essentials Pool (50%)", f"₹{essentials_target:,.2f}")
    d_col3.metric("Goal Sinking Provisions", f"₹{total_monthly_goal_sinking:,.2f}")
    d_col4.metric("Guilt-Free Spending Cash", f"₹{net_discretionary_guilt_free:,.2f}")
    
    st.markdown("---")
    
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("#### Complete Salary Capital Allocation")
        alloc_map = {
            "Structural Loan EMIs": home_loan_emi + personal_loan_emi,
            "Property Tax Sinking Funds": monthly_property_tax_cushion,
            "Fixed Utility Outlays": total_monthly_utilities,
            "Remaining Operational Essentials": max(0.0, essentials_target - total_monthly_utilities),
            "Active Goal Allocations": total_monthly_goal_sinking,
            "Net Discretionary Runway": net_discretionary_guilt_free,
            "Strategic Investment Tranche": investing_target
        }
        st.plotly_chart(px.pie(names=list(alloc_map.keys()), values=list(alloc_map.values()), color_discrete_sequence=px.colors.qualitative.Pastel), use_container_width=True)
        
    with chart_col2:
        st.markdown("#### Sinking Goals Tracking Index")
        if calculated_goals_list:
            st.dataframe(pd.DataFrame(calculated_goals_list), use_container_width=True, hide_index=True)
            for g in calculated_goals_list:
                pct = min(g["Saved Pool (INR)"] / g["Target (INR)"], 1.0)
                st.caption(f"**{g['Name']}** Progress: {pct*100:.1f}% (Required: ₹{g['Required Runrate / Mo']:,.2f}/mo)")
                st.progress(pct)
        else:
            st.info("No active milestones logged yet.")

    # 🆕 NEW SECTION: ADD MILESTONES ON THE GO
    st.markdown("---")
    st.subheader("✨ Create a New Financial Milestone On the Go")
    
    with st.form("new_milestone_form", clear_on_submit=True):
        g_col1, g_col2, g_col3, g_col4 = st.columns(4)
        new_g_name = g_col1.text_input("Milestone Goal Name (e.g., Electric Scooter, Emergency Fund)")
        new_g_target = g_col2.number_input("Target Amount (INR)", min_value=0.0, value=50000.0, step=5000.0)
        new_g_saved = g_col3.number_input("Initial Saved Seed Capital (INR)", min_value=0.0, value=0.0, step=1000.0)
        new_g_date = g_col4.date_input("Target Timeline Target Date", datetime.today() + timedelta(days=365))
        
        if st.form_submit_button("Add Milestone to System Architecture"):
            if new_g_name:
                formatted_date = new_g_date.strftime('%Y-%m-%d')
                success = save_goal_to_db(new_g_name, new_g_target, new_g_saved, formatted_date)
                if success:
                    st.success(f"✨ Milestone '{new_g_name}' successfully added into SQLite backend memory! Recalculating allocations...")
                    st.rerun()
                else:
                    st.error("❌ A milestone with that exact identifier name already exists in the local database.")
            else:
                st.warning("⚠️ Please provide a name description for the target milestone goal.")

# ------------------------------------------
# TAB 2: PREDICTIVE CASH FLOW RUNWAY
# ------------------------------------------
with tab_runway:
    st.subheader("6-Month Liquidity Forecast Model")
    st.write("This engine analyzes your fixed expenditures alongside your spending rate to project cash flow sustainability trends.")
    
    expenses_df = load_expenses_from_db()
    current_month_str = datetime.today().strftime('%Y-%m')
    current_month_expenses = expenses_df[expenses_df['date'].str.startswith(current_month_str)] if not expenses_df.empty else pd.DataFrame()
    avg_monthly_discretionary_spend = current_month_expenses[current_month_expenses['category'] == "Discretionary (Wants)"]['amount'].sum() if not current_month_expenses.empty else 15000.0
    
    spending_multiplier = st.slider("Simulate Variable Discretionary Spending Velocity:", min_value=0.5, max_value=2.0, value=1.0, step=0.1)
    simulated_spend = avg_monthly_discretionary_spend * spending_multiplier
    
    runway_projection = []
    simulated_liquid_cash = st.session_state.portfolio_holdings["Emergency/Liquid"]
    
    for i in range(1, 7):
        future_date = datetime.today() + timedelta(days=i*30)
        month_label = future_date.strftime('%b %Y')
        monthly_inflow = gross_salary
        total_monthly_outflow = total_fixed_structural_outflow + total_monthly_utilities + total_monthly_goal_sinking + simulated_spend + investing_target
        
        simulated_liquid_cash += (monthly_inflow - total_monthly_outflow)
        runway_projection.append({"Month": month_label, "Projected Liquid Buffer": max(0.0, simulated_liquid_cash), "Safety Threshold Floor": 30000.0})
        
    runway_df = pd.DataFrame(runway_projection)
    fig_runway = px.line(runway_df, x="Month", y=["Projected Liquid Buffer", "Safety Threshold Floor"], labels={"value": "Amount (INR)"}, color_discrete_sequence=["#00CC96", "#EF553B"])
    st.plotly_chart(fig_runway, use_container_width=True)
    
    if runway_df.iloc[-1]["Projected Liquid Buffer"] < 30000.0:
        st.error(f"🚨 **Runway Warning:** Your simulated spending pace (₹{simulated_spend:,.2f}/mo) combined with recurring debt will breach your cash reserve limits within 6 months.")
    else:
        st.success("✅ **Runway Safe:** Cash reserves remain stable and well above your minimum security baseline.")

# ------------------------------------------
# TAB 3: TAX OPTIMIZATION MATRIX
# ------------------------------------------
with tab_tax:
    st.subheader("Tax Compliance & Optimization Shield")
    tax_col1, tax_col2 = st.columns([2, 1])
    
    with tax_col1:
        st.markdown("#### Section 80C Investment Maximization")
        max_80c_limit = 150000.0
        current_80c = st.number_input("Enter current Financial Year Section 80C contributions (PPF, ELSS, EPF, etc):", min_value=0.0, value=85000.0, step=5000.0)
        
        remaining_room = max(0.0, max_80c_limit - current_80c)
        st.progress(min(current_80c / max_80c_limit, 1.0))
        st.caption(f"**Exemption Space Used:** ₹{current_80c:,.2f} / ₹{max_80c_limit:,.2f}")
        
    with tax_col2:
        st.markdown("#### 🧠 Optimization Instructions")
        target_debt_allocation = investing_target * get_target_weights(risk_profile)["Debt/Fixed Income"]
        if remaining_room > 0:
            st.info(f"**Action Plan:** You have a tax-saving shortfall of **₹{remaining_room:,.2f}**. Consider deploying this month's fixed income tranche (**₹{target_debt_allocation:,.2f}**) directly into Public Provident Fund (PPF) or ELSS mutual schemes to lower your tax liability.")
        else:
            st.success("🎉 Section 80C limits are maximized for the current financial cycle!")

# ------------------------------------------
# TAB 4: LOCAL TRANSACTION LEDGER
# ------------------------------------------
with tab_ledger:
    st.subheader("Secure SQLite Expense Ingestion")
    l_col1, l_col2 = st.columns([1, 2])
    
    with l_col1:
        st.markdown("#### Log New Transaction")
        with st.form("ledger_form", clear_on_submit=True):
            tx_date = st.date_input("Transaction Date", datetime.today())
            tx_desc = st.text_input("Merchant/Item Description")
            tx_cat = st.selectbox("Category Bucket", ["Essentials (Needs)", "Discretionary (Wants)"])
            tx_amt = st.number_input("Amount (INR)", min_value=0.0, step=50.0)
            
            if st.form_submit_button("Write to Database") and tx_desc:
                save_expense_to_db(tx_date.strftime('%Y-%m-%d'), tx_desc, tx_cat, tx_amt)
                st.success("Transaction securely written to SQLite file!")
                st.rerun()
                
    with l_col2:
        st.markdown("#### Historical Expenses Log")
        live_df = load_expenses_from_db()
        if not live_df.empty:
            st.dataframe(live_df[["date", "description", "category", "amount"]], use_container_width=True, hide_index=True)
            
            grp = live_df.groupby("category")["amount"].sum().reset_index()
            spent_ess = grp[grp["category"] == "Essentials (Needs)"]["amount"].values[0] if "Essentials (Needs)" in grp["category"].values else 0.0
            spent_wnt = grp[grp["category"] == "Discretionary (Wants)"]["amount"].values[0] if "Discretionary (Wants)" in grp["category"].values else 0.0
            
            st.write(f"**Essentials Budget Velocity:** Spent ₹{spent_ess:,.2f} of ₹{essentials_target:,.2f}")
            st.progress(min(spent_ess / essentials_target, 1.0) if essentials_target > 0 else 0.0)
            
            st.write(f"**Discretionary Budget Velocity:** Spent ₹{spent_wnt:,.2f} of ₹{net_discretionary_guilt_free:,.2f}")
            st.progress(min(spent_wnt / net_discretionary_guilt_free, 1.0) if net_discretionary_guilt_free > 0 else 0.0)
        else:
            st.info("No transaction velocity records currently stored in the database.")

# ------------------------------------------
# TAB 5: PAYDAY EXECUTION ROOM
# ------------------------------------------
with tab_payday:
    st.subheader("System Investment Deployment Terminal")
    st.write("Check items off once you execute your transfers on your external investment platform.")
    
    p_room1, p_room2 = st.columns([2, 1])
    with p_room1:
        st.markdown("#### Open Action Requirements")
        weights_map = get_target_weights(risk_profile)
        
        st.session_state.sip_checklist["Equity Core Index Target"] = st.checkbox(f"Execute Core Equity ETF / Nifty BEES Deployment — Target: ₹{investing_target * weights_map['Equity']:,.2f}", value=st.session_state.sip_checklist.get("Equity Core Index Target", False))
        st.session_state.sip_checklist["Debt Core Target"] = st.checkbox(f"Execute Tax Optimized Fixed Income Deployment (PPF / Debt Scheme) — Target: ₹{investing_target * weights_map['Debt/Fixed Income']:,.2f}", value=st.session_state.sip_checklist.get("Debt Core Target", False))
        st.session_state.sip_checklist["Liquid Buffer Topup"] = st.checkbox(f"Top-up Cash Reserve Cushion — Target: ₹{investing_target * weights_map['Emergency/Liquid']:,.2f}", value=st.session_state.sip_checklist.get("Liquid Buffer Topup", False))
        
        st.markdown("#### Goal Sinking Fund Deployments")
        for goal in calculated_goals_list:
            st.session_state.sip_checklist[goal["Name"]] = st.checkbox(f"Transfer Target Runrate for *{goal['Name']}* ➡️ Move **₹{goal['Required Runrate / Mo']:,.2f}** to structural goal account.", value=st.session_state.sip_checklist.get(goal["Name"], False))
            
    with p_room2:
        st.markdown("#### Finalize & Snapshot Records")
        done_count = sum(st.session_state.sip_checklist.values())
        total_count = len(st.session_state.sip_checklist)
        st.metric("Deployment Tasks Finalized", f"{done_count} / {total_count}")
        
        if done_count == total_count and total_count > 0:
            st.balloons()
            st.success("Strategic configurations executed perfectly!")
            
        st.markdown("---")
        if st.button("Archive Current Month Financial Snapshot"):
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
            st.success(f"Snapshot compiled successfully inside local database archive for month reference ({month_key})!")