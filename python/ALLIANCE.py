import pdfplumber
import pandas as pd
import re

def ALL_main(df_list, sort):
    DATE_REGEX = r'\d{2}\d{2}\d{2}'
    KEYWORDS_TO_REMOVE = ["TOTAL DEBIT/CREDIT"]

    df = pd.concat(df_list, ignore_index=True)
    df.columns = ['Date', 'Description', 'Cheque No.', 'Debit', 'Credit', 'Balance']
    
    # Iterate over rows
    idx = None
    for index, row in df.iterrows():
        if re.match(DATE_REGEX, str(row['Date'])):
            idx = index
        elif any(keyword in str(row) for keyword in KEYWORDS_TO_REMOVE):
            idx = None
        elif idx is not None and df.iloc[index, 1] is not None:
            # Concatenate description with previous row
            df.iloc[idx, 1] = str(df.iloc[idx, 1]) + ' ' + str(df.iloc[index, 1])

    # Drop rows where the first element is not a date
    df_with_balance = df[df['Date'].str.match(r'\d{2}\d{2}\d{2}') | df['Description'].str.contains('BEGINNING BALANCE')]
    df_with_balance = df_with_balance.reset_index(drop=True)

    for index in range(1, len(df)):
        if df.at[index, 'Balance'] is not None or df.at[index, 'Balance'] != "" or df.at[index, 'Balance'] != " ":
            # Get the previous balance value
            balance = str(df.at[index, 'Balance'])
            # Check if the balance contains 'CR' or 'DR'
            if 'CR' in balance:
                # Replace comma and convert to float
                df.at[index, 'Balance'] = float(balance.replace(",", "").replace("CR", ""))
            elif ' DR' in balance:            
                df.at[index, 'Balance'] = -float(balance.replace(",", "").replace("DR", ""))
        else:
            # If balance is None or empty string, you can set it to 0 or handle it accordingly
            df.at[index, 'Balance'] = None

    df_with_balance = df[df['Balance'].notna()]
    df_with_balance = df_with_balance.reset_index(drop=True)

    bal = [(row['Balance'], pd.to_datetime(df_with_balance.at[index + 1, 'Date'], errors='coerce', dayfirst=True).month, index) for index, row in df_with_balance[df_with_balance['Description'].str.contains('BEGINNING BALANCE', na=False)].iterrows()]

    df['Date2'] = pd.to_datetime(df['Date'], errors='coerce', format='%d%m%y')
    df.to_csv('test.csv')
    df = df[df['Date2'].notna() & ((df['Credit'] != "") | (df['Debit'] != "")) & (df['Balance'] != "")]
    df = df.reset_index(drop=True)

    df['Month'] = df['Date2'].dt.month
    df['Idx'] = df.index
    df['Idx'] = pd.to_numeric(df['Idx'], errors='coerce')
    if sort == 1:
        df = df.sort_values(by = ['Date2', 'Idx'], ascending = [True, True])
    elif sort == -1:
        df = df.sort_values(by = ['Date2', 'Idx'], ascending = [True, False])

    df['Credit'] = pd.to_numeric(df['Credit'].str.replace(',', ''), errors='coerce').fillna(0)
    df['Debit'] = pd.to_numeric(df['Debit'].str.replace(',', ''), errors='coerce').fillna(0)

    df['Amount2'] = df['Credit'] - df['Debit']
    df['Amount'] = df['Amount2'].apply(lambda x: f'{abs(x):.2f}+' if x > 0 else f'{abs(x):.2f}-')
    df['Description'] = df['Description'] + ' ' + df['Cheque No.']
    df = df.drop(['Credit', 'Debit'], axis=1)
    df = df.reset_index(drop=True)

    df['Sign'] = df['Amount2'].apply(lambda x: 1 if x > 0 else -1)
    df['Description'] = df['Description'].str.replace('\n', ' ')
    
    bal = [(x, y) for x, y, _ in bal]

    return df, bal