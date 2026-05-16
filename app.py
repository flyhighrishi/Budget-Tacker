import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ==========================================
# 1. PAGE CONFIGURATION & SESSION STATE
# ==========================================
st.set_page_config(page_title="Personal Wealth Prototype", layout="wide")

if "expenses" not in st.session_state:
    st.session_state.expenses = pd.DataFrame(
        columns=["Date", "Description", "Category", "Amount"]
    )

if "cc_cards" not in st.session_state:
    st.session_state.cc_cards = {
        "HDFC Regalia": {"Total Outstanding": 45000.0, "Limit": 66000.0},
        "ICICI Amazon Pay": {"Total Outstanding": 12500.0, "Limit": 260000.0}
    }

if "sip_checklist" not in st.session_state:
    st.session_state.sip_checklist = {
        "Nifty BEES (Equity ETF)": False,
        "Flexi-cap Mutual Fund": False,
        "PPF / Debt Fund": False,
        "Liquid Emergency Buffer": False
    }

# ==========================================
# 2. CORE BUDGETING ENGINE LOGIC
# ==========================================
def calculate_budget(base_disposable, monthly_utilities):
    """
    Applies 50/30/20 rule on post-EMI income.
    Embeds monthly utility parameters directly into the 50% Essentials bucket.
    """
    total_essentials_target = base_disposable * 0.50
    
    # Remaining capacity for other essentials (Groceries, Insurance, etc.)
    other_essentials_left = max(0.0, total_essentials_target - monthly_utilities)
    
    return {
        "Essentials (Needs)": total_essentials_target,
        "Discretionary (Wants)": base_disposable * 0.30,
        "Investing (Savings)": base_disposable * 0.20,
        "_meta_utilities_absorbed": monthly_utilities,
        "_meta_other_essentials": other_essentials_left
    }

def allocate_investments(investing_amount, risk_profile):
    if risk_profile == "Conservative":
        weights = {"Equity": 0.25, "Debt/Fixed Income": 0.55, "Emergency/Liquid": 0.20}
    elif risk_profile == "Moderate":
        weights = {"Equity": 0.55, "Debt/Fixed Income": 0.35, "Emergency/Liquid": 0.10}
    else:  # Aggressive
        weights = {"Equity": 0.75, "Debt/Fixed Income": 0.15, "Emergency/Liquid": 0.10}
    return {k: investing_amount * v for k, v in weights.items()}

# ==========================================
# 3. SIDEBAR CONTROLS (INCOME, LOANS & UTILITIES)
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

# Calculations
monthly_property_tax_cushion = annual_property_tax / 12
total_fixed_structural_outflow = home_loan_emi + personal_loan_emi + monthly_property_tax_cushion
disposable_income_pool = max(0, gross_salary - total_fixed_structural_outflow)
total_monthly_utilities = electricity_bill + water_bill

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Structural Outflows (EMIs + Tax Sinking Fund):** ₹{total_fixed_structural_outflow:,.2f}")
st.sidebar.markdown(f"**Net Disposable Pool:** ₹{disposable_income_pool:,.2f}")

risk_profile = st.sidebar.selectbox("Risk Appetite Profile:", ["Conservative", "Moderate", "Aggressive"], index=1)

# Run Framework calculations
budget = calculate_budget(disposable_income_pool, total_monthly_utilities)
investments = allocate_investments(budget["Investing (Savings)"], risk_profile)

# Populate fixed utilities into the live expense ledger automatically if empty to save typing
if st.session_state.expenses.empty and total_monthly_utilities > 0:
    st.session_state.expenses = pd.DataFrame([
        {"Date": datetime.today().strftime('%Y-%m-%d'), "Description": "Electricity Bill (Fixed Base)", "Category": "Essentials (Needs)", "Amount": electricity_bill},
        {"Date": datetime.today().strftime('%Y-%m-%d'), "Description": "Water Bill (Fixed Base)", "Category": "Essentials (Needs)", "Amount": water_bill}
    ])

# ==========================================
# 4. DASHBOARD LAYOUT & METRICS
# ==========================================
st.title("💸 Personal Finance Budgeting & Investment Engine")
st.markdown("---")

# High-Level Metrics Row
m_col1, m_col2, m_col3, m_col4 = st.columns(4)
with m_col1:
    st.metric("Fixed Outflows + Tax Sinking", f"₹{total_fixed_structural_outflow:,.2f}", 
              delta=f"-{total_fixed_structural_outflow/gross_salary*100:.1f}% of Salary", delta_color="inverse")
with m_col2:
    st.metric("Essentials Bucket (50%)", f"₹{budget['Essentials (Needs)']:,.2f}")
with m_col3:
    st.metric("Discretionary Bucket (30%)", f"₹{budget['Discretionary (Wants)']:,.2f}")
with m_col4:
    st.metric("Investment Bucket (20%)", f"₹{budget['Investing (Savings)']:,.2f}")

st.markdown("---")

# Visualizations
left_chart_col, right_chart_col = st.columns(2)
with left_chart_col:
    st.subheader("Total Capital Allocation Matrix")
    all_allocations = {
        "Debt EMIs": home_loan_emi + personal_loan_emi,
        "Property Tax Provisions": monthly_property_tax_cushion,
        "Fixed Utilities (Power/Water)": total_monthly_utilities,
        "Other Essentials (Groceries, Var Needs)": budget["_meta_other_essentials"],
        "Discretionary Spending Pool": budget["Discretionary (Wants)"],
        "Systematic Investment Pool": budget["Investing (Savings)"]
    }
    fig_budget = px.pie(
        names=list(all_allocations.keys()), 
        values=list(all_allocations.values()), 
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    st.plotly_chart(fig_budget, use_container_width=True)

with right_chart_col:
    st.subheader(f"Target Savings Distribution ({risk_profile} Strategy)")
    fig_inv = px.pie(
        names=list(investments.keys()), 
        values=list(investments.values()), 
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    st.plotly_chart(fig_inv, use_container_width=True)

# ==========================================
# 5. CREDIT CARD DEBT TRACKER
# ==========================================
st.markdown("---")
st.header("💳 Credit Card Outstanding Tracker")

cc_col1, cc_col2 = st.columns([1, 2])
with cc_col1:
    st.subheader("Manage Card Balances")
    selected_card = st.selectbox("Select Card", list(st.session_state.cc_cards.keys()))
    action = st.radio("Action", ["Update Total Outstanding", "Log Bill Payment"])
    cc_amount = st.number_input("Amount (INR)", min_value=0.0, step=1000.0)
    
    if st.button("Submit Card Update"):
        if action == "Update Total Outstanding":
            st.session_state.cc_cards[selected_card]["Total Outstanding"] = cc_amount
            st.success(f"Updated {selected_card} balance.")
        elif action == "Log Bill Payment":
            st.session_state.cc_cards[selected_card]["Total Outstanding"] = max(0.0, st.session_state.cc_cards[selected_card]["Total Outstanding"] - cc_amount)
            payment_row = pd.DataFrame([{
                "Date": datetime.today().strftime('%Y-%m-%d'),
                "Description": f"Credit Card Payment: {selected_card}",
                "Category": "Discretionary (Wants)",
                "Amount": cc_amount
            }])
            st.session_state.expenses = pd.concat([st.session_state.expenses, payment_row], ignore_index=True)
            st.success(f"Payment logged! Added to monthly Discretionary tracker.")

with cc_col2:
    st.subheader("Current Card Metrics")
    for card, details in st.session_state.cc_cards.items():
        outstanding = details["Total Outstanding"]
        limit = details["Limit"]
        utilization = (outstanding / limit) * 100
        st.write(f"**{card}**")
        st.write(f"Outstanding: ₹{outstanding:,.2f} / Limit: ₹{limit:,.2f} — *Utilization: {utilization:.1f}%*")
        st.progress(min(utilization / 100, 1.0))

# ==========================================
# 6. LIVE EXPENSE TRACKING
# ==========================================
st.markdown("---")
st.header("🛒 Monthly Spending Trackers")

exp_col1, exp_col2 = st.columns([1, 2])
with exp_col1:
    st.subheader("Log Manual Expense")
    with st.form("manual_expense_form", clear_on_submit=True):
        exp_date = st.date_input("Transaction Date", datetime.today())
        exp_desc = st.text_input("Merchant/Description (e.g., Swiggy, Internet)")
        exp_cat = st.selectbox("Budget Target Bucket", ["Essentials (Needs)", "Discretionary (Wants)", "Investing (Savings)"])
        exp_amt = st.number_input("Amount (INR)", min_value=0.0, step=50.0)
        
        submit_expense = st.form_submit_button("Add Transaction")
        if submit_expense and exp_desc:
            new_row = pd.DataFrame([{
                "Date": exp_date.strftime('%Y-%m-%d'), 
                "Description": exp_desc, 
                "Category": exp_cat, 
                "Amount": exp_amt
            }])
            st.session_state.expenses = pd.concat([st.session_state.expenses, new_row], ignore_index=True)
            st.success("Expense added successfully!")

with exp_col2:
    st.subheader("Transaction Ledger")
    if not st.session_state.expenses.empty:
        st.dataframe(st.session_state.expenses, use_container_width=True, hide_index=True)
        summary_df = st.session_state.expenses.groupby("Category")["Amount"].sum().reset_index()
        
        st.subheader("Disposable Income Burn Analysis")
        for cat, b_amt in [("Essentials (Needs)", budget["Essentials (Needs)"]), 
                           ("Discretionary (Wants)", budget["Discretionary (Wants)"]), 
                           ("Investing (Savings)", budget["Investing (Savings)"])]:
            spent = summary_df[summary_df["Category"] == cat]["Amount"].values[0] if cat in summary_df["Category"].values else 0.0
            remaining = b_amt - spent
            progress = min(spent / b_amt, 1.0) if b_amt > 0 else 0.0
            
            st.write(f"**{cat}**: Spent ₹{spent:,.2f} of ₹{b_amt:,.2f} ({remaining:,.2f} remaining)")
            st.progress(progress)

# ==========================================
# 7. PAYDAY CHECKLIST & EXECUTION
# ==========================================
st.markdown("---")
st.header("📈 Investment Execution Blueprint")

chk_col1, chk_col2 = st.columns([2, 1])
with chk_col1:
    st.subheader("Payday Execution Checklist")
    eq_target = investments.get("Equity", 0)
    debt_target = investments.get("Debt/Fixed Income", 0)
    liquid_target = investments.get("Emergency/Liquid", 0)

    st.session_state.sip_checklist["Nifty BEES (Equity ETF)"] = st.checkbox(
        f"Route Systematic Index Transfer to Equity ETFs / Nifty BEES — Target: ₹{eq_target:,.2f}",
        value=st.session_state.sip_checklist["Nifty BEES (Equity ETF)"]
    )
    st.session_state.sip_checklist["Flexi-cap Mutual Fund"] = st.checkbox(
        f"Deploy Regular Active Core Equity Mutual Fund SIP — Target: Included in Equity Pool",
        value=st.session_state.sip_checklist["Flexi-cap Mutual Fund"]
    )
    st.session_state.sip_checklist["PPF / Debt Fund"] = st.checkbox(
        f"Execute Debt Allocation Sweep (PPF / Debt Mutual Funds) — Target: ₹{debt_target:,.2f}",
        value=st.session_state.sip_checklist["PPF / Debt Fund"]
    )
    st.session_state.sip_checklist["Property Tax Sinking Reserve"] = st.checkbox(
        f"Sweep Property Tax pro-rated reserve to separate high-yield account — Target: ₹{monthly_property_tax_cushion:,.2f}",
        value=st.session_state.sip_checklist.get("Property Tax Sinking Reserve", False)
    )
    st.session_state.sip_checklist["Liquid Emergency Buffer"] = st.checkbox(
        f"Park Capital Reserve Component into Liquid Scheme / Savings — Target: ₹{liquid_target:,.2f}",
        value=st.session_state.sip_checklist["Liquid Emergency Buffer"]
    )

with chk_col2:
    st.subheader("Deployment Status")
    completed = sum(st.session_state.sip_checklist.values())
    total = len(st.session_state.sip_checklist)
    
    st.metric("Tasks Completed", f"{completed} / {total}")
    if completed == total:
        st.balloons()
        st.success("Clean execution! All systematic investments and reserve sweeps are complete.")