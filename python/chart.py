import pandas as pd
from collections import defaultdict
import calendar

def plot_to_html_image(df, bal):
    # Ensure all days are present in the data
    updated_data = pd.DataFrame(columns=['Date2', 'Balance'])
    for month in df['Date2'].dt.to_period("M").unique():
        month_df = pd.DataFrame({'Date2': pd.date_range(month.start_time, month.end_time)})
        month_df['Balance'] = month_df['Date2'].apply(lambda x: df.loc[df['Date2'].dt.date == x.date(), 'Balance'].values[-1] if not df.loc[df['Date2'].dt.date == x.date()].empty else None)
        updated_data = pd.concat([updated_data, month_df])
    if pd.isna(updated_data['Balance'].iloc[0]):
        month = int(updated_data['Date2'].iloc[0].month)
        for balance, m in bal:
            if month == m:
                updated_data['Balance'].iloc[0] = float(balance)
                break
    updated_data['Balance'].fillna(method='ffill', inplace=True)
    # Calculate average daily balance for each month
    average_daily_balances = updated_data.groupby(updated_data['Date2'].dt.strftime('%m%y').astype(int))['Balance'].mean().to_dict()

    # Updated data with all days included
    chart_data = {
        'Labels': updated_data['Date2'].dt.strftime('%d/%m/%y').unique().tolist(),
        'Data': updated_data['Balance'].tolist()
    }
    
    return chart_data, average_daily_balances