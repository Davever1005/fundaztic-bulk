def type(df):
    # List of transaction types and their keywords
    transaction_types = {
        "Cheque": ["CHQ"],
        "Cash": ["CASH DEPOSIT"],
        "QR": ["QR P2P", "QRPOS", "MAE QR", "DuitNow QR"],
        "E-wallet": ["GPAY NETWORK", "BIGPAY MALAYSIA", "TNG DIGITAL", "AXIATA DIGITAL", "SHOPEEPAY"],
        "DuitNow": ["DUITNOW"],
        "Other merchants": ["CR/CARD SALES", "DR/CARD SALES"],
        "TOD/TEOD Charges": ["TOD/TEOD"]
    }

    # Initialize dictionaries to store counts, debit sums, and credit sums
    type_data = {}

    # Iterate through transaction types and calculate counts, debit sums, and credit sums
    for type_name, keywords in transaction_types.items():
        count = sum(df['Description'].str.replace(" ", "").str.upper().str.contains(keyword.replace(" ", "").upper()).sum() for keyword in keywords)

        # Initialize debit and credit sums
        debit_sum = 0
        credit_sum = 0

        # Iterate through keywords to calculate debit and credit sums
        for keyword in keywords:
            debit_sum += df.loc[df['Description'].str.replace(" ", "").str.upper().str.contains(keyword.replace(" ", "").upper()) & (df['Amount2'] < 0), 'Amount2'].sum()
            credit_sum += df.loc[df['Description'].str.replace(" ", "").str.upper().str.contains(keyword.replace(" ", "").upper()) & (df['Amount2'] >= 0), 'Amount2'].sum()
        
        type_data[type_name] = {
            "count": count,
            "debit_sum": abs(debit_sum),
            "credit_sum": abs(credit_sum)
        }

    return type_data