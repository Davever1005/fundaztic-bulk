import pandas as pd

def summary_main(df, bal, bank_selected):

    dict_data={}
    # Convert 'Amount' column to numeric (remove commas and convert to float)
    df['Amount2'] = df['Amount2'].replace('[\$,]', '', regex=True).astype(float)

    df['Month_Year'] = df['Date2'].dt.strftime('%b %y')
    for name, group in df.groupby(df['Month_Year']):
        if len(bal) == 0 or bank_selected=='HLBB':
            begin = group.iloc[0]['Balance'] - group.iloc[0]['Amount2']
        else:
            begin = float(next((item[0] for item in bal if item[1] == group.iloc[0]['Month']), 0))
            print(begin)
        cr_count = group[group['Sign'] == 1]['Amount2'].count()
        cr_sum = group[group['Sign'] == 1]['Amount2'].sum()
        db_count = group[group['Sign'] == -1]['Amount2'].count()
        db_sum = abs(group[group['Sign'] == -1]['Amount2'].sum())
        ending_balance = group.iloc[-1]['Balance']
        
        dict_data[name] = {
            'BEGINNING BALANCE': round(begin, 2),
            'CR_Transactions': cr_count,
            'CR_Amount': round(cr_sum, 2),
            'DB_Transactions': db_count,
            'DB_Amount': round(db_sum, 2),
            'ENDING BALANCE': round(ending_balance, 2)
        }

    dict_data = dict(sorted(dict_data.items(), key=lambda x: pd.to_datetime(x[0], format='%b %y')))

    return dict_data
