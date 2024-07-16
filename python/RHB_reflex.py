import pandas as pd
import re

def RHB_find_next_one(my_list, index):
    DATE_REGEX = r'\w{3}\d{2}|\d{2}\w{3}'
    AMOUNT_REGEX = r'\.\d{2}|\.\d{2}-|\d{1}\.\d{1}'
    for i in range(index + 1, len(my_list)):
        elements = my_list[i].split()
        if my_list[i] == "Date BranchDescription Sender's Reference 1 / Reference 2 / RefNum Amount (DR) Amount (CR) Balance":
            if i < len(my_list):
                return i + 1
            else:
                return i
    return -1


def RHB_process_rows(rows,bal, sort):
    DATE_REGEX = r'\d{2}-\d{2}-\d{4}'
    AMOUNT_REGEX = r'\.\d{2}\+|\.\d{2}-|\.\d{2}'
    KEYWORDS_TO_REMOVE = ['www.rhbgroup.com']
    data = {}
    transaction_number = 1
    transaction = None
    test = 0
    for row in rows:
        elements = row.split()  # Split the row into elements
        if elements:
            elements = [elem for elem in elements if elem != '-']
            if re.match(DATE_REGEX, elements[0])  and re.match(AMOUNT_REGEX, elements[-1][-4:]) and re.match(AMOUNT_REGEX, elements[-2][-3:]):
                # Start of a new transaction
                test = 1
                if transaction is not None:
                    data[f"{transaction_number}"] = transaction
                    transaction_number += 1
                if elements[-1][-1] == "-":
                    balance = -float(elements[-1].replace(",", "").replace("+", "").replace("-",""))
                else:
                    balance = float(elements[-1].replace(",", "").replace("+", "").replace("-",""))
                amt = float(elements[-2].replace(",", "").replace("+", "").replace("-",""))
                description = " ".join(elements[1:-2])  # Join elements as description
                transaction = {
                    "Date": elements[0],
                    "Description": description,
                    "Amount": amt,
                    "Balance": balance
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


def RHB_reflex_main(rows, bal, sort):
    KEYWORDS_TO_REMOVE = ["www.rhbgroup.com"]
    indices_containing = [i for i, s in enumerate(rows) if any(keyword.lower() in s.lower() for keyword in KEYWORDS_TO_REMOVE)]
    indices_containing.sort(reverse=True)
    
    for index in indices_containing:
        if 0 <= index < len(rows):
            result_index = RHB_find_next_one(rows, index)
            if result_index != -1:
                del rows[index:result_index]
            else:
                del rows[index:]

    # List to store extracted values
    transformed_data = []

    # Extract balance and month index from each string
    for string in bal:
        if string.split()[-1][-1] == '-':
            balance = -float(string.split()[-1][0:-1].replace(",", ""))
        else:
            balance = float(string.split()[-1][0:-1].replace(",", ""))
        if 'january' in string.lower():
            month_index = 1
        elif 'february' in string.lower():
            month_index = 2
        elif 'march' in string.lower():
            month_index = 3
        elif 'april' in string.lower():
            month_index = 4
        elif 'may' in string.lower():
            month_index = 5
        elif 'june' in string.lower():
            month_index = 6
        elif 'july' in string.lower():
            month_index = 7
        elif 'august' in string.lower():
            month_index = 8
        elif 'september' in string.lower():
            month_index = 9
        elif 'october' in string.lower():
            month_index = 10
        elif 'november' in string.lower():
            month_index = 11
        elif 'december' in string.lower():
            month_index = 12
        else:
            month_index = None
        transformed_data.append((balance, month_index))
    bal = transformed_data
    data = RHB_process_rows(rows,bal, sort)

    df = pd.DataFrame.from_dict(data, orient='index')

    if sort == '-1':
        previous_balance = None
        df['Idx'] = df.index
        df['Idx'] = pd.to_numeric(df['Idx'], errors='coerce')
        current_month = None
        i = 0
        try:
            date_format = '%d-%m-%Y'
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
            date_format = '%d-%m-%Y'
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

