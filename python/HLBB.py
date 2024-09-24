import pdfplumber
import pandas as pd
import re

def check_and_fill(df_list):
    df = pd.concat(df_list, ignore_index=True)
    AMOUNT_REGEX = r'\.\d{2}'
    
    for i in range(1, len(df) - 1):
        try:
            # Check if first column is empty string and any of columns 2, 3, 4 match the regex
            if df.iloc[i, 0] == "" and df.iloc[i, 1] != "Balance from previous statement" and any(isinstance(df.iloc[i, col], str) and 
                                           re.search(AMOUNT_REGEX, str(df.iloc[i, col])[-3:]) 
                                           for col in [2, 3, 4]):
                
                matching_columns = [col for col in [2, 3, 4] 
                                    if isinstance(df.iloc[i, col], str) and 
                                    re.search(AMOUNT_REGEX, str(df.iloc[i, col])[-3:])]
                if matching_columns:
                    prev_amt_check = all(pd.isna(df.iloc[i-1, j]) or df.iloc[i-1, j] == "" for j in matching_columns)
                    next_amt_check = all(pd.isna(df.iloc[i+1, j]) or df.iloc[i+1, j] == "" for j in matching_columns)
                    prev_date_check = all(df.iloc[i-1, j] != "" for j in [0,1] if pd.notna(df.iloc[i-1, j]))
                    next_date_check = all(df.iloc[i+1, j] != "" for j in [0,1] if pd.notna(df.iloc[i+1, j]))
                    
                    if next_amt_check and next_date_check:
                        for col in matching_columns:
                            df.iloc[i+1, col] = df.iloc[i, col]
                            df.iloc[i, col] = ""
                    elif prev_amt_check and prev_date_check:
                        for col in matching_columns:
                            df.iloc[i-1, col] = df.iloc[i, col]
                            df.iloc[i, col] = ""
        
        except Exception as e:
            print(f"Error processing row {i}: {str(e)}")
            print(f"Row data: {df.iloc[i]}")
    
    return df

def find_surrounding_rows(s, df):
    for idx, row in df.iterrows():
        row_str = ' '.join(row.astype(str))
        if s in row_str:
            prev_row = df.iloc[idx - 1] if idx > 0 else None
            current_row = row
            next_row = df.iloc[idx + 1] if idx < len(df) - 1 else None
            return prev_row.tolist(), current_row.tolist(), next_row.tolist(), idx
    return None, None, None, None

def HLBB_main(df_list, alltext, sort):
    DATE_REGEX = r'\d{2}-\d{2}-\d{4}'
    KEYWORDS_TO_REMOVE = ["Hong Leong Bank Berhad", "Total Withdrawals", "Balance from"]
    df = check_and_fill(df_list)

    ######
    mask_col3_valid = df[df.columns[2]].notnull() & (df[df.columns[2]].str.strip() == '')
    mask_col4_valid = df[df.columns[3]].notnull() & (df[df.columns[3]].str.strip() == '')

    filtered_df = df[mask_col3_valid & mask_col4_valid]

    DATE_REGEX = r'\d{2}-\d{2}-\d{4}'
    date_filtered_df = filtered_df[filtered_df[filtered_df.columns[0]].str.match(DATE_REGEX, na=False)]

    first_two_columns_df = date_filtered_df.iloc[:, :2]
    list_of_strings = first_two_columns_df.apply(lambda row: ' '.join(row.astype(str)), axis=1).tolist()
    for s in list_of_strings:
        value_to_find = None
        for r in alltext:
            if s in r:
                print(f"Matching text: {r}")
                value_to_find = r.split(" ")[-1]
                print(f"Value to find: {value_to_find}")
                if value_to_find:
                    prev_row, current_row, next_row, current_idx = find_surrounding_rows(s, df)
                    
                    if prev_row is not None:
                        try:
                            # Get the index of value_to_find in prev_row
                            value_index = prev_row.index(value_to_find)
                            prev_row[value_index] = ''
                            current_row[value_index] = value_to_find
                        except ValueError:
                            print(f"Value '{value_to_find}' not found in previous row.")
                    
                    if next_row is not None:
                        try:
                            # Get the index of value_to_find in next_row
                            value_index = next_row.index(value_to_find)
                            next_row[value_index] = ''
                            current_row[value_index] = value_to_find
                        except ValueError:
                            print(f"Value '{value_to_find}' not found in next row.")
                    
                    # Update the DataFrame with modified rows
                    if prev_row is not None:
                        df.iloc[current_idx - 1] = prev_row
                    df.iloc[current_idx] = current_row
                    if next_row is not None:
                        df.iloc[current_idx + 1] = next_row
                    print("Updated list_of_strings:", list_of_strings)
                else:
                    print("Value to find not found.")
    #####
    df.columns = ['Date', 'Description', 'Deposit', 'Withdrawal', 'Balance']
    # Iterate over rows
    idx = None
    for index, row in df.iterrows():
        if re.match(DATE_REGEX, row['Date']):
            idx = index
        elif any(keyword in str(row) for keyword in KEYWORDS_TO_REMOVE):
            idx = None
        elif idx is not None and df.iloc[index, 1] is not None:
            # Concatenate description with previous row
            df.iloc[idx, 1] = str(df.iloc[idx, 1]) + ' ' + str(df.iloc[index, 1])

    # Drop rows where the first element is not a date
    df_with_balance = df[df['Date'].str.match(r'\d{2}-\d{2}-\d{4}') | df['Description'].str.contains('Balance from')]
    df_with_balance = df_with_balance.reset_index(drop=True)

    for index, row in df_with_balance.iterrows():
        if "(" in str(row['Balance']) and ")" in str(row['Balance']):
            df_with_balance.at[index, 'Balance'] = -float(str(row['Balance']).replace("(", "").replace(")", "").replace(",", ""))

    bal = [(float(str(row['Balance']).replace(',', "")), pd.to_datetime(df_with_balance.at[index + 1, 'Date'], errors='coerce', dayfirst=True).month, index) for index, row in df_with_balance[df_with_balance['Description'].str.contains('Balance from previous statement', na=False)].iterrows()]
    # for i in range(len(bal)):
    #     try:
    #         index = bal[i][2]
    #         previous_balance = str(df_with_balance.at[index, 'Balance']).replace(",", "")
    #         deposit = str(df_with_balance.at[index + 1, 'Deposit']).replace(",", "")
    #         withdrawal = str(df_with_balance.at[index + 1, 'Withdrawal']).replace(",", "")
    #         print(previous_balance, deposit, withdrawal)
    #         # Replace empty values with zeros
    #         previous_balance = float(previous_balance) if previous_balance else 0
    #         deposit = float(deposit) if deposit else 0
    #         withdrawal = float(withdrawal) if withdrawal else 0
    #     except Exception:
    #         pass

    #     df_with_balance.at[index + 1, 'Balance'] = previous_balance + deposit - withdrawal

    df_with_balance['Deposit'] = pd.to_numeric(df_with_balance['Deposit'].str.replace(',', ''), errors='coerce').fillna(0)
    df_with_balance['Withdrawal'] = pd.to_numeric(df_with_balance['Withdrawal'].str.replace(',', ''), errors='coerce').fillna(0)
    df_with_balance['Amount2'] = df_with_balance['Deposit'] - df_with_balance['Withdrawal']
    df_with_balance['Amount'] = df_with_balance['Amount2'].apply(lambda x: f'{abs(x):.2f}+' if x > 0 else f'{abs(x):.2f}-')
    df_with_balance = df_with_balance.reset_index(drop=True)
    i = 0
    for index, row in df_with_balance.iterrows():
        if row['Balance'] == "":
            df_with_balance.at[index, 'Balance'] = float(str(df_with_balance.at[index - 1, 'Balance']).replace(",", "")) + float(str(row['Deposit']).replace(",", "")) - float(str(row['Withdrawal']).replace(",", ""))

    df = df_with_balance[df_with_balance['Date'].str.match(r'\d{2}-\d{2}-\d{4}')]
    df['Date2'] = pd.to_datetime(df['Date'].str[:10], errors='coerce', dayfirst=True)
    df_null_date = df[df['Date2'].isnull()]
    df = df.dropna(subset=['Date2'])  # DataFrame with valid dates
    df['Month'] = df['Date2'].dt.month
    df['Idx'] = df.index
    df['Idx'] = pd.to_numeric(df['Idx'], errors='coerce')
    
    bal = sorted(bal, key=lambda x: x[1])
   
                
    df['Balance'] = df['Balance'].apply(lambda x: float(str(x).replace(",", "")))
    df = df.drop(['Deposit', 'Withdrawal'], axis=1)
    df = df.reset_index(drop=True)

    if sort == 1:
        df = df.sort_values(by = ['Date2', 'Idx'], ascending = [True, True])
    elif sort == -1:
        df = df.sort_values(by = ['Date2', 'Idx'], ascending = [True, False])


    bal = [(x, y) for x, y, _ in bal]

    df['Sign'] = df['Amount2'].apply(lambda x: 1 if x > 0 else -1)
    df['Description'] = df['Description'].str.replace('\n', ' ')
    return df, bal, df_null_date