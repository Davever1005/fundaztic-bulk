def summary_main(df):
    unique_months_list = df['Month'].unique()

    dict_data={}
    # Iterate through unique months and populate the dictionary
    for month in unique_months_list:
        # Use boolean indexing to filter rows for a specific month
        filtered_df = df[df['Month'] == month]
        
        if not filtered_df.empty:
            credit_df = filtered_df.query('Amount.str.contains("\+")')
            debit_df = filtered_df.query('Amount.str.contains("-")')

            cr_count = len(credit_df)
            db_count = len(debit_df)
            if cr_count > 0:
                cr_sum = credit_df['Amount'].str.replace("\+", "").str.replace(",", "").astype(float).sum()
            else:
                cr_sum = 0

            if db_count > 0:
                db_sum = debit_df['Amount'].str.replace("-", "").str.replace(",", "").astype(float).sum()
            else:
                db_sum = 0
            if '-' in filtered_df.iloc[0]['Amount']:
                begin = filtered_df.iloc[0]['Balance'] + float(filtered_df.iloc[0]['Amount'].replace("-", "").replace(",", ""))
            elif '+' in filtered_df.iloc[0]['Amount']:
                begin = filtered_df.iloc[0]['Balance'] - float(filtered_df.iloc[0]['Amount'].replace("+", "").replace(",", ""))
            dict_data[month] = {
                'BEGINNING BALANCE': round(begin,2),
                'CR_Transactions': cr_count,
                'CR_Amount': round(cr_sum,2),
                'DB_Transactions': db_count,
                'DB_Amount': round(db_sum,2),
                'ENDING BALANCE': filtered_df.iloc[-1]['Balance']
            }
        else:
            print(f"No data available for {month}")

    return dict_data
