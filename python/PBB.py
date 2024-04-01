import re
import pandas as pd


def PBB_find_next_one(my_list, index):
    DATE_REGEX = r'\d{2}/\d{2}'
    AMOUNT_REGEX = r'\d\.\d{2}'

    date = ""
    for i in range(index + 1, len(my_list)):
        elements = my_list[i].split()
        if re.match(DATE_REGEX, my_list[i][0:5]):
            date = my_list[i][0:5]
        if my_list[i] == 'DATE TRANSACTION DEBIT CREDIT BALANCE':
            if 'Balance From Last Statement' not in my_list[i+1]:
                return (date,i + 1)
            else:
                return (date,i + 2)
        elif re.match(AMOUNT_REGEX, elements[-1][-4:]) and re.match(AMOUNT_REGEX, elements[-2][-4:]):
            return (date, i)  # Return the index of the first occurrence of 1 after the specified index
        elif elements[-1] == 'OD':
            if re.match(AMOUNT_REGEX, elements[-2][-4:]) and re.match(AMOUNT_REGEX, elements[-3][-4:]):
                return (date, i)  # Return the index of the first occurrence of 1 after the specified index
    return (date, -1)

def add_year(my_list):
    DATE_REGEX = r'\d{2}/\d{2}'
    AMOUNT_REGEX = r'\d\.\d{2}'
    year = None
    for i in range(len(my_list)):
        elements = my_list[i].split()
        if len(elements)>0:
            if 'Statement Date' in my_list[i] and re.match(r'\d{4}',elements[-1]):
                year = elements[-1]
            elif re.match(DATE_REGEX, elements[0]) and re.match(AMOUNT_REGEX, elements[-2][-4:]):
                elements[0] = elements[0] + '/' + str(year)
                my_list[i] = " ".join(elements)

def PBB_process_rows(rows, bal, sort):
    DATE_REGEX = r'\d{2}/\d{2}'
    AMOUNT_REGEX = r'\d\.\d{2}'
    KEYWORDS_TO_REMOVE = ["Penyata ini dicetak melalui komputer", "Baki Harian Dan Penutup Meliputi Semua"]

    data = {}
    transaction_number = 1
    transaction = None
    test = 0

    for row in rows:
        elements = row.split()  # Split the row into elements
        if elements:
            if len(elements)>=3:
                if (re.match(AMOUNT_REGEX, elements[-1][-4:]) and re.match(AMOUNT_REGEX, elements[-2][-4:])) or (re.match(AMOUNT_REGEX, elements[-3][-4:]) and re.match(AMOUNT_REGEX, elements[-2][-4:]) and re.match('OD', elements[-1])):
                    test = 1
                    if transaction is not None:
                        data[f"{transaction_number}"] = transaction
                        transaction_number += 1
                    if 'OD' in elements[-1]:
                        balance = -float(elements[-2].replace(",", ""))
                        amt = float(elements[-3].replace(",", ""))
                        description_end = -3
                    else:
                        balance = float(elements[-1].replace(",", ""))
                        amt = float(elements[-2].replace(",", ""))
                        description_end = -2
                    if re.match(DATE_REGEX, elements[0]):
                        date = elements[0]
                        description_start = 1
                    else:
                        description_start = 0

                    description = " ".join(elements[description_start:description_end])  # Join elements as description
                    transaction = {
                        "Date": date,
                        "Description": description,
                        "Amount": amt,
                        "Balance": round(float(balance), 2)
                    }
                elif test == 1 and all(s not in "".join(elements) for s in KEYWORDS_TO_REMOVE):
                    # This is a continuation of the description, skip if "**"
                    if "Description" not in transaction:
                        transaction["Description"] = " ".join(elements)
                    else:
                        transaction["Description"] += " " + " ".join(elements)
                else:
                    test = 0

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


def PBB_main(rows, bal, sort):
    DATE_REGEX = r'\d{2}/\d{2}'
    KEYWORDS_TO_REMOVE = ["Penyata ini dicetak melalui komputer", "Baki Harian Dan Penutup Meliputi Semua"]
    add_year(rows)

    indices_containing = [i for i, s in enumerate(rows) if any(keyword.lower() in s.lower() for keyword in KEYWORDS_TO_REMOVE)]
    indices_containing.sort(reverse=True)

    new_bal = []
    for index in indices_containing:
        if 0 <= index < len(rows):
            date, result_index = PBB_find_next_one(rows, index)
            if result_index != -1:
                if not re.match(DATE_REGEX, rows[result_index][0:5]):
                    rows[result_index] = " ".join([date, rows[result_index]])
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

            if 'OD' in bal[i][0].split()[-1]:
                if bal[i][0].split()[-1] == 'OD':
                    bal[i] = (" ".join(bal[i][0].split()[0:-2]) + ' -' + bal[i][0].split()[-2],month_only)
                else:
                    bal[i] = (" ".join(bal[i][0].split()[0:-1]) + ' -' + bal[i][0].split()[-1].replace("OD", ""),month_only)
            new_bal.append((float(bal[i][0].split()[-1].replace(',', "")), month_only))
        bal = sorted(bal, key=lambda x: x[1])
    except:
        pass

    try:
        date_format = '%d/%m'
        for i in range(len(bal)):
            date_string = bal[i][1].split()[0]

            # Convert the date string to pandas datetime object
            date_object = pd.to_datetime(date_string, format=date_format)

            # Extract the month from the pandas datetime object
            month_only = date_object.month

            if 'OD' in bal[i][0].split()[-1]:
                if bal[i][0].split()[-1] == 'OD':
                    bal[i] = (" ".join(bal[i][0].split()[0:-2]) + ' -' + bal[i][0].split()[-2],month_only)
                else:
                    bal[i] = (" ".join(bal[i][0].split()[0:-1]) + ' -' + bal[i][0].split()[-1].replace("OD", ""),month_only)
            new_bal.append((bal[i][0].split()[-1].replace(',', ""), month_only))
        bal = sorted(bal, key=lambda x: x[1])
    except Exception as e:
        print(e)
    bal = new_bal
    
    rows = [item for item in rows if 'Closing Balance' not in item]
    rows = [item for item in rows if 'Balance From' not in item]
    rows = [item for item in rows if 'Balance B/F' not in item]
    rows = [item for item in rows if 'Balance C/F' not in item]
    data = PBB_process_rows(rows, bal, sort)
    df = pd.DataFrame.from_dict(data, orient='index')
    if sort == '-1':
        i = 0
        previous_balance = None
        df['Idx'] = df.index
        df['Idx'] = pd.to_numeric(df['Idx'], errors='coerce')
        current_month = None
        try:
            date_format = '%d/%m/%Y'
            df['Date2'] = pd.to_datetime(df['Date'], format=date_format)
            df['Month'] = df['Date2'].dt.month
            df = df.sort_values(by = ['Date2', 'Idx'], ascending = [True, False])
            df["Sign"] = df.apply(lambda _: ' ', axis=1)
            df["Amt"] = df.apply(lambda _: ' ', axis=1)
            bal = sorted(bal, key=lambda x: x[1])
            for index, row in df.iterrows():
                date_str = row['Month']
                if current_month is None or date_str.month != current_month:
                    # Update current month and reset previous balance
                    current_month = date_str.month
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
            pass

    elif sort == '1':
        i = 0
        previous_balance = None
        df['Idx'] = df.index
        df['Idx'] = pd.to_numeric(df['Idx'], errors='coerce')
        current_month = None
        try:
            date_format = '%d/%m/%Y'
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
            pass
    
    df['Amount2'] = df.Amt * df.Sign

    return df, bal

