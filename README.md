**Run the Application**
Since Streamlit creates localized environmental binaries, run the application using the explicit Python module flag to avoid terminal environment path errors:

Bash
python -m streamlit run app.py

Once executed, a local development network server will initialize, and the dashboard will automatically open in your default browser at http://localhost:8501.

📈 Financial Framework Breakdown
The application implements a structural cash flow hierarchy to prevent budget deficits:

Gross Monthly Salary Ingestion

➖ Structural Outflows Subtraction: (Home Loan EMI + Personal Loan EMI + Annual Property Tax / 12)

🗺️ 50/30/20 Rule Application: Evaluated solely on the remaining Net Disposable Income Pool.

50% Essentials: Absorbs base electricity & water parameters immediately; remaining funds are dedicated to dynamic necessities (groceries, insurance, etc.).

30% Discretionary: Dedicated to variables (dining, entertainment, credit card settlements).

20% Investing: Passed to the risk-profile allocation matrix.

🔒 Security Note
This is a personal local-first prototype. All data logged via the transaction engines or entered into financial inputs remains strictly in your local system's active runtime memory environment. No data is tracked, logged, or transmitted to external servers.
