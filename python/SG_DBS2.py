import pdfplumber
import pandas as pd
import re

def combine_df_rows(df):

    combined_rows = []
    current_row = None
    for _, row in df.iterrows():
        if pd.notna(row['Date2']) and ((row["Deposit"]!="" or row["Deposit"] is not None) or (row["Withdrawal"]!="" or row["Withdrawal"] is not None) and (row["Balance"]!="" or row["Balance"] is not None)):  # If the Date is not empty, it's a new transaction
            if current_row is not None:
                combined_rows.append(current_row)
            current_row = row.copy()
        elif row['Date']=="" and ((row["Deposit"]!="" or row["Deposit"] is not None) or (row["Withdrawal"]!="" or row["Withdrawal"] is not None) and (row["Balance"]!="" or row["Balance"] is not None)):  # If the Date is empty, it's a continuation of the previous transaction
            if current_row is not None:
                # Combine the description, handling potential None or NaN values
                current_desc = str(current_row['Description']) if pd.notna(current_row['Description']) else ""
                new_desc = str(row['Description']) if pd.notna(row['Description']) else ""
                current_row['Description'] = (current_desc + ' ' + new_desc).strip()
                

    if current_row is not None:
        combined_rows.append(current_row)

    return pd.DataFrame(combined_rows)

def SG_DBS2_main(df_list, sort):
    DATE_REGEX = r'\d{2}-\d{2}-\d{4}'
    KEYWORDS_TO_REMOVE = ["TotalinAccountCurrency",'For Customer', '']
    df = pd.concat(df_list, ignore_index=True)
    df.columns = ['Date', 'Transaction Date/Time', 'Description', 'Withdrawal', 'Deposit', 'Balance']

    # df['Date2'].fillna(pd.to_datetime(df['Date'], errors='coerce', format='%d/%m'), inplace=True)
    # df['Date2'].fillna(pd.to_datetime(df['Date'], errors='coerce', format='%d/%m/%y'), inplace=True)

    # df['Deposit'] = pd.to_numeric(df['Deposit'].apply(lambda x: str(x).replace(',', '') if pd.notna(x) else x), errors='coerce')
    # df['Withdrawal'] = pd.to_numeric(df['Withdrawal'].apply(lambda x: str(x).replace(',', '') if pd.notna(x) else x), errors='coerce')
    index_export_date = df[df.apply(lambda row: 'For Customer' in ''.join(map(str, row)), axis=1)].index
    prev_end = 0
    # Drop rows from each occurrence of "导出日期" until the next header row
    for start_index in index_export_date:
        if start_index > prev_end:
            index_found = df[df.index > start_index].apply(lambda row: '账单日期' in row[0], axis=1)
            if len(index_found) >0:
                next_occurrence_index = index_found.idxmax()
                end_index = next_occurrence_index
                
                # Now you can perform your desired operation, e.g., dropping rows
                df = df.drop(range(start_index, end_index))
                prev_end = end_index
    df = df.reset_index(drop=True)

    index_export_date = df[df.apply(lambda row: 'Printed By' in ''.join(map(str, row)), axis=1)].index
    for start_index in index_export_date:
        if start_index > prev_end:
            index_found = df[df.index > start_index].apply(lambda row: 'Date' in row[0], axis=1)
            if len(index_found) >0:
                next_occurrence_index = index_found.idxmax()
                end_index = next_occurrence_index
                
                # Now you can perform your desired operation, e.g., dropping rows
                df = df.drop(range(start_index, end_index))
                prev_end = end_index
    df = df.reset_index(drop=True)
    # Find the indices of the rows containing "Date of Export" in any column
    index_export_date = df[df.apply(lambda row: 'Total Debit' in ''.join(map(str, row)), axis=1)].index
    prev_end = 0
    # Drop rows from each occurrence of "Date of Export" until the next header row
    for start_index in index_export_date:
        if start_index > prev_end:
            index_found = df[df.index > start_index].apply(lambda row: 'Date' in row[0], axis=1)
            if len(index_found) >0:
                next_occurrence_index = index_found.idxmax()
                end_index = next_occurrence_index
                
                # Now you can perform your desired operation, e.g., dropping rows
                df = df.drop(range(start_index, end_index))
                prev_end = end_index
            else:
                df = df.drop(range(start_index, len(df)))
                prev_end = len(df)
    df = df[df.iloc[:, 0] != "Date"]
    df['Date2'] = pd.to_datetime(df['Date'], errors='coerce', format='%d-%b-%Y')
    df = combine_df_rows(df)
    df = df.dropna(subset=['Date2'])  # DataFrame with valid dates
    df = df.reset_index(drop=True)
    idx = None
    for index, row in df.iterrows():
        if not pd.isna(row['Date2']):
            idx = index
        elif any(keyword in str(row) for keyword in KEYWORDS_TO_REMOVE):
            df.at[index, 'Date'] = pd.NA
            idx = None
        elif idx is not None and df.at[index, 'Description'] is not None:
            # Concatenate description with previous row
            df.at[idx, 'Description'] = str(df.at[idx, 'Description']) + ' ' + str(df.at[index, 'Description'])

    # Drop rows where the first element is not a date
    df = df[df['Date2'].notna() & ((df['Deposit'] != "") | (df['Withdrawal'] != "")) & (df['Balance'] != "")]
    df = df.reset_index(drop=True)
    df['Month'] = df['Date2'].dt.month
    df['Idx'] = df.index
    df['Idx'] = pd.to_numeric(df['Idx'], errors='coerce')
    if sort == 1:
        df = df.sort_values(by = ['Date2', 'Idx'], ascending = [True, True])
    elif sort == -1:
        df = df.sort_values(by = ['Date2', 'Idx'], ascending = [True, False])

    # Convert 'Deposit' and 'Withdrawal' columns to numeric values and fill NaN with 0
    df['Deposit'] = pd.to_numeric(df['Deposit'].str.replace(',', ''), errors='coerce').fillna(0)
    df['Withdrawal'] = pd.to_numeric(df['Withdrawal'].str.replace(',', ''), errors='coerce').fillna(0)

    df['Amount2'] = df['Deposit'] - df['Withdrawal']
    df['Amount'] = df['Amount2'].apply(lambda x: f'{abs(x):.2f}+' if x > 0 else f'{abs(x):.2f}-')
    i = 0
    for index, row in df.iterrows():
        if row['Balance'] == "":
            df.at[index, 'Balance'] = float(str(df.at[index - 1, 'Balance']).replace(",", "")) + float(str(row['Deposit']).replace(",", "")) - float(str(row['Withdrawal']).replace(",", ""))
            
    df['Balance'] = df['Balance'].apply(lambda x: float(str(x).replace(",", "")))
    df = df.drop(['Deposit', 'Withdrawal'], axis=1)
    df = df.reset_index(drop=True)

    df['Sign'] = df['Amount2'].apply(lambda x: 1 if x > 0 else -1)
    df['Description'] = df['Description'].str.replace('\n', ' ')

    return df