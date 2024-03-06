import pdfplumber
import pandas as pd
import re

def HLBB_main(df_list, sort):
    DATE_REGEX = r'\d{2}-\d{2}-\d{4}'
    KEYWORDS_TO_REMOVE = ["Hong Leong Bank Berhad", "Total Withdrawals", "Balance from"]

    df = pd.concat(df_list, ignore_index=True)

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


    bal = [(float(row['Balance'].replace(',', "")), pd.to_datetime(df_with_balance.at[index + 1, 'Date'], errors='coerce', dayfirst=True).month, index) for index, row in df_with_balance[df_with_balance['Description'].str.contains('Balance from previous statement', na=False)].iterrows()]
    for i in range(len(bal)):
        index = bal[i][2]
        previous_balance = df_with_balance.at[index, 'Balance'].replace(",", "")
        deposit = df_with_balance.at[index + 1, 'Deposit'].replace(",", "")
        withdrawal = df_with_balance.at[index + 1, 'Withdrawal'].replace(",", "")

        # Replace empty values with zeros
        previous_balance = float(previous_balance) if previous_balance else 0
        deposit = float(deposit) if deposit else 0
        withdrawal = float(withdrawal) if withdrawal else 0

        df_with_balance.at[index + 1, 'Balance'] = previous_balance + deposit - withdrawal

    df = df_with_balance[df_with_balance['Date'].str.match(r'\d{2}-\d{2}-\d{4}')]

    df['Date2'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
    df['Month'] = df['Date2'].dt.month
    df['Idx'] = df.index
    df['Idx'] = pd.to_numeric(df['Idx'], errors='coerce')
    if sort == 1:
        df = df.sort_values(by = ['Date2', 'Idx'], ascending = [True, True])
    elif sort == -1:
        df = df.sort_values(by = ['Date2', 'Idx'], ascending = [True, False])

    bal = sorted(bal, key=lambda x: x[1])

    # Convert 'Deposit' and 'Withdrawal' columns to numeric values and fill NaN with 0
    df['Deposit'] = pd.to_numeric(df['Deposit'].str.replace(',', ''), errors='coerce').fillna(0)
    df['Withdrawal'] = pd.to_numeric(df['Withdrawal'].str.replace(',', ''), errors='coerce').fillna(0)

    df['Amount2'] = df['Deposit'] - df['Withdrawal']
    df['Amount'] = df['Amount2'].apply(lambda x: f'{abs(x):.2f}+' if x > 0 else f'{abs(x):.2f}-')
    i = 0
    for index, row in df.iterrows():
        if row['Balance'] == "":
            df.at[index, 'Balance'] = float(str(df.at[index - 1, 'Balance']).replace(",", "")) + float(str(row['Deposit']).replace(",", "")) - float(str(row['Withdrawal']).replace(",", ""))
            prev_idx = row['Idx']
            
    df['Balance'] = df['Balance'].apply(lambda x: float(str(x).replace(",", "")))
    df = df.drop(['Deposit', 'Withdrawal'], axis=1)
    df = df.reset_index(drop=True)

    return df, bal