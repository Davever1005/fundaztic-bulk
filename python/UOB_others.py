import pdfplumber
import pandas as pd
import re

def add_year(df):
    DATE_REGEX = r'\d{2}\w{3}'
    AMOUNT_REGEX = r'\.\d{2}'
    BAL_REGEX = r'\.\d{2}|\.\d{2}-'
    year = None
    months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    # Create a copy of the DataFrame to avoid modifying the original
    new_df = df.copy()
    adjustYear = False
    for i, row in new_df.iterrows():
        # Join all columns into a single string
        row_string = ",".join(row.astype(str).values)
        elements = row_string.split(',')
        if len(elements) > 1:
            if re.match(r'\d{2}\w{3}\d{4}', "".join(elements[-3:]).replace(",", "").replace(" ", "")[-9:]) and ('Current' in elements[0] or 'vestPro' in elements[0]):
                if 'JAN' in "".join(elements[-3:]).replace(",", "").replace(" ", "")[-9:]:
                    adjustYear = True
                else:
                    adjustYear = False
                year = elements[-1][-4:]
            elif (re.match(DATE_REGEX, elements[0].replace(" ", "")) and 
                (any(month in elements[0][-3:].upper() for month in months)) and
                (re.match(BAL_REGEX, elements[-1][-3:]) or re.match(BAL_REGEX, elements[-1][-4:])) and 
                any(re.match(AMOUNT_REGEX, elem[-3:]) for elem in elements[-3:] if elem)):
                if 'DEC' in elements[0] and adjustYear:
                    elements[0] = elements[0].replace(" ", "") + str(int(year)-1)
                else:
                    elements[0] = elements[0].replace(" ", "") + str(year)
                # Update the first column (assuming it's the date column)
                new_df.iloc[i, 0] = elements[0]
    
    return new_df

def UOB2_main(df_list, sort, temp):
    DATE_REGEX = r'\d{2}\w{3}\d{4}'
    KEYWORDS_TO_REMOVE = ["BALANCE C/F", "BALANCE B/F", "ount Summary"]
    df = pd.concat(df_list, ignore_index=True)
    df = add_year(df)
    df.columns = ['Date', 'Transaction Date/Time', 'Description', 'Withdrawal', 'Deposit', 'Balance']
    df.to_csv('test2.csv')
    # df['Date2'].fillna(pd.to_datetime(df['Date'], errors='coerce', format='%d/%m'), inplace=True)
    # df['Date2'].fillna(pd.to_datetime(df['Date'], errors='coerce', format='%d/%m/%y'), inplace=True)

    # df['Deposit'] = pd.to_numeric(df['Deposit'].apply(lambda x: str(x).replace(',', '') if pd.notna(x) else x), errors='coerce')
    # df['Withdrawal'] = pd.to_numeric(df['Withdrawal'].apply(lambda x: str(x).replace(',', '') if pd.notna(x) else x), errors='coerce')
    index_export_date = df[df.apply(lambda row: 'fikasi' in ''.join(map(str, row)), axis=1)].index
    prev_end = 0
    # Drop rows from each occurrence of "导出日期" until the next header row
    for start_index in index_export_date:
        if start_index > prev_end:
            index_found = df[df.index > start_index].apply(lambda row: 'Trans Date' in row[0], axis=1)
            if len(index_found) >0:
                next_occurrence_index = index_found.idxmax()
                end_index = next_occurrence_index
                
                # Now you can perform your desired operation, e.g., dropping rows
                df = df.drop(range(start_index, end_index))
                prev_end = end_index
    df = df.reset_index(drop=True)
    idx = None
    for index, row in df.iterrows():
        if re.match(DATE_REGEX, str(row['Date'])):
            idx = index
        elif any(keyword in str(row) for keyword in KEYWORDS_TO_REMOVE):
            idx = None
        elif idx is not None and df.iloc[index, 2] is not None:
            # Concatenate description with previous row
            df.iloc[idx, 2] = str(df.iloc[idx, 2]) + ' ' + str(df.iloc[index, 2])
    df['Date2'] = pd.to_datetime(df['Date'], errors='coerce', format='%d%b%Y')
    df_null_date = df[df['Date2'].isnull()]
    df = df.dropna(subset=['Date2'])  # DataFrame with valid dates
    df = df.reset_index(drop=True)
    df = df[df.iloc[:, 0] != "Trans Date"]
    df = df[df.iloc[:, 2] != "BALANCE B/F "]
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