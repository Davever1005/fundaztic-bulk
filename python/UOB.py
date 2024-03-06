import pdfplumber
import pandas as pd
import re

def UOB_main(df_list, sort, temp):
    DATE_REGEX = r'\d{2}-\d{2}-\d{4}'
    KEYWORDS_TO_REMOVE = ["TotalinAccountCurrency",'For Customer', '']

    df = pd.concat(df_list, ignore_index=True)
    df.to_csv('test.csv')
    if temp == 1:
        df.columns = ['Date', 'Transaction Date/Time', 'Description', 'Deposit', 'Withdrawal', 'Balance']
    else:
        df.columns = ['Date', 'Value Date', 'Transaction Date/Time', 'Description', 'Deposit', 'Withdrawal', 'Balance']

    df['Date2'] = pd.to_datetime(df['Date'], errors='coerce', format='%d/%m/%Y')
    df.to_csv('test2.csv')
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

    index_export_date = df[df.apply(lambda row: 'For Customer' in ''.join(map(str, row)), axis=1)].index
    for start_index in index_export_date:
        if start_index > prev_end:
            index_found = df[df.index > start_index].apply(lambda row: 'Statement Date' in row[0], axis=1)
            if len(index_found) >0:
                next_occurrence_index = index_found.idxmax()
                end_index = next_occurrence_index
                
                # Now you can perform your desired operation, e.g., dropping rows
                df = df.drop(range(start_index, end_index))
                prev_end = end_index
    df = df.reset_index(drop=True)

    # Find the indices of the rows containing "导出日期" in any column
    index_export_date = df[df.apply(lambda row: '导出日期' in ''.join(map(str, row)), axis=1)].index
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
            else:
                df = df.drop(range(start_index, len(df)))
                prev_end = len(df)
    df = df[df.iloc[:, 0] != "账单日期"]
    df = df.reset_index(drop=True)
    # Find the indices of the rows containing "Date of Export" in any column
    index_export_date = df[df.apply(lambda row: 'Date of Export' in ''.join(map(str, row)), axis=1)].index
    prev_end = 0
    # Drop rows from each occurrence of "Date of Export" until the next header row
    for start_index in index_export_date:
        if start_index > prev_end:
            index_found = df[df.index > start_index].apply(lambda row: 'Statement Date' in row[0], axis=1)
            if len(index_found) >0:
                next_occurrence_index = index_found.idxmax()
                end_index = next_occurrence_index
                
                # Now you can perform your desired operation, e.g., dropping rows
                df = df.drop(range(start_index, end_index))
                prev_end = end_index
            else:
                df = df.drop(range(start_index, len(df)))
                prev_end = len(df)
    df = df[df.iloc[:, 0] != "Statement Date"]
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
    df = df[df['Date2'].notna() & (df['Deposit'] != "") & (df['Withdrawal'] != "") & (df['Balance'] != "")]
    df.to_csv('test3.csv')
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

    return df