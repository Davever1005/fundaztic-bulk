import pandas as pd
import re

def RHB_find_next_one(my_list, index):
    DATE_REGEX = r'\w{3}\d{2}|\d{2}\w{3}'
    AMOUNT_REGEX = r'\.\d{2}|\.\d{2}-|\d{1}\.\d{1}'
    for i in range(index + 1, len(my_list)):
        elements = my_list[i].split()
        if my_list[i] == 'Tarikh Diskripsi Cek/NomborSiri Debit Kredit Baki' or my_list[i] == 'Tarikh Diskripsi Cek/ Nombor Siri Debit Kredit Baki':
            return i
        elif my_list[i] == 'Date Description Cheque/Serial No Debit Credit Balance':
            if my_list[i+1] == 'Tarikh Diskripsi Cek/NomborSiri Debit Kredit Baki' or my_list[i+1] == 'Tarikh Diskripsi Cek/ Nombor Siri Debit Kredit Baki':
                return i + 1
            else:
                return i
    return -1

def add_year(my_list):
    DATE_REGEX = r'\w{3}\d{2}|\d{2}\w{3}'
    AMOUNT_REGEX = r'\.\d{2}|\.\d{2}-|\d{1}\.\d{1}'
    months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    pattern = r'\w{3} \d{2}, \d{4} to \w{3} \d{2}, \d{4} \d{1} of \d{1}'
    year = None
    for i in range(len(my_list)):
        date_idx = None
        elements = my_list[i].split()
        if len(elements)>0:
            if ('Statement Period' in my_list[i] or 'StatementPeriod' in my_list[i]) and re.match(r'\d{2}',elements[-1][-2:]):
                year = elements[-1][-2:]
            elif re.match(pattern, my_list[i]):
                year = elements[-4][-2:]
            elif len(elements) > 2:
                if any(month in elements[0].upper() for month in months) and len(elements[0])==3:
                    date_idx = 2
                elif any(month in elements[0].upper() for month in months) and len(elements[0])>3:
                    date_idx = 1
                elif any(month in elements[1].upper() for month in months) and len(elements[0]):
                    date_idx = 2
                if date_idx and re.match(DATE_REGEX, "".join(elements[0:date_idx]).replace(" ", "")[0:5]) and (re.match(AMOUNT_REGEX, elements[-1][-3:]) or re.match(AMOUNT_REGEX, elements[-1][-4:])) and re.match(AMOUNT_REGEX, elements[-2][-3:]):
                    elements[0] = "".join(elements[0:date_idx]).replace(" ", "")[0:5] + str(year)
                    elements[1:date_idx] = " "
                    my_list[i] = " ".join(elements)

def RHB_process_rows(rows,bal, sort):
    DATE_REGEX = r'\w{3}\d{2}|\d{2}\w{3}'
    AMOUNT_REGEX = r'\.\d{2}|\.\d{2}-|\d{1}\.\d{1}'
    KEYWORDS_TO_REMOVE = ["Member of PIDM", "B/F BALANCE", "Protected by PIDM", 'IMPORTANTNOTES', 'B/FBALANCE', 'C/FBALANCE']
    data = {}
    transaction_number = 1
    transaction = None
    test = 0
    previous_balance = None
    b = 0
    date_idx = None
    months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

    for row in rows:
        elements = row.split()  # Split the row into elements
        date_idx = None
        if previous_balance == None:
            previous_balance = round(float(bal[0][0].split()[-1].replace(",", "")),2)
        if elements:
            if len(elements) > 2:
                if any(month in elements[0].upper() for month in months) and len(elements[0])==3:
                    date_idx = 2
                elif any(month in elements[0].upper() for month in months) and len(elements[0])>3:
                    date_idx = 1
                elif any(month in elements[1].upper() for month in months) and len(elements[0]):
                    date_idx = 2
                if date_idx and re.match(DATE_REGEX, "".join(elements[0:date_idx]).replace(" ", "")[0:5]) and (re.match(AMOUNT_REGEX, elements[-1][-3:]) or re.match(AMOUNT_REGEX, elements[-1][-4:])) and re.match(AMOUNT_REGEX, elements[-2][-3:]):
                    # Start of a new transaction
                    test = 1
                    if transaction is not None:
                        data[f"{transaction_number}"] = transaction
                        transaction_number += 1

                    matching_indices = [idx for idx, el in reversed(list(enumerate(elements))) if (re.match(AMOUNT_REGEX, el[-3:]) or re.match(AMOUNT_REGEX, el[-4:]))]
                    balance_index = matching_indices[0] if matching_indices else None
                    if balance_index:
                        if "-" in elements[balance_index]:
                            bal = -float(elements[balance_index].replace(",", "").replace("-", "")) - previous_balance
                            balance = -float(elements[balance_index].replace(",", "").replace("-", ""))
                        else:
                            bal = float(elements[balance_index].replace(",", "")) - previous_balance
                            balance = float(elements[balance_index].replace(",", ""))
                        if len(matching_indices)==2:
                            amt = float(elements[balance_index-1].replace(",", ""))
                            description_end = balance_index-1
                        elif len(matching_indices)==3:
                            amt = float(elements[balance_index-2].replace(",", ""))
                            description_end = balance_index-2
                        else:
                            amt = 0
                            description_end = balance_index
                        description = " ".join(elements[date_idx:description_end])  # Join elements as description
                        transaction = {
                            "Date": "".join(elements[0:date_idx]),
                            "Description": description,
                            "Amount": amt,
                            "Balance": balance
                        }
                        previous_balance = transaction["Balance"]
                    else:
                        print('no balance found')

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


def RHB_main(rows, bal, sort):
    KEYWORDS_TO_REMOVE = ["Member of PIDM", "Protected by PIDM", 'IMPORTANTNOTES', 'MemberofPIDM/AhliPIDM', 'maklumat lanjut.']
    add_year(rows)
    indices_containing = [i for i, s in enumerate(rows) if any(keyword.lower() in s.lower() for keyword in KEYWORDS_TO_REMOVE)]
    indices_containing.sort(reverse=True)

    for index in indices_containing:
        if 0 <= index < len(rows):
            result_index = RHB_find_next_one(rows, index)
            if result_index != -1:
                del rows[index:result_index]
            else:
                del rows[index:]
    try:
        date_format = '%b%d'
        for i in range(len(bal)):
            if len(bal[i][1].split()[0]) <= 3:
                date_string = bal[i][1].split()[0] + bal[i][1].split()[1]
            else:    
                date_string = bal[i][1].split()[0]

            # Convert the date string to pandas datetime object
            date_object = pd.to_datetime(date_string, format=date_format)

            # Extract the month from the pandas datetime object
            month_only = date_object.month

            # Create a new tuple with the month
            bal[i] = (bal[i][0].split()[-1].replace(",", ""), month_only)
        bal = sorted(bal, key=lambda x: x[1])
    except Exception as e:
        print(e)

    try:
        date_format = '%d%b'
        for i in range(len(bal)):
            if len(bal[i][1].split()[0]) <= 3:
                date_string = bal[i][1].split()[0] + bal[i][1].split()[1]
            else:    
                date_string = bal[i][1].split()[0]

            # Convert the date string to pandas datetime object
            date_object = pd.to_datetime(date_string, format=date_format)

            # Extract the month from the pandas datetime object
            month_only = date_object.month

            # Create a new tuple with the month
            bal[i] = (bal[i][0].split()[-1].replace(",", ""), month_only)
        bal = sorted(bal, key=lambda x: x[1])
    except Exception as e:
        print(e)
    data = RHB_process_rows(rows,bal, sort)

    df = pd.DataFrame.from_dict(data, orient='index')

    if sort == '-1':
        previous_balance = None
        df['Idx'] = df.index
        df['Idx'] = pd.to_numeric(df['Idx'], errors='coerce')
        current_month = None
        i = 0
        try:
            date_format = '%b%d%y'
            df['Date2'] = pd.to_datetime(df['Date'], format=date_format)
            df['Month'] = df['Date2'].dt.month
            df = df.sort_values(by = ['Date2', 'Idx'], ascending = [True, False])
            df["Sign"] = df.apply(lambda _: ' ', axis=1)
            df["Amt"] = df.apply(lambda _: ' ', axis=1)
            bal = sorted(bal, key=lambda x: x[1])
            for index, row in df.iterrows():
                date_str = row['Month']
                if current_month is None or date_str != current_month:
                    # Update current month and reset previous balance
                    current_month = date_str
                    find_balance = next((item[0] for item in bal if item[1] == current_month), None)
                    if find_balance:
                        previous_balance = find_balance
                diff = float(row['Balance']) - float(previous_balance)
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

        try:
            date_format = '%d%b'
            df['Date2'] = pd.to_datetime(df['Date'], format=date_format)
            df['Month'] = df['Date2'].dt.month
            df = df.sort_values(by = ['Date2', 'Idx'], ascending = [True, False])
            df["Sign"] = df.apply(lambda _: ' ', axis=1)
            df["Amt"] = df.apply(lambda _: ' ', axis=1)
            bal = sorted(bal, key=lambda x: x[1])
            for index, row in df.iterrows():
                date_str = row['Month']
                if current_month is None or date_str != current_month:
                    # Update current month and reset previous balance
                    current_month = date_str
                    find_balance = next((item[0] for item in bal if item[1] == current_month), None)
                    if find_balance:
                        previous_balance = find_balance
                diff = float(row['Balance']) - float(previous_balance)
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
        current_month = None
        i = 0
        previous_balance = None
        df['Idx'] = df.index
        df['Idx'] = pd.to_numeric(df['Idx'], errors='coerce')
        try:
            date_format = '%b%d%y'
            df['Date2'] = pd.to_datetime(df['Date'], format=date_format)
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
                diff = float(row['Balance']) - float(previous_balance)
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

        try:
            date_format = '%d%b%y'
            df['Date2'] = pd.to_datetime(df['Date'], format=date_format)
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
                diff = float(row['Balance']) - float(previous_balance)
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
            
    df['Amount2'] = df.Amt * df.Sign

    return df, bal

