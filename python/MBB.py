import re
import json
import csv
from datetime import datetime
import pandas as pd
import pandas as pd


def MBB_find_next_one(my_list, index):
    DATE_REGEX = r'\d{2}/\d{2}'
    AMOUNT_REGEX = r'\.\d{2}[+-]'
    BAL_REGEX = r'\.\d{2}|\.\d{2}DR'
    for i in range(index + 1, len(my_list)):
        elements = my_list[i].split()
        if my_list[i] == 'ENTRY DATE VALUE DATE TRANSACTION DESCRIPTION TRANSACTION AMOUNT STATEMENT BALANCE' or my_list[i] ==  'ENTRY DATE VALUE DATE TRANSACTION DESCRIPTION GST TYPE TRANSACTION AMOUNT STATEMENT BALANCE' or my_list[i] ==  'ENTRY DATE TRANSACTION DESCRIPTION GST TYPE TRANSACTION AMOUNT STATEMENT BALANCE' or my_list[i] ==  'ENTRY DATE TRANSACTION DESCRIPTION TRANSACTION AMOUNT STATEMENT BALANCE':
            return i
        elif re.match(DATE_REGEX, elements[0]) and (re.match(BAL_REGEX, elements[-1][-3:]) or re.match(BAL_REGEX, elements[-1][-5:])) and re.match(AMOUNT_REGEX, elements[-2][-4:]):
            return i
    return -1

def add_year(my_list):
    DATE_REGEX = r'^\d{2}/\d{2}$'
    AMOUNT_REGEX = r'\.\d{2}[+-]'
    BAL_REGEX = r'\.\d{2}|\.\d{2}DR'
    year = None
    for i in range(len(my_list)):
        elements = my_list[i].split()
        if len(elements)>1:
            if re.match(r'\d{2}/\d{2}/\d{2}',elements[-1]) and elements[-2] == ':':
                year = elements[-1][-2:]
            elif re.match(DATE_REGEX, elements[0]) and (re.match(BAL_REGEX, elements[-1][-3:]) or re.match(BAL_REGEX, elements[-1][-5:])) and re.match(AMOUNT_REGEX, elements[-2][-4:]):
                elements[0] = elements[0] + '/' + str(year)
                my_list[i] = " ".join(elements)


def MBB_process_rows(rows, bal):
    DATE_REGEX = r'\d{2}/\d{2}/\d{2}'
    AMOUNT_REGEX = r'\.\d{2}[+-]'
    BAL_REGEX = r'\.\d{2}|\.\d{2}DR'
    KEYWORDS_TO_REMOVE = ["Perhation / Note", "BAKI", "BAKILEGAR", "ENDING", "BEGINNING BALANCE", "ENTRY DATE VALUE DATE TRANSACTION DESCRIPTION TRANSACTION AMOUNT STATEMENT BALANCE"]
    data = {}
    transaction_number = 1
    transaction = None
    test = 0
    previous_balance = None

    for index, row in enumerate(rows):
        elements = row.split()  # Split the row into elements
        if previous_balance == None:
            previous_balance = round(float(bal[0][0]),2)
            
        if elements:
            try:
                if re.match(DATE_REGEX, elements[0]) and (re.match(BAL_REGEX, elements[-1][-3:]) or re.match(BAL_REGEX, elements[-1][-5:])) and re.match(AMOUNT_REGEX, elements[-2][-4:]):
                    # Start of a new transaction
                    test = 1
                    if transaction is not None:
                        data[f"{transaction_number}"] = transaction
                        transaction_number += 1

                    amount_index = next((idx for idx, el in enumerate(elements) if re.match(AMOUNT_REGEX, el[-4:])), None)
                    if amount_index is None:
                        # No such element found, initialize description_end with a value that ensures it's not used
                        description_end = len(elements) - 2
                        amt = float(elements[description_end + 1].replace(",", "")) - previous_balance
                        if amt < 0:
                            amt = abs(amt)
                            A = f'{amt:.2f}-'
                            sign = -1
                        else:
                            A = f'{amt:.2f}+'
                            sign = 1
                        description = " ".join(elements[1:description_end+1])  # Join elements as description
                        if "DR" in elements[description_end + 1]:
                            B = elements[description_end + 1].replace("DR","")
                            B = float(B.replace(",",""))
                            B = -B
                            transaction = {
                                "Date": elements[0],
                                "Description": description,
                                "Amount": A,
                                "Balance": round(B, 2),
                                "Sign": sign,
                                "Amt": round(float(elements[description_end][0:-1].replace(",","")), 2)
                            }
                            previous_balance = transaction["Balance"]
                        else:
                            transaction = {
                                "Date": elements[0],
                                "Description": description,
                                "Amount": A,
                                "Balance": float(elements[description_end + 1].replace(",","")),
                                "Sign": sign,
                                "Amt": round(float(elements[description_end][0:-1].replace(",","")), 2)
                            }
                            previous_balance = transaction["Balance"]
                    else:
                        description_end = amount_index
                        description = " ".join(elements[1:description_end])  # Join elements as description
                        if elements[description_end][-1] == "-":
                            sign = -1
                        elif elements[description_end][-1] == "+":
                            sign = 1
                        if "DR" in elements[description_end + 1]:
                            B = elements[description_end + 1].replace("DR","")
                            B = float(B.replace(",",""))
                            B = -B
                            transaction = {
                                "Date": elements[0],
                                "Description": description,
                                "Amount": elements[description_end],
                                "Balance": round(B, 2),
                                "Sign": sign,
                                "Amt": round(float(elements[description_end][0:-1].replace(",","")), 2)
                                
                            }
                            previous_balance = transaction["Balance"]
                        else:
                            transaction = {
                                "Date": elements[0],
                                "Description": description,
                                "Amount": elements[description_end],
                                "Balance": float(elements[description_end + 1].replace(",","")),
                                "Sign": sign,
                                "Amt": round(float(elements[description_end][0:-1].replace(",","")), 2)
                            }
                            previous_balance = transaction["Balance"]
                elif re.match(DATE_REGEX, elements[0]) and (re.match(BAL_REGEX, elements[-1][-3:]) or re.match(BAL_REGEX, elements[-1][-5:])) and re.match(AMOUNT_REGEX, rows[index+1][-4:]):
                    test = 1
                    if transaction is not None:
                        data[f"{transaction_number}"] = transaction
                        transaction_number += 1


                    description_end = -2
                    description = " ".join(elements[1:-1])  # Join elements as description
                    if rows[index+1][-1] == "-":
                        sign = -1
                    elif rows[index+1][-1] == "+":
                        sign = 1
                    if "DR" in elements[-1]:
                        B = elements[-1].replace("DR","")
                        B = float(B.replace(",",""))
                        B = -B
                        transaction = {
                            "Date": elements[0],
                            "Description": description,
                            "Amount": rows[index+1],
                            "Balance": round(B, 2),
                            "Sign": sign,
                            "Amt": round(float(rows[index+1][0:-1].replace(",","")), 2)
                            
                        }
                        previous_balance = transaction["Balance"]
                    else:
                        transaction = {
                            "Date": elements[0],
                            "Description": description,
                            "Amount": rows[index+1],
                            "Balance": float(elements[-1].replace(",","")),
                            "Sign": sign,
                            "Amt": round(float(rows[index+1][0:-1].replace(",","")), 2)
                        }
                        previous_balance = transaction["Balance"]
                else:
                    # This is a continuation of the description, skip if "**"
                    if "Description" not in transaction:
                        transaction["Description"] = " ".join(elements)
                    else:
                        transaction["Description"] += " " + " ".join(elements)
            except Exception as e:
                print(e)
            

    # Append the last transaction to the data dictionary for the current page
    if transaction is not None:
        data[f"{transaction_number}"] = transaction

    return data

def MBB_main(rows, bal, sort):
    KEYWORDS_TO_REMOVE = ["BAKI LEGAR", "BAKILEGAR", "ENDING", "SINGLE ACCOUNT AND INCREASE", "THE PERSONAL DATA PROTECTION", "TOTAL DEBIT", "Perhation / Note"]
    DATE_REGEX = r'\d{2}/\d{2}'
    indices_containing = [i for i, s in enumerate(rows) if any(keyword.lower() in s.lower() for keyword in KEYWORDS_TO_REMOVE )]
    indices_containing.sort(reverse=True)
    add_year(rows)
    for index in indices_containing:
        if 0 <= index < len(rows):
            result_index = MBB_find_next_one(rows, index)
            if result_index != -1:
                del rows[index:result_index]
            else:
                del rows[index:]
    print(bal)
    new_bal = []
    for i in range(len(bal)):
        date_string = bal[i][1].split()[0][0:5]
        if i == len(bal):
            break
        if re.match(DATE_REGEX, date_string):
            try:
                date_format = '%d/%m/%Y'
                # Convert the date string to pandas datetime object
                date_object = pd.to_datetime(date_string, format=date_format)

                # Extract the month from the pandas datetime object
                month_only = date_object.month

                if 'DR' in bal[i][0].split()[-1]:
                    bal[i] = (" ".join(bal[i][0].split()[0:-1]) + ' -' + bal[i][0].split()[-1].replace("DR", ""),month_only)
                # Create a new tuple with the month
                new_bal.append((bal[i][0].split()[-1].replace(',', ""), month_only))
            except Exception as e:
                pass
            try:
                date_format = '%d/%m/%y'
                # Convert the date string to pandas datetime object
                date_object = pd.to_datetime(date_string, format=date_format)

                # Extract the month from the pandas datetime object
                month_only = date_object.month

                if 'DR' in bal[i][0].split()[-1]:
                    bal[i] = (" ".join(bal[i][0].split()[0:-1]) + ' -' + bal[i][0].split()[-1].replace("DR", ""),month_only)

                # Create a new tuple with the month
                new_bal.append((bal[i][0].split()[-1].replace(',', ""), month_only))
            except Exception as e:
                pass
            try:
                date_format = '%d/%m'
                # Convert the date string to pandas datetime object
                date_object = pd.to_datetime(date_string, format=date_format)

                # Extract the month from the pandas datetime object
                month_only = date_object.month

                if 'DR' in bal[i][0].split()[-1]:
                    bal[i] = (" ".join(bal[i][0].split()[0:-1]) + ' -' + bal[i][0].split()[-1].replace("DR", ""),month_only)
                # Create a new tuple with the month
                new_bal.append((bal[i][0].split()[-1].replace(',', ""), month_only))

            except Exception as e:
                print(e)
    bal = new_bal
    paragraph = """
PLEASE BE INFORMED THAT EFFECTIVE 01/04/2018, THE AMOUNT OF
3RD PARTY CHEQUE ENCASHMENT ALLOWED OVER THE COUNTER IS LIMITED
TO RM10,000.00 PER CHEQUE.
.
FOR ENCASHMENT OF CHEQUE BY AUTHORISED PARTIES, THE AMOUNT IS
LIMITED TO RM50,000.00 PER CHEQUE.
.
KIJANG EMAS
KIJANG EMAS, MALAYSIA'S OWN GOLD BULLION COIN IS AVAILABLE FOR
PURCHASE IN VARIOUS DENOMINATION OF 1 OZ, 1/2 OZ AND 1/4 OZ.
VISIT ANY OF OUR NEAREST 31 PARTICIPATING BRANCHES OR VISIT
WWW.MAYBANK.COM.MY FOR MORE INFO.
.
M2U BIZ
MAYBANK2U BIZ IS NOW EVEN MORE COMPACT WITH THE NEW BULK PAYMENT
FEATURE! LOGIN TO MAYBANK2U BIZ TO DISCOVER MORE. NOT A USER
YET? VISIT THE NEAREST MAYBANK BRANCH FOR MORE INFO.
TERMS AND CONDITIONS APPLY.
.
FCN
EXCHANGE YOUR CURRENCY AT COMPETITIVE RATES WITH US. NO HIDDEN
CHARGES! VISIT THE NEAREST MAYBANK MONEY EXCHANGE BOOTH TODAY.
VISIT

LOOKING TO EXCHANGE CURRENCY? BUY AND SELL FOREIGN CURRENCIES AT
COMPETITIVE RATES AT ANY MAYBANK MONEY EXCHANGE BOOTHS. NO HIDDEN
CHARGES WHEN TRANSACTING WITH US! VISIT THE NEAREST MAYBANK MONEY
EXCHANGE BOOTH TODAY!
.
.
SIGN UP FOR MAYBANK AUTOCREDIT AND FIND OUT HOW THE FY17 PAYROLL
ATTACK CAMPAIGN CAN BENEFIT YOUR COMPANY. VISIT ANY OF OUR BRANCHES
OR LOG ON TO WWW.MAYBANK2U.COM FOR MORE INFO. T&C APPLY
.
.
INSTRUCTION OR INSTANT FUND TRANSFER VIA M2U. YOU MAY CONTACT YOUR
MORTGAGE LOAN/FINANCING HOME BRANCH TO SET UP A VARIABLE STANDING
INSTRUCTION TO PAY YOUR LOAN/FINANCING. TERMS AND CONDITIONS APPLY.
.
YOU CAN NOW TRANSFER OR RECEIVE FUNDS UP TO RM30,000 DAILY WITH
INTERBANK GIRO OR INSTANT TRANSFER VIA MAYBANK ATM OR MAYBANK2U.
CALL 1300 88 6688 OR LOG ON TO WWW.MAYBANK.COM.MY FOR MORE DETAILS.
TERMS AND CONDITIONS APPLY.
.
.
MAKE MONTHLY MORTGAGE LOAN/FINANCING REPAYMENTS VIA STANDING
FCN EXCHANGE YOUR CURRENCY AT COMPETITIVE RATES WITH US. NO HIDDEN
CHARGES! VISIT THE NEAREST MAYBANK MONEY EXCHANGE BOOTH TODAY.
VISIT WWW.MAYBANK.COM.MY FOR MORE INFO.
.
1. NEVER REVEAL YOUR TRANSACTION AUTHORISATION CODE(TAC) TO
AMYONE TO KEEP YOUR ACCOUNT SAFE AND SECURE.
2. DOUBLE CHECK BEFORE YOU PROCEED WITH A TRANSACTION. WHEN
SENDING MONEY OR ADDING SOMEONE AS FAVOURITES, PLEASE ENSURE ALL
DETAILS ARE CORRECT SUCH AS NAME AND ACCOUNT NUMBER.
3. NEVER SHARE OR USE THE SAME PASSWORD BETWEEN MAKER AND CHECKER.
IT IS YOUR IDENTITY TO PROVE THAT YOU'RE YOU.
.
4. SPOT ANY UNUSUAL ACTIVITY WITH YOUR M2U BIZ ACCOUNT? DO CONTACT
US IMMEDIATELY AT 03-58914744 AND WE WILL ASSIST YOU.
.
5. MAKE SURE YOUR PASSWORD IS UNIQUE AND DIFFERENT FROM THE
PASSWORD YOU USE FOR SOCIAL MEDIA OR EMAIL. SET A PASSWORD THAT
IS DIFFICULT TO GUESS SO IT HELPS TO PROTECT YOU FROM HACKERS,
IDENTITY THEFT AND OTHER PRIVACY BREACHES.

6. DO NOT CLICK ON ANY ATTACHMENTS OR LINKS FROM KNOWN OR
UNKNOWN SOURCES THAT'S LOOK SUSPICIOUS. ALWAYS ENTER THE URL
WWW.MAYBANK2U.COM.MY DIRECTLY INTO YOUR BROWSER TO LOG IN TO
MAYBANK2U.BIZ.
.
PLEASE BE REMINDED TO CHECK YOUR BANK ACCOUNT BALANCES REGULARLY
VIA MAYBANK2U, MAYBANK2U APP, MAE APP OR MAYBANK2U BIZ AND BE
INFORMED OF YOUR DAILY FINANCIAL ACTIVITIES.
.
CREDIT TO MULTIPLE ACCOUNTS AT ONE GO WITH BULK PAYMENTS FROM A
SINGLE ACCOUNT AND INCREASE YOUR BUSINESS TRANSFER LIMIT FROM
RM50,000 TO RM250,000.IF YOU ARE A M2U BIZ CUSTOMER, THE CHECKER
CAN REGISTER THE BULK PAYMENT FEATURE ON THE M2U BIZ WEB DASHBOARD.
NOT A M2U BIZ USER? VISIT US AT HTTP://WWW.MAYBANK2U.COM.MY/M2UBIZAPP
OR CALL US AT 1300-88-6688.
    .
EFFECTIVE 1 SEPTEMBER 2022, THE BANK WILL NO LONGER ACCEPT HARDCOPY
REQUESTS ON BANK CONFIRMATION LETTERS FROM YOU OR YOUR AUDITOR.
YOUR AUDITOR, ON YOUR BEHALF, CAN SUBMIT THE BANK CONFIRMATION REQUEST
THROUGH THE MIA GOVERNED PLATFORM- ECONFIRM.MY.
NOTE:MAYBANK IS NOT RESPONSIBLE OR LIABLE FOR THE USE OF THE PLATFORM.
    .
KINI, ANDA TIDAK PERLU MENULIS CEK ATAU PERGI KE BANK UNTUK MEMBAYAR
PEMBIAYAAN RUMAH. NIKMATI CARA YANG LEBIH MUDAH DAN SELAMAT MELALUI
ARAHAN TETAP (SI/ESI), PINDAHAN DANA SEGERA (IBGT) ATAU GIRO ANTARA
BANK MELALUI LAMAN WEB MAYBANK2U. TIADA YURAN TRANSAKSI DIKENAKAN.
.
MGIA
DIVERSIFY YOUR PORTFOLIO VIA MAYBANK GOLD INVESTMENT ACCOUNT!
YOU CAN INVEST ANYTIME, ANYWHERE VIA WWW.MAYBANK.COM.MY.
TERMS AND CONDITIONS APPLY.
.
.
ASNB
UNDER THE ADAM50 INITIATIVE, YOUR CHILD IS ELIGIBLE TO RECEIVE
RM200 UNIT TRUST INCENTIVE IN ASB/AS 1MALAYSIA IF HE/SHE IS BORN
BETWEEN 1 JANUARY 2018 TO 31 DECEMBER 2022. AN OPPORTUNITY NOT TO BE
MISSED! VISIT THE NEAREST MAYBANK BRANCH FOR MORE INFO. TERMS AND
CONDITIONS APPLY.
.
ENDING BALANCE :
LEDGER BALANCE :
TOTAL DEBIT :
TOTAL CREDIT :
"""

    # Extract consecutive 3-word phrases from the paragraph
    phrases_to_remove = re.findall(r'\b\w+\s\w+\s\w+\b', paragraph)

    # Remove elements from the list if they match any 3-word phrase from the paragraph
    rows = [item for item in rows if not any(phrase in item for phrase in phrases_to_remove)]
    rows = [item for item in rows if item not in paragraph.split('\n')]
    string_to_remove = 'ENTRY DATE VALUE DATE TRANSACTION DESCRIPTION TRANSACTION AMOUNT STATEMENT BALANCE'
    rows = [item for item in rows if item.strip() != string_to_remove]
    string_to_remove = 'ENTRY DATE VALUE DATE TRANSACTION DESCRIPTION GST TYPE TRANSACTION AMOUNT STATEMENT BALANCE'
    rows = [item for item in rows if item.strip() != string_to_remove]
    string_to_remove = 'ENTRY DATE TRANSACTION DESCRIPTION TRANSACTION AMOUNT STATEMENT BALANCE'
    rows = [item for item in rows if item.strip() != string_to_remove]
    rows = [item for item in rows if 'BEGINNING BALANCE' not in item]

    data = MBB_process_rows(rows, bal)

    df = pd.DataFrame.from_dict(data, orient='index')
    df['Date2'] = pd.to_datetime(df['Date'], errors='coerce', format='%d/%m/%Y')
    df['Date2'].fillna(pd.to_datetime(df['Date'], errors='coerce', format='%d/%m/%y'), inplace=True)
    df_null_date = df[df['Date2'].isnull()]
    df = df.dropna(subset=['Date2'])  # DataFrame with valid dates
    df['Month'] = df['Date2'].dt.month
    df['Idx'] = df.index
    df['Idx'] = pd.to_numeric(df['Idx'], errors='coerce')
    if sort == 1:
        df = df.sort_values(by = ['Date2', 'Idx'], ascending = [True, True])
    elif sort == -1:
        df = df.sort_values(by = ['Date2', 'Idx'], ascending = [True, False])
    
    bal = sorted(bal, key=lambda x: x[1])
    
    df['Amount2'] = df.Amt * df.Sign

    return df, bal, df_null_date

