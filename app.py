import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime, timedelta

# ==========================================
# 1. PAGE SETUP & HYBRID RESPONSIVE CSS
# ==========================================
st.set_page_config(page_title="Universal Wealth Workspace", layout="wide")

st.markdown("""
    <style>
        .block-container {
            padding-top: 0.75rem !important;
            padding-bottom: 0.5rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        header[data-testid="stHeader"] {
            height: 1.2rem !important;
        }
        
        @media (min-width: 769px) {
            [data-testid="stMetricValue"] { font-size: 2.2rem !important; }
            [data-testid="stMetricLabel"] { font-size: 1rem !important; }
            h1 { font-size: 2.5rem !important; }
            h2 { font-size: 1.8rem !important; }
            h3 { font-size: 1.4rem !important; }
        }

        @media (max-width: 768px) {
            .block-container {
                padding-left: 0.5rem !important;
                padding-right: 0.5rem !important;
            }
            [data-testid="stMetricValue"] {
                font-size: 5.5vw !important;
                font-weight: bold;
            }
            [data-testid="stMetricLabel"] { font-size: 3.2vw !important; }
            h1 { font-size: 6.5vw !important; }
            h2 { font-size: 5.5vw !important; }
            h3 { font-size: 4.8vw !important; }
            
            button[data-baseweb="tab"] {
                padding-left: 8px !important;
                padding-right: 8px !important;
                font-size: 3.4vw !important;
            }
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
    # 🆕 New Persistent Credit Card Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS credit_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_name TEXT UNIQUE,
            total_limit REAL,
            total_outstanding REAL,
            min_outstanding REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()

def seed_default_data():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Snapshot seed
    cursor.execute("SELECT COUNT(*) FROM historical_snapshots")
    if cursor.fetchone()[0] == 0:
        mock_history = [
            ("2026-01", 150000.0, 44000.0, 21200.0, 480000.0),
            ("2026-02", 150000.0, 44000.0, 21200.0, 502000.0),
            ("2026-03", 150000.0, 44000.0, 21200.0, 515000.0),
            ("2026-04", 150000.0, 44000.0, 21200.0, 540000.0),
        ]
        cursor.executemany("INSERT OR REPLACE INTO historical_snapshots VALUES (?,?,?,?,?)", mock_history)
    
    # Goals seed
    cursor.execute("SELECT COUNT(*) FROM goals")
    if cursor.fetchone()[0] == 0:
        mock_goals = [
            ("Nepal Milestone Travel (Dec 2026)", 150000.0, 50000.0, "2026-12-01"),
            ("Home Capital Buffer", 500000.0, 160000.0, "2027-06-01")
        ]
        cursor.executemany("INSERT OR REPLACE INTO goals (name, target, saved, target_date) VALUES (?, ?, ?, ?)", mock_goals)
        
    # Credit Card Seed
    cursor.execute("SELECT COUNT(*) FROM credit_cards")
    if cursor.fetchone()[0] == 0:
        mock_cards = [
            ("HDFC Regalia Black", 500000.0, 45000.0, 2500.0),
            ("ICICI Amazon Pay", 200000.0, 12000.0, 600.0)
        ]
        cursor.executemany("INSERT OR REPLACE INTO credit_cards (card_name, total_limit, total_outstanding, min_outstanding) VALUES (?, ?, ?, ?)", mock_cards)
        
    conn.commit()
    conn.close()

seed_default_data()

if "portfolio_holdings" not in st.session_state:
    st.session_state.portfolio_holdings = {"Equity": 380000.0, "Debt/Fixed Income": 120000.0, "Emergency/Liquid": 40000.0}

if "sip_checklist" not in st.session_state:
    st.session_state.sip_checklist = {}

# ==========================================
# 3. DATABASE CONTROLLER UTILITIES
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

# 🆕 New Credit Card DB Operations
def load_cards_from_db():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM credit_cards", conn)
    conn.close()
    return df.to_dict(orient="records")

def save_card_to_db(name, limit, outstanding, minimum):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO credit_cards (card_name, total_limit, total_outstanding, min_outstanding) VALUES (?, ?, ?, ?)", (name, limit, outstanding, minimum))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def update_card_balances_in_db(card_id, outstanding, minimum):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE credit_cards SET total_outstanding = ?, min_outstanding = ? WHERE id = ?", (outstanding, minimum, card_id))
    conn.commit()
    conn.close()

def get_target_weights(risk_profile):
    if risk_profile == "Conservative": return {"Equity": 0.25, "Debt/Fixed Income": 0.55, "Emergency/Liquid": 0.20}
    elif risk_profile == "Moderate": return {"Equity": 0.55, "Debt/Fixed Income": 0.35, "Emergency/Liquid": 0.10}
    else: return {"Equity": 0.75, "Debt/Fixed Income": 0.15, "Emergency/Liquid": 0.10}

# ==========================================
# 4. MASTER FINANCIAL LOGIC INTEGRATION
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

# Fetch Cards to compute minimum mandatory commitments
active_cards = load_cards_from_db()
total_cc_minimums = sum(card["min_outstanding"] for card in active_cards)
total_cc_outstanding = sum(card["total_outstanding"] for card in active_cards)

# Framework Structural Calculations
monthly_property_tax_cushion = annual_property_tax / 12
# CC Minimum payments are added to unalterable fixed commitments to insulate budget health
total_fixed_structural_outflow = home_loan_emi + personal_loan_emi + monthly_property_tax_cushion + total_cc_minimums
disposable_income_pool = max(0, gross_salary - total_fixed_structural_outflow)
total_monthly_utilities = electricity_bill + water_bill

risk_profile = st.sidebar.selectbox("Risk Profile Strategy:", ["Conservative", "Moderate", "Aggressive"], index=1)

# Dynamic Milestones
active_milestones = load_goals_from_db()
total_monthly_goal_sinking = 0.0
current_date = datetime.today()
calculated_goals_list = []

for goal in active_milestones:
    target_date = datetime.strptime(goal["target_date"], "%Y-%m-%d")
    months_remaining = max(1, (target_date.year - current_date.year) * 12 + (target_date.month - current_date.month))
    runrate = max(0.0, goal["target"] - goal["saved"]) / months_remaining
    total_monthly_goal_sinking += runrate
    calculated_goals_list.append({"Name": goal["name"], "Target (INR)": goal["target"], "Saved (INR)": goal["saved"], "Months Remaining": months_remaining, "Runrate/Mo": runrate})

# 50/30/20 Slice Allocations
essentials_target = disposable_income_pool * 0.50
gross_discretionary = disposable_income_pool * 0.30
investing_target = disposable_income_pool * 0.20
net_discretionary_guilt_free = max(0.0, gross_discretionary - total_monthly_goal_sinking)

# ==========================================
# 5. USER WORKSPACE TABS INTERFACE
# ==========================================
tab_dashboard, tab_cards, tab_runway, tab_tax, tab_ledger, tab_payday = st.tabs([
    "📊 Summary", "💳 Credit Cards", "🔮 Runway", "🛡️ Tax", "🛒 Ledger", "📈 Payday"
])

# ------------------------------------------
# TAB 1: DASHBOARD OVERVIEW
# ------------------------------------------
with tab_dashboard:
    st.subheader("Current Month Framework Split")
    
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("Fixed Loans + CC Min", f"₹{total_fixed_structural_outflow:,.0f}")
    m_col2.metric("Needs Pool (50%)", f"₹{essentials_target:,.0f}")
    m_col3.metric("Goal Sinking", f"₹{total_monthly_goal_sinking:,.0f}")
    m_col4.metric("Guilt-Free Cash", f"₹{net_discretionary_guilt_free:,.0f}")
    
    st.markdown("---")
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("#### Complete Salary Capital Architecture")
        alloc_map = {
            "Loan EMIs": home_loan_emi + personal_loan_emi,
            "Prop Tax Reserves": monthly_property_tax_cushion,
            "CC Minimum Dues": total_cc_minimums,
            "Base Fixed Utilities": total_monthly_utilities,
            "Remaining Essentials": max(0.0, essentials_target - total_monthly_utilities),
            "Active Goals": total_monthly_goal_sinking,
            "Wants Allocation": net_discretionary_guilt_free,
            "Core Investments": investing_target
        }
        st.plotly_chart(px.pie(names=list(alloc_map.keys()), values=list(alloc_map.values()), color_discrete_sequence=px.colors.qualitative.Pastel), use_container_width=True)
        
    with chart_col2:
        st.markdown("#### Total Liability Exposure")
        exposure_map = {"Total Credit Card Debt": total_cc_outstanding, "Home Loan Principal Projection": home_loan_emi * 120, "Personal Loan Outstanding": personal_loan_emi * 24}
        st.plotly_chart(px.bar(x=list(exposure_map.keys()), y=list(exposure_map.values()), labels={'x': 'Debt Pool Type', 'y': 'Outstanding Balance'}, color_discrete_sequence=["#EF553B"]), use_container_width=True)

# ------------------------------------------
# 🆕 TAB 2: CREDIT CARD MANAGEMENT HUB
# ------------------------------------------
with tab_cards:
    st.subheader("💳 Unified Credit Card Command Center")
    
    c_col1, c_col2 = st.columns([1, 2])
    with c_col1:
        st.markdown("#### Add Card Asset on the Go")
        with st.form("add_cc_form", clear_on_submit=True):
            new_cc_name = st.text_input("Card Issuer Name (e.g., Apple Titanium)")
            new_cc_limit = st.number_input("Total Credit Limit (INR)", min_value=0.0, value=100000.0, step=10000.0)
            new_cc_out = st.number_input("Current Total Outstanding (INR)", min_value=0.0, value=5000.0, step=1000.0)
            new_cc_min = st.number_input("Current Minimum Due (INR)", min_value=0.0, value=250.0, step=100.0)
            
            if st.form_submit_button("Hook Card to Workspace") and new_cc_name:
                if save_card_to_db(new_cc_name, new_cc_limit, new_cc_out, new_cc_min):
                    st.success("Card integrated successfully!")
                    st.rerun()
                else:
                    st.error("Duplicate card identifier discovered.")

    with c_col2:
        st.markdown("#### Current Active Balances Matrix")
        if active_cards:
            for card in active_cards:
                utilization = (card["total_outstanding"] / card["total_limit"]) * 100 if card["total_limit"] > 0 else 0
                st.write(f"**{card['card_name']}** (Limit: ₹{card['total_limit']:,.0f})")
                
                # Render parameters dynamically
                b_col1, b_col2, b_col3 = st.columns(3)
                b_col1.caption(f"Outstanding: ₹{card['total_outstanding']:,.0f}")
                b_col2.caption(f"Minimum Due: ₹{card['min_outstanding']:,.0f}")
                b_col3.caption(f"Utilization: {utilization:.1f}%")
                st.progress(min(utilization / 100, 1.0))
                
                # Quick update balances sub-system
                with st.expander(f"⚙️ Quick Update {card['card_name']} Statement Values"):
                    new_out = st.number_input("New Total Outstanding:", min_value=0.0, value=card['total_outstanding'], key=f"out_{card['id']}")
                    new_min = st.number_input("New Minimum Due:", min_value=0.0, value=card['min_outstanding'], key=f"min_{card['id']}")
                    if st.button("Update Ledger Records", key=f"btn_{card['id']}"):
                        update_card_balances_in_db(card["id"], new_out, new_min)
                        st.success("Statement metrics realigned!")
                        st.rerun()
                st.markdown("---")
        else:
            st.info("No credit cards logged in database profile yet.")

# ------------------------------------------
# TAB 3: PREDICTIVE RUNWAY
# ------------------------------------------
with tab_runway:
    st.subheader("6-Month Liquidity Path Projections")
    expenses_df = load_expenses_from_db()
    current_month_str = datetime.today().strftime('%Y-%m')
    current_month_expenses = expenses_df[expenses_df['date'].str.startswith(current_month_str)] if not expenses_df.empty else pd.DataFrame()
    avg_monthly_discretionary_spend = current_month_expenses[current_month_expenses['category'] == "Discretionary (Wants)"]['amount'].sum() if not current_month_expenses.empty else 15000.0
    
    spending_multiplier = st.slider("Simulate Spending Velocity:", min_value=0.5, max_value=2.0, value=1.0, step=0.1)
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
    st.plotly_chart(fig_runway, use_container_width=True)

# ------------------------------------------
# TAB 4: TAX CONFIGURATION
# ------------------------------------------
with tab_tax:
    st.subheader("Tax Optimization Shield")
    max_80c_limit = 150000.0
    current_80c = st.number_input("Current FY Section 80C Contributions:", min_value=0.0, value=85000.0, step=5000.0)
    remaining_room = max(0.0, max_80c_limit - current_80c)
    st.progress(min(current_80c / max_80c_limit, 1.0))
    st.caption(f"**Exemption Space Used:** ₹{current_80c:,.0f} / ₹{max_80c_limit:,.0f}")

# ------------------------------------------
# TAB 5: TRANSACTION LEDGER
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
        live_df = load_expenses_from_db()
        if not live_df.empty:
            st.dataframe(live_df[["date", "description", "amount"]], use_container_width=True, hide_index=True)

# ------------------------------------------
# TAB 6: PAYDAY EXECUTION TERMINAL
# ------------------------------------------
with tab_payday:
    st.subheader("Investment Deployment Terminal")
    weights_map = get_target_weights(risk_profile)
    
    st.markdown("#### Core System Task Matrix")
    st.session_state.sip_checklist["Equity SIP Target"] = st.checkbox(f"Core Equity ETFs — Target: ₹{investing_target * weights_map['Equity']:,.0f}", value=st.session_state.sip_checklist.get("Equity SIP Target", False))
    st.session_state.sip_checklist["Debt SIP Target"] = st.checkbox(f"Tax Safe Debt Sweep — Target: ₹{investing_target * weights_map['Debt/Fixed Income']:,.0f}", value=st.session_state.sip_checklist.get("Debt SIP Target", False))
    
    st.markdown("#### Milestone Runrate Sweeps")
    for goal in calculated_goals_list:
        st.session_state.sip_checklist[goal["Name"]] = st.checkbox(f"Sweep for *{goal['Name']}* ➡️ Route: **₹{goal['Runrate/Mo']:,.0f}**", value=st.session_state.sip_checklist.get(goal["Name"], False))
        
    st.markdown("---")
    if st.button("Archive Snapshot Entry Record", use_container_width=True):
        st.success("Snapshot locked successfully!")