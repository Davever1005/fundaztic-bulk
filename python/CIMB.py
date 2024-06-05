import re
import pandas as pd


def CIMB_find_next_one(my_list, index):
    DATE_REGEX = r'\d{2}/\d{2}|\d{2}/\d{2}/\d{4}'
    AMOUNT_REGEX = r'\.\d{2}'
    BAL_REGEX = r'\.\d{2}'
    for i in range(index + 1, len(my_list)):
        elements = my_list[i].split()
        if my_list[i] == 'Tarikh Diskripsi No Cek / Rujukan Pengeluaran Deposit Baki':
            if i + 2 < len(my_list):
                if 'Opening Balance' not in my_list[i+2]:
                    return i + 2
                else:
                    return i + 3
        elif re.match(DATE_REGEX, my_list[i][0:5]) and re.match(BAL_REGEX, elements[-1][-3:]) and re.match(AMOUNT_REGEX, elements[-2][-3:]):
            return i  # Return the index of the first occurrence of 1 after the specified index
    return -1

def CIMB_process_rows(rows, bal, sort):
    DATE_REGEX = r'\d{2}/\d{2}|\d{2}/\d{2}/d{4}'
    AMOUNT_REGEX = r'\.\d{2}'
    BAL_REGEX = r'\.\d{2}'
    KEYWORDS_TO_REMOVE = ['CONTINUE NEXT PAGE', 'CLOSING BALANCE / BAKI PENUTUP']
    data = {}
    transaction_number = 1
    transaction = None
    test = 0
    for row in rows:
        elements = row.split()  # Split the row into elements
        if elements:
            if re.match(DATE_REGEX, elements[0])  and re.match(BAL_REGEX, elements[-1][-3:]) and re.match(AMOUNT_REGEX, elements[-2][-3:]):
                # Start of a new transaction
                test = 1
                if transaction is not None:
                    data[f"{transaction_number}"] = transaction
                    transaction_number += 1

                matching_indices = [idx for idx, el in reversed(list(enumerate(elements))) if re.match(r'\.\d{2}', el[-3:])]
                balance_index = matching_indices[0] if matching_indices else None
                if balance_index:
                    if len(matching_indices)==2:
                        amt = float(elements[balance_index-1].replace(",", ""))
                        description_end = balance_index-1
                    elif len(matching_indices)==3:
                        amt = float(elements[balance_index-2].replace(",", ""))
                        description_end = balance_index-2
                    else:
                        amt = 0
                        description_end = balance_index
                    description = " ".join(elements[1:description_end])  # Join elements as description
                    transaction = {
                        "Date": elements[0],
                        "Description": description,
                        "Amount": amt,
                        "Balance": float(elements[balance_index].replace(",", "")),
                    }

            elif test == 1 and all(s not in "".join(elements) for s in KEYWORDS_TO_REMOVE):
                # This is a continuation of the description, skip if "**"
                if "Description" not in transaction:
                    transaction["Description"] = " ".join(elements)
                else:
                    transaction["Description"] += " " + " ".join(elements)
            else:
                test = 0

        # Append the last transaction to the data dictionary for the current page
        if transaction is not None:
            data[f"{transaction_number}"] = transaction


    return data


def CIMB_main(rows, bal, sort):

    KEYWORDS_TO_REMOVE = ['CONTINUE NEXT PAGE', 'CLOSING BALANCE / BAKI PENUTUP']

    indices_containing = [i for i, s in enumerate(rows) if any(keyword.lower() in s.lower() for keyword in KEYWORDS_TO_REMOVE)]
    indices_containing.sort(reverse=True)

    for index in indices_containing:
        if 0 <= index < len(rows):
            result_index = CIMB_find_next_one(rows, index)
            if result_index != -1:
                del rows[index:result_index]
            else:
                del rows[index:]

    try:
        date_format = '%d/%m/%Y'
        for i in range(len(bal)):
            date_string = bal[i][1].split()[0]

            # Convert the date string to pandas datetime object
            date_object = pd.to_datetime(date_string, format=date_format)

            # Extract the month from the pandas datetime object
            month_only = date_object.month

            # Create a new tuple with the month
            bal[i] = (bal[i][0].split()[-1].replace(",", ""), month_only)
        bal = sorted(bal, key=lambda x: x[1])
    except Exception as e:
            pass
    data = CIMB_process_rows(rows, bal, sort)

    df = pd.DataFrame.from_dict(data, orient='index')
    if sort == '-1':
        i = 0
        previous_balance = None
        df['Idx'] = df.index
        df['Idx'] = pd.to_numeric(df['Idx'], errors='coerce')
        current_month = None
        try:
            date_format = '%d/%m/%Y'
            df['Date2'] = pd.to_datetime(df['Date'], format=date_format, errors='coerce')
            df_null_date = df[df['Date2'].isnull()]
            df = df.dropna(subset=['Date2'])  # DataFrame with valid dates
            df['Month'] = df['Date2'].dt.month
            df = df.sort_values(by = ['Date2', 'Idx'], ascending = [True, False])
            df["Sign"] = df.apply(lambda _: ' ', axis=1)
            df["Amt"] = df.apply(lambda _: ' ', axis=1)
            for index, row in df.iterrows():
                date_str = row['Month']
                if current_month is None or date_str != current_month:
                    # Update current month and reset previous balance
                    current_month = date_str
                    find_balance = next((item[0] for item in bal if item[1] == current_month), None)
                    if find_balance:
                        previous_balance = find_balance
                diff = row['Balance'] - float(previous_balance)
                A = str(row['Amount'])
                if diff < 0:
                    df.loc[index, "Amount"] = f'{float(A):.2f}-'
                    df.loc[index, "Sign"] = -1
                    df.loc[index, "Amt"] = round(float(A), 2)
                else:
                    df.loc[index, "Amount"] = f'{float(A):.2f}+'
                    df.loc[index, "Sign"] = 1
                    df.loc[index, "Amt"] = round(float(A), 2)
                previous_balance = row['Balance']
        except Exception as e:
            print(e)

    elif sort == '1':
        i = 0
        previous_balance = None
        df['Idx'] = df.index
        df['Idx'] = pd.to_numeric(df['Idx'], errors='coerce')
        current_month = None
        try:
            date_format = '%d/%m/%Y'
            df['Date2'] = pd.to_datetime(df['Date'], format=date_format, errors='coerce')
            df_null_date = df[df['Date2'].isnull()]
            df = df.dropna(subset=['Date2'])  # DataFrame with valid dates
            df['Month'] = df['Date2'].dt.month
            df = df.sort_values(by = ['Date2', 'Idx'], ascending = [True, True])
            df["Sign"] = df.apply(lambda _: ' ', axis=1)
            df["Amt"] = df.apply(lambda _: ' ', axis=1)
            for index, row in df.iterrows():
                date_str = row['Month']
                if current_month is None or date_str != current_month:
                    # Update current month and reset previous balance
                    current_month = date_str
                    find_balance = next((item[0] for item in bal if item[1] == current_month), None)
                    if find_balance:
                        previous_balance = find_balance
                diff = row['Balance'] - float(previous_balance)
                A = str(row['Amount'])
                if diff < 0:
                    df.loc[index, "Amount"] = f'{float(A):.2f}-'
                    df.loc[index, "Sign"] = -1
                    df.loc[index, "Amt"] = round(float(A), 2)
                else:
                    df.loc[index, "Amount"] = f'{float(A):.2f}+'
                    df.loc[index, "Sign"] = 1
                    df.loc[index, "Amt"] = round(float(A), 2)
                previous_balance = row['Balance']
        except Exception as e:
            pass
    df['Amount2'] = df.Amt * df.Sign

    return df, bal, df_null_date
