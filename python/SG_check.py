import pandas as pd
from datetime import datetime

def SG_check_balance_within_month(df, bal, sort, bank_selected):
    warning = []
    warning_index = []
    go = 0
    prev_month = None
    for index, row in df.iterrows():
        if len(bal) == 0 and go==0:
            warning.append("No beginning balance in bank statement.")
            prev_balance = round(float(row['Balance']),2)
            go=1
        else:
            # Extract relevant columns
            amount2 = round(float(row['Amount2']),2)
            current_balance = round(float(row['Balance']),2)
            # Calculate previous balance + amount2
            calculated_balance = float(prev_balance) + float(amount2)
            # Compare with current balance
            if round(calculated_balance,2) != round(current_balance,2):
                warning.append(f"Balance mismatch at {row['Date']}: {row['Description']}, {row['Amount2']}, {row['Balance']} :: Calculated Balance = {calculated_balance}")
                warning_index.append(int(index))
            # Update previous balance for the next iteration
            prev_balance = current_balance
    if len(warning) < 1:
        warning.append("no warning")

    return warning, warning_index
