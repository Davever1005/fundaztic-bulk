import pandas as pd
from fuzzywuzzy import fuzz
from collections import defaultdict


def find_repeat(final_df):
    # Create a dictionary to store transactions based on their descriptions
    transaction_dict = {}

    # Threshold for fuzzy matching (adjust as needed)
    threshold = 80

    # Iterate through each row in the DataFrame
    for index, row in final_df.iterrows():
        description = row["Description"].lower()  # Convert to lowercase

        # Check if there's a similar description in the dictionary
        found_similar = False
        for desc_key in transaction_dict.keys():
            if fuzz.ratio(description, desc_key.lower()) >= threshold:  # Convert to lowercase
                transaction_dict[desc_key].append(row)
                found_similar = True
                break

        # If no similar description is found, create a new entry
        if not found_similar:
            transaction_dict[description] = [row]

    # Filter out descriptions with only one transaction (not repeated)
    repeated_transactions = {desc: trans_list for desc, trans_list in transaction_dict.items() if len(trans_list) > 1}

    sorted_repeated_transactions = dict(sorted(repeated_transactions.items(), key=lambda item: len(item[1]), reverse=True))
    # Create a dictionary to store DataFrames for each unique count
    tables_by_count = defaultdict(list)

    # Populate the tables_by_count dictionary
    for description, transactions in sorted_repeated_transactions.items():
        count = len(transactions)
        for transaction in transactions:
            amount = transaction['Amount']
            credit = amount[:-1] if amount.endswith('+') else ''
            debit = amount[:-1] if amount.endswith('-') else ''
            tables_by_count[f'{count},{description}'].append({
                'Description': transaction['Description'],
                'Date': transaction['Date'],
                'Credit': credit,
                'Debit': debit
            })

    # Create HTML tables for each count
    html_tables = {}
    for title, data in tables_by_count.items():
        count = title.split(',')[0]
        df = pd.DataFrame(data)
        df = df.sort_values('Date')
        html_tables[count] = df.to_html(classes='table table-striped table-bordered', index=False)

    return html_tables
