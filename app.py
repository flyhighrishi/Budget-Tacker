import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import math

# ==========================================
# 1. PAGE CONFIGURATION & SESSION STATE
# ==========================================
st.set_page_config(page_title="Personal Wealth Engine", layout="wide")

# Core ledger state
if "expenses" not in st.session_state:
    st.session_state.expenses = pd.DataFrame(columns=["Date", "Description", "Category", "Amount"])

# 🆕 Financial Goals Sinking Fund State
if "goals" not in st.session_state:
    st.session_state.goals = [
        {"Name": "Nepal Milestone Travel (Dec 2026)", "Target": 150000.0, "Saved": 40000.0, "Date": "2026-12-01"},
        {"Name": "Home Capital Buffer", "Target": 500000.0, "Saved": 150000.0, "Date": "2027-06-01"}
    ]

# 🆕 Current Investment Portfolio holdings for tracking asset drift
if "portfolio_holdings" not in st.session_state:
    st.session_state.portfolio_holdings = {
        "Equity": 380000.0,
        "Debt/Fixed Income": 120000.0,
        "Emergency/Liquid": 40000.0
    }

if "sip_checklist" not in st.session_state:
    st.session_state.sip_checklist = {}

# ==========================================
# 2. HELPER FUNCTIONS & MATH ENGINES
# ==========================================
def calculate_budget(base_disposable, monthly_utilities, total_goal_sinking_fund):
    """Calculates allocations and deducts goal sinking funds from discretionary pool."""
    total_essentials = base_disposable * 0.50
    gross_discretionary = base_disposable * 0.30
    investing = base_disposable * 0.20
    
    # Sinking funds drain directly from Discretionary (Wants) capacity
    net_discretionary = max(0.0, gross_discretionary - total_goal_sinking_fund)
    other_essentials_left = max(0.0, total_essentials - monthly_utilities)
    
    return {
        "Essentials (Needs)": total_essentials,
        "Gross Discretionary": gross_discretionary,
        "Goal Sinking Reserves": total_goal_sinking_fund,
        "Net Discretionary (Guilt-Free)": net_discretionary,
        "Investing (Savings)": investing,
        "_meta_other_essentials": other_essentials_left
    }

def get_target_weights(risk_profile):
    if risk_profile == "Conservative":
        return {"Equity": 0.25, "Debt/Fixed Income": 0.55, "Emergency/Liquid": 0.20}
    elif risk_profile == "Moderate":
        return {"Equity": 0.55, "Debt/Fixed Income": 0.35, "Emergency/Liquid": 0.10}
    else: # Aggressive
        return {"Equity": 0.75, "Debt/Fixed Income": 0.15, "Emergency/Liquid": 0.10}

# ==========================================
# 3. SIDEBAR CONTROLS (FINANCIAL PARAMETERS)
# ==========================================
st.sidebar.header("🎯 Financial Parameters")
gross_salary = st.sidebar.number_input("Monthly Net Salary (INR):", min_value=0, value=150000, step=5000)

st.sidebar.subheader("🪓 Fixed Monthly Debt Obligations")
home_loan_emi = st.sidebar.number_input("Home Loan EMI (INR):", min_value=0, value=35000, step=1000)
personal_loan_emi = st.sidebar.number_input("Personal Loan EMI (INR):", min_value=0, value=8000, step=500)

st.sidebar.subheader("🚰 Regular Utilities & Taxes")
electricity_bill = st.sidebar.number_input("Avg Electricity Bill / Month (INR):", min_value=0, value=3500, step=500)
water_bill = st.sidebar.number_input("Avg Water Bill / Month (INR):", min_value=0, value=500, step=100)
annual_property_tax = st.sidebar.number_input("Annual Property Tax (INR):", min_value=0, value=12000, step=1000)

# Structural Matrix Math
monthly_property_tax_cushion = annual_property_tax / 12
total_fixed_structural_outflow = home_loan_emi + personal_loan_emi + monthly_property_tax_cushion
disposable_income_pool = max(0, gross_salary - total_fixed_structural_outflow)
total_monthly_utilities = electricity_bill + water_bill

risk_profile = st.sidebar.selectbox("Risk Appetite Profile:", ["Conservative", "Moderate", "Aggressive"], index=1)

# ==========================================
# 4. 🆕 GOAL SINKING FUNDS CALCULATION ENGINE
# ==========================================
total_monthly_goal_sinking = 0.0
calculated_goals_list = []

current_date = datetime.today()

for goal in st.session_state.goals:
    target_date = datetime.strptime(goal["Date"], "%Y-%m-%d")
    # Calculate difference in months
    months_remaining = (target_date.year - current_date.year) * 12 + (target_date.month - current_date.month)
    months_remaining = max(1, months_remaining) # Avoid divide by zero or negative months
    
    amount_needed = max(0.0, goal["Target"] - goal["Saved"])
    monthly_allocation = amount_needed / months_remaining
    total_monthly_goal_sinking += monthly_allocation
    
    calculated_goals_list.append({
        "Name": goal["Name"],
        "Target": goal["Target"],
        "Saved": goal["Saved"],
        "Months Left": months_remaining,
        "Monthly Runrate": monthly_allocation
    })

# Evaluate Budgets
budget = calculate_budget(disposable_income_pool, total_monthly_utilities, total_monthly_goal_sinking)
target_weights = get_target_weights(risk_profile)
monthly_investment_bucket = budget["Investing (Savings)"]

# ==========================================
# 5. DASHBOARD LAYOUT & METRICS
# ==========================================
st.title("💸 Advanced Personal Wealth & Intelligent Rebalancing Dashboard")
st.markdown("---")

# High-Level System Metrics Row
m_col1, m_col2, m_col3, m_col4 = st.columns(4)
with m_col1:
    st.metric("Fixed Structural Outflows", f"₹{total_fixed_structural_outflow:,.2f}")
with m_col2:
    st.metric("Essentials Bucket (50%)", f"₹{budget['Essentials (Needs)']:,.2f}")
with m_col3:
    st.metric("Goal Sinking Deductions", f"₹{budget['Goal Sinking Reserves']:,.2f}", delta="Deducted from Wants", delta_color="inverse")
with m_col4:
    st.metric("Net Guilt-Free Wants (30%)", f"₹{budget['Net Discretionary (Guilt-Free)']:,.2f}")

st.markdown("---")

# Visual Structural Allocations
left_chart_col, right_chart_col = st.columns(2)
with left_chart_col:
    st.subheader("Total Salary Capital Breakdown")
    all_allocations = {
        "Debt Structural EMIs": home_loan_emi + personal_loan_emi,
        "Property Tax Cushion": monthly_property_tax_cushion,
        "Fixed Base Utilities": total_monthly_utilities,
        "Other Operational Essentials": budget["_meta_other_essentials"],
        "Goal Sinking Reserves": budget["Goal Sinking Reserves"],
        "Net Guilt-Free Cash": budget["Net Discretionary (Guilt-Free)"],
        "Systematic Core Investments": budget["Investing (Savings)"]
    }
    fig_budget = px.pie(names=list(all_allocations.keys()), values=list(all_allocations.values()), color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_budget, use_container_width=True)

with right_chart_col:
    st.subheader("💡 Dynamic Goal Sinking Ledger")
    goals_df = pd.DataFrame(calculated_goals_list)
    if not goals_df.empty:
        st.dataframe(goals_df[["Name", "Target", "Saved", "Months Left", "Monthly Runrate"]], use_container_width=True, hide_index=True)
        for g in calculated_goals_list:
            progress_pct = min(g["Saved"] / g["Target"], 1.0)
            st.caption(f"**{g['Name']}** Progress: {progress_pct*100:.1f}% (Need ₹{g['Monthly Runrate']:,.2f}/mo)")
            st.progress(progress_pct)

# ==========================================
# 6. 🆕 INTELLIGENT INVESTMENT REBALANCING MATRIX
# ==========================================
st.markdown("---")
st.header("🎯 Portfolio Health & Smart Rebalancing Engine")

# Portfolio Portfolio Allocation Evaluation
total_portfolio_value = sum(st.session_state.portfolio_holdings.values())
portfolio_analysis_data = []

st.subheader("Current Structural Portfolio Drift Analysis")
p_col1, p_col2 = st.columns([2, 1])

with p_col1:
    drift_alerts = []
    rebalance_suggestions = {}
    
    for asset, current_value in st.session_state.portfolio_holdings.items():
        actual_weight = current_value / total_portfolio_value if total_portfolio_value > 0 else 0.0
        target_weight = target_weights[asset]
        drift = actual_weight - target_weight
        
        portfolio_analysis_data.append({
            "Asset Class": asset,
            "Current Valuation": current_value,
            "Actual Weight": f"{actual_weight*100:.1f}%",
            "Target Weight": f"{target_weight*100:.1f}%",
            "Drift Variance": f"{drift*100:+.1f}%"
        })
        
        # Trigger insight conditions if drift variance exceeding thresholds (e.g. +/- 5%)
        if abs(drift) >= 0.05:
            direction = "OVERWEIGHT 📈" if drift > 0 else "UNDERWEIGHT 📉"
            drift_alerts.append(f"⚠️ **{asset}** class has drifted to **{actual_weight*100:.1f}%** (Target: {target_weight*100:.1f}%). It is currently **{direction}** by **{abs(drift)*100:.1f}%**.")
            
        # Strategy Recommendation Router
        if drift > 0:
            rebalance_suggestions[asset] = "Reduce new distribution inflow. Market appreciation has exceeded strategic target profiles."
        elif drift < 0:
            rebalance_suggestions[asset] = f"🎯 TARGET BUY: Divert a larger chunk of this month's ₹{monthly_investment_bucket:,.2f} savings pool to correct this shortfall."
        else:
            rebalance_suggestions[asset] = "Holding steady. Aligned perfectly with strategic risk matrix parameters."

    st.dataframe(pd.DataFrame(portfolio_analysis_data), use_container_width=True, hide_index=True)

with p_col2:
    st.metric("Total Tracked Net Asset Value (NAV)", f"₹{total_portfolio_value:,.2f}")
    fig_portfolio = px.pie(names=list(st.session_state.portfolio_holdings.keys()), values=list(st.session_state.portfolio_holdings.values()), color_discrete_sequence=px.colors.qualitative.Safe, hole=0.4)
    st.plotly_chart(fig_portfolio, use_container_width=True)

# Render Intelligent Action Insights Block
st.subheader("🧠 Automated Rebalancing Insights")
if drift_alerts:
    for alert in drift_alerts:
        st.info(alert)
        
    # Generate dynamic execution blueprint based on portfolio drift
    st.markdown("### 🛠️ Strategic Capital Deployment Adjustments for This Month:")
    adjusted_allocations = {}
    remaining_investment = monthly_investment_bucket
    
    # Simple rebalancing execution engine math
    underweight_assets = [a for a, v in target_weights.items() if (st.session_state.portfolio_holdings[a]/total_portfolio_value) < v]
    
    if underweight_assets:
        st.write("To naturally repair the structural portfolio drift without forcing asset liquidation, alter your monthly savings pool configuration to the following distribution:")
        for asset in target_weights.keys():
            if asset in underweight_assets:
                # Add extra weight premium to assets that are currently falling short
                adjusted_allocations[asset] = target_weights[asset] + 0.15 
            else:
                adjusted_allocations[asset] = max(0.05, target_weights[asset] - 0.15)
                
        # Normalize weights to exactly equal 1.0
        total_adj_w = sum(adjusted_allocations.values())
        adjusted_allocations = {k: (v / total_adj_w) * monthly_investment_bucket for k, v in adjusted_allocations.items()}
        
        for asset, amt in adjusted_allocations.items():
            st.success(f"👉 **Deploy to {asset}**: Allocate **₹{amt:,.2f}** (Standard target was ₹{monthly_investment_bucket * target_weights[asset]:,.2f})")
    else:
        st.write("Strategic target bands are uniform. Maintain standard target index rules.")
else:
    st.success("✅ Portfolio allocation health within acceptable parameters. No critical variance detected. Stick to baseline target models.")

# ==========================================
# 7. TRACKING & LEDGERS
# ==========================================
st.markdown("---")
st.header("🛒 Monthly Spending Ledgers")
exp1, exp2 = st.columns([1, 2])

with exp1:
    st.subheader("Log Manual Expense")
    with st.form("expense_form", clear_on_submit=True):
        exp_date = st.date_input("Transaction Date", datetime.today())
        exp_desc = st.text_input("Merchant/Description")
        exp_cat = st.selectbox("Target Allocation Bucket", ["Essentials (Needs)", "Discretionary (Wants)"])
        exp_amt = st.number_input("Amount (INR)", min_value=0.0, step=50.0)
        
        if st.form_submit_button("Log Transaction") and exp_desc:
            new_row = pd.DataFrame([{"Date": exp_date.strftime('%Y-%m-%d'), "Description": exp_desc, "Category": exp_cat, "Amount": exp_amt}])
            st.session_state.expenses = pd.concat([st.session_state.expenses, new_row], ignore_index=True)
            st.success("Transaction recorded.")

with exp2:
    st.subheader("Transaction Ledger")
    if not st.session_state.expenses.empty:
        st.dataframe(st.session_state.expenses, use_container_width=True, hide_index=True)
        summary_df = st.session_state.expenses.groupby("Category")["Amount"].sum().reset_index()
        
        st.subheader("Budget Velocity Tracker")
        for cat, b_amt in [("Essentials (Needs)", budget["Essentials (Needs)"]), ("Discretionary (Wants)", budget["Net Discretionary (Guilt-Free)"])]:
            spent = summary_df[summary_df["Category"] == cat]["Amount"].values[0] if cat in summary_df["Category"].values else 0.0
            remaining = b_amt - spent
            progress = min(spent / b_amt, 1.0) if b_amt > 0 else 0.0
            st.write(f"**{cat}**: Spent ₹{spent:,.2f} of ₹{b_amt:,.2f} ({remaining:,.2f} remaining)")
            st.progress(progress)
    else:
        st.info("No transaction velocity tracked yet for the current month.")

# ==========================================
# 8. PAYDAY EXECUTION CHECKLIST
# ==========================================
st.markdown("---")
st.header("📈 Payday Execution Blueprint")

chk1, chk2 = st.columns([2, 1])
with chk1:
    st.subheader("Action Item Checklist")
    
    # Set targets based on whether the rebalancing system adjusted weights or defaulted
    final_eq = adjusted_allocations.get("Equity", monthly_investment_bucket * target_weights["Equity"]) if 'adjusted_allocations' in locals() else (monthly_investment_bucket * target_weights["Equity"])
    final_debt = adjusted_allocations.get("Debt/Fixed Income", monthly_investment_bucket * target_weights["Debt/Fixed Income"]) if 'adjusted_allocations' in locals() else (monthly_investment_bucket * target_weights["Debt/Fixed Income"])
    final_liquid = adjusted_allocations.get("Emergency/Liquid", monthly_investment_bucket * target_weights["Emergency/Liquid"]) if 'adjusted_allocations' in locals() else (monthly_investment_bucket * target_weights["Emergency/Liquid"])

    st.session_state.sip_checklist["Equity SIP"] = st.checkbox(f"Execute Equity ETF/Fund Purchases — Recommended Target: ₹{final_eq:,.2f}", value=st.session_state.sip_checklist.get("Equity SIP", False))
    st.session_state.sip_checklist["Debt SIP"] = st.checkbox(f"Deploy Fixed Income / Debt Sweep — Recommended Target: ₹{final_debt:,.2f}", value=st.session_state.sip_checklist.get("Debt SIP", False))
    st.session_state.sip_checklist["Liquid Buffer"] = st.checkbox(f"Top-up Liquid Reserve Fund — Recommended Target: ₹{final_liquid:,.2f}", value=st.session_state.sip_checklist.get("Liquid Buffer", False))
    
    st.markdown("#### 🆕 Goal Sinking Allocations")
    for goal in calculated_goals_list:
        st.session_state.sip_checklist[goal["Name"]] = st.checkbox(f"Transfer Monthly Runrate for *{goal['Name']}* ➡️ Move **₹{goal['Monthly Runrate']:,.2f}** to structural savings.", value=st.session_state.sip_checklist.get(goal["Name"], False))

with chk2:
    st.subheader("System Confirmation")
    completed = sum(st.session_state.sip_checklist.values())
    total = len(st.session_state.sip_checklist)
    st.metric("Tasks Fully Deployed", f"{completed} / {total}")
    if completed == total and total > 0:
        st.balloons()
        st.success("Financial configuration optimized! Your wealth targets are aligned.")