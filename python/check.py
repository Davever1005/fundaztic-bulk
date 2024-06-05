import pandas as pd
from datetime import datetime

def check_balance_within_month(df, bal, sort, bank_selected):
    warning = []
    warning_index = []
    if bank_selected =='HLBB':
        prev_month = None
        for index, row in df.iterrows():
            if index == 0:
                prev_balance = round(float(row['Balance']),2)
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
    elif bank_selected == 'UOB':
         go = 0
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
    elif bank_selected == 'PBB':
        df['Idx'] = df.index
        df['Idx'] = pd.to_numeric(df['Idx'], errors='coerce')
        if sort == 1:
            df = df.sort_values(by = ['Date2', 'Idx'], ascending = [True, True])
        elif sort == -1:
            df = df.sort_values(by = ['Date2', 'Idx'], ascending = [True, False])
        prev_month = None
        go = 0
        for index, row in df.iterrows():
            # Extract relevant columns
            current_month = row['Month']
            if prev_month is None:
                find_balance = next((item[0] for item in bal if item[1] == current_month), None)
                if find_balance:
                    prev_balance = find_balance
            amount2 = round(float(row['Amount2']),2)
            current_balance = round(float(row['Balance']),2)
            # Calculate previous balance + amount2
            calculated_balance = float(prev_balance) + float(amount2)
            prev_month = current_month
            # Compare with current balance
            
            if round(calculated_balance,2) != round(current_balance,2):
                warning.append(f"Balance mismatch at {row['Date']}: {row['Description']}, {row['Amount2']}, {row['Balance']} :: Calculated Balance = {calculated_balance}")
                warning_index.append(int(index))
            # Update previous balance for the next iteration
            prev_balance = current_balance
    else:
        df['Idx'] = df.index
        df['Idx'] = pd.to_numeric(df['Idx'], errors='coerce')
        if sort == 1:
            df = df.sort_values(by = ['Date2', 'Idx'], ascending = [True, True])
        elif sort == -1:
            df = df.sort_values(by = ['Date2', 'Idx'], ascending = [True, False])
        prev_month = None
        go = 0
        for index, row in df.iterrows():
            # Extract relevant columns
            current_month = row['Month']
            if prev_month is None and bank_selected!='HLBB':
                find_balance = next((item[0] for item in bal if item[1] == current_month), None)
                if find_balance:
                    prev_balance = find_balance
            amount2 = round(float(row['Amount2']),2)
            current_balance = round(float(row['Balance']),2)
            # Calculate previous balance + amount2
            calculated_balance = float(prev_balance) + float(amount2)
            prev_month = current_month
            # Compare with current balance
            
            if round(calculated_balance,2) != round(current_balance,2):
                warning.append(f"Balance mismatch at {row['Date']}: {row['Description']}, {row['Amount2']}, {row['Balance']} :: Calculated Balance = {calculated_balance}")
                warning_index.append(int(index))
            # Update previous balance for the next iteration
            prev_balance = current_balance
    if len(warning) < 1:
        warning.append("no warning")

    return warning, warning_index
