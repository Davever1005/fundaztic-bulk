# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import render_template, redirect, request, url_for

from apps import db, login_manager
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm
from apps.authentication.models import Users

from apps.authentication.util import verify_pass
import numpy as np
from flask import Flask, request, render_template
import urllib.request
import json
from flask_cors import CORS
from joblib import load
import sklearn
import pandas as pd
import time
from urllib.error import HTTPError, URLError
from io import BytesIO
import csv
from flask import send_file
from flask import session
import os
from flask import jsonify
from flask import Flask, request, render_template
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import FileField
from io import BytesIO
import base64
from flask import Response, stream_with_context
import pickle



@blueprint.route('/')
def route_default():
    return render_template('home/Home.html')

@blueprint.route('/manual_input', methods=['GET', 'POST'])
def manual_input():
    scaler = load(open('files/scaler.joblib', 'rb'))

    # Define feature keys and their default values
    FEATURE_KEYS = ['INSTALLMENT_TENOR_MONTHS', 'APPLIED_AMOUNT', 'APPROVED_AMOUNT',
        'INTEREST_RATE_PA', 'FINAL_PD', 'RnR', 'Financing_Amount_Principal',
        'Financing_Amount_Interest', 'YIB', 'Female_Y', 'Avg_Age_When_apply',
        'Origination_fee', 'Total_investors', 'Avg_investor_investment',
        'Guarantor_invested', 'days_to_disb', 'Day_disbursed', 'Day_hosted',
        'Nature_of_Business_Accommodation & Food Service Activities',
        'Nature_of_Business_Administrative and Support Service Activities',
        'Nature_of_Business_Agriculture, Forestry and Fishing',
        'Nature_of_Business_Arts, Entertainment and Recreation',
        'Nature_of_Business_Construction', 'Nature_of_Business_Education',
        'Nature_of_Business_Financial and Insurance/Takaful Activities',
        'Nature_of_Business_Human Health and Social Work Activities',
        'Nature_of_Business_Information and Communication',
        'Nature_of_Business_Manufacturing',
        'Nature_of_Business_Other Service Activities',
        'Nature_of_Business_Professional, Scientific & Technical Activities',
        'Nature_of_Business_Real-Estate Activities',
        'Nature_of_Business_Transportation & Storage',
        'Nature_of_Business_Water, Sewerage & Waste Mgmt & Related Activities',
        'Nature_of_Business_Wholesale & Retail (incl Motor Vehicle Repairs)',
        'Entity_Partnership', 'Entity_Private Limited',
        'Entity_Sole Proprietor', 'STATE_JOHOR', 'STATE_KEDAH',
        'STATE_KELANTAN', 'STATE_Kedah1', 'STATE_MELAKA',
        'STATE_NEGERI SEMBILAN', 'STATE_PAHANG', 'STATE_PERAK', 'STATE_PERLIS',
        'STATE_PULAU PINANG', 'STATE_Perak1', 'STATE_SABAH', 'STATE_SARAWAK',
        'STATE_SELANGOR', 'STATE_Sarawak1', 'STATE_TERENGGANU',
        'STATE_WILAYAH PERSEKUTUAN', 'LOAN_PURPOSE_Asset acquisition',
        'LOAN_PURPOSE_Contract financing',
        'LOAN_PURPOSE_Debt consolidation / refinancing',
        'LOAN_PURPOSE_Marketing and advertising',
        'LOAN_PURPOSE_Other business purpose',
        'LOAN_PURPOSE_Purchase of equipment',
        'LOAN_PURPOSE_Upgrading / Renovation', 'LOAN_PURPOSE_Working Capital',
        'FIN_GRADE_A1', 'FIN_GRADE_A2', 'FIN_GRADE_B3', 'FIN_GRADE_B4',
        'FIN_GRADE_C5', 'FIN_GRADE_C6', 'FIN_GRADE_D7', 'FIN_GRADE_D8',
        'FIN_GRADE_X1', 'Race_Chinese', 'Race_Indian', 'Race_Malay',
        'Race_Others']
    FEATURE_KEYS2 = ['INSTALLMENT_TENOR_MONTHS', 'APPLIED_AMOUNT', 'APPROVED_AMOUNT',
        'INTEREST_RATE_PA', 'FINAL_PD', 'RnR', 'Financing_Amount_Principal',
        'Financing_Amount_Interest', 'YIB', 'Female_Y', 'Avg_Age_When_apply',
        'Origination_fee', 'Total_investors', 'Avg_investor_investment',
        'Guarantor_invested', 'days_to_disb', 'Day_disbursed', 'Day_hosted',
        'Nature_of_Business_Accommodation & Food Service Activities',
        'Nature_of_Business_Administrative and Support Service Activities',
        'Nature_of_Business_Agriculture, Forestry and Fishing',
        'Nature_of_Business_Arts, Entertainment and Recreation',
        'Nature_of_Business_Construction', 'Nature_of_Business_Education',
        'Nature_of_Business_Financial and Insurance/Takaful Activities',
        'Nature_of_Business_Human Health and Social Work Activities',
        'Nature_of_Business_Information and Communication',
        'Nature_of_Business_Manufacturing',
        'Nature_of_Business_Other Service Activities',
        'Nature_of_Business_Professional, Scientific & Technical Activities',
        'Nature_of_Business_Real-Estate Activities',
        'Nature_of_Business_Transportation & Storage',
        'Nature_of_Business_Water, Sewerage & Waste Mgmt & Related Activities',
        'Nature_of_Business_Wholesale & Retail (incl Motor Vehicle Repairs)',
        'Entity_Partnership', 'Entity_Private Limited',
        'Entity_Sole Proprietor', 'STATE_JOHOR', 'STATE_KEDAH',
        'STATE_KELANTAN', 'STATE_Kedah', 'STATE_MELAKA',
        'STATE_NEGERI SEMBILAN', 'STATE_PAHANG', 'STATE_PERAK', 'STATE_PERLIS',
        'STATE_PULAU PINANG', 'STATE_Perak', 'STATE_SABAH', 'STATE_SARAWAK',
        'STATE_SELANGOR', 'STATE_Sarawak', 'STATE_TERENGGANU',
        'STATE_WILAYAH PERSEKUTUAN', 'LOAN_PURPOSE_Asset acquisition',
        'LOAN_PURPOSE_Contract financing',
        'LOAN_PURPOSE_Debt consolidation / refinancing',
        'LOAN_PURPOSE_Marketing and advertising',
        'LOAN_PURPOSE_Other business purpose',
        'LOAN_PURPOSE_Purchase of equipment',
        'LOAN_PURPOSE_Upgrading / Renovation', 'LOAN_PURPOSE_Working Capital',
        'FIN_GRADE_A1', 'FIN_GRADE_A2', 'FIN_GRADE_B3', 'FIN_GRADE_B4',
        'FIN_GRADE_C5', 'FIN_GRADE_C6', 'FIN_GRADE_D7', 'FIN_GRADE_D8',
        'FIN_GRADE_X1', 'Race_Chinese', 'Race_Indian', 'Race_Malay',
        'Race_Others']
    FEATURE_KEYS=[item.replace(" ", "").upper() for item in FEATURE_KEYS]

    FEATURE_DEFAULTS = {key: 0.0 for key in FEATURE_KEYS}
    if request.method == 'POST':
        # Get form values
        form_values = [value for value in request.form.values()]
        # Prepare features
        features = FEATURE_DEFAULTS.copy()
        features.update(zip(FEATURE_KEYS[:18], map(float, [str(item).replace(",", "") for item in form_values[:18]])))

        # Update features based on selected options
        features[f'NATURE_OF_BUSINESS_{form_values[18].replace(" ", "").upper()}'] = 1.0
        features[f'ENTITY_{form_values[19].replace(" ", "").upper()}'] = 1.0
        features[f'STATE_{form_values[20].replace(" ", "").upper()}'] = 1.0
        features[f'LOAN_PURPOSE_{form_values[21].replace(" ", "").upper()}'] = 1.0
        features[f'FIN_GRADE_{form_values[22].replace(" ", "").upper()}'] = 1.0
        features[f'RACE_{form_values[23].replace(" ", "").upper()}'] = 1.0


        # Extract numerical values
        numerical_values = list(features.values())
        
        # Transform the numerical values
        scaled_values_2d = scaler.transform(np.array(numerical_values).reshape(1, -1))
        # Update the dictionary with the scaled values
        scaled_values = [val for val in scaled_values_2d[0]]
        scaled_dict = dict(zip(FEATURE_KEYS2, scaled_values))


        # Prepare data for API request
        data = {
            "Inputs": {"data": [scaled_dict]},
            "GlobalParameters": 0.0
        }

        # Encode data and make API request
        body = str.encode(json.dumps(data))
        url = 'http://b579b683-51a0-4526-8834-a3b9a8ee91be.eastus.azurecontainer.io/score'
        headers = {'Content-Type': 'application/json'}
        req = urllib.request.Request(url, body, headers)

        try:
            response = urllib.request.urlopen(req, timeout=10)
            result = response.read().decode("utf8", 'ignore')   # Decode the result to a string
            result=float(result[13:-3])
            if result > 1:
                result = 1
            elif result < 0:
                result = 0
            print(f't: {result}')
            result = round(result,4)
        except urllib.error.HTTPError as error:
            result = error.read().decode("utf8", 'ignore')

        # Pass the result and form values to the template
        return render_template('home/All_manual.html', result=result, form_values=form_values)

    # If it's a GET request, just render the template with default values
    return render_template('home/All_manual.html', result=None, form_values=None)

class MyForm(FlaskForm):
    csv_file = FileField('Upload CSV File')

@blueprint.route('/csv_upload', methods=['POST', 'GET'])
def csv_upload():
    form = MyForm()  # Instantiate the form

    if request.method == 'POST' and form.validate_on_submit():
        csv_file = form.csv_file.data  # Access the uploaded file from the form

        global status_data
        status_data = (0,0)

        # Process the CSV file
        df = process_csv(csv_file)

        table_html = df.to_html(classes='table table-striped', index=False)

        return render_template('home/All_csv.html', table=table_html, form=form)

    # If it's a GET request or form is not valid, render the template with the form
    return render_template('home/All_csv.html', table=None, form=form)

@blueprint.route('/process', methods=['POST', 'GET'])
def process():
    if 'csv_file' not in request.files:
        return jsonify({'error': 'No file uploaded'})

    csv_file = request.files['csv_file']

    if csv_file.filename == '':
        return jsonify({'error': 'No file selected'})

    # Process the CSV file
    df = process_csv(csv_file)

    table_html = df.to_html(classes='table table-striped', index=False)

    return jsonify({'table': table_html})

def process_csv(csv_file):
    global status_data
    FEATURE_KEYS = ['INSTALLMENT_TENOR_MONTHS', 'APPLIED_AMOUNT', 'APPROVED_AMOUNT',
        'INTEREST_RATE_PA', 'FINAL_PD', 'RnR', 'Financing_Amount_Principal',
        'Financing_Amount_Interest', 'YIB', 'Female_Y', 'Avg_Age_When_apply',
        'Origination_fee', 'Total_investors', 'Avg_investor_investment',
        'Guarantor_invested', 'days_to_disb', 'Day_disbursed', 'Day_hosted',
        'Nature_of_Business_Accommodation & Food Service Activities',
        'Nature_of_Business_Administrative and Support Service Activities',
        'Nature_of_Business_Agriculture, Forestry and Fishing',
        'Nature_of_Business_Arts, Entertainment and Recreation',
        'Nature_of_Business_Construction', 'Nature_of_Business_Education',
        'Nature_of_Business_Financial and Insurance/Takaful Activities',
        'Nature_of_Business_Human Health and Social Work Activities',
        'Nature_of_Business_Information and Communication',
        'Nature_of_Business_Manufacturing',
        'Nature_of_Business_Other Service Activities',
        'Nature_of_Business_Professional, Scientific & Technical Activities',
        'Nature_of_Business_Real-Estate Activities',
        'Nature_of_Business_Transportation & Storage',
        'Nature_of_Business_Water, Sewerage & Waste Mgmt & Related Activities',
        'Nature_of_Business_Wholesale & Retail (incl Motor Vehicle Repairs)',
        'Entity_Partnership', 'Entity_Private Limited',
        'Entity_Sole Proprietor', 'STATE_JOHOR', 'STATE_KEDAH',
        'STATE_KELANTAN', 'STATE_Kedah1', 'STATE_MELAKA',
        'STATE_NEGERI SEMBILAN', 'STATE_PAHANG', 'STATE_PERAK', 'STATE_PERLIS',
        'STATE_PULAU PINANG', 'STATE_Perak1', 'STATE_SABAH', 'STATE_SARAWAK',
        'STATE_SELANGOR', 'STATE_Sarawak1', 'STATE_TERENGGANU',
        'STATE_WILAYAH PERSEKUTUAN', 'LOAN_PURPOSE_Asset acquisition',
        'LOAN_PURPOSE_Contract financing',
        'LOAN_PURPOSE_Debt consolidation / refinancing',
        'LOAN_PURPOSE_Marketing and advertising',
        'LOAN_PURPOSE_Other business purpose',
        'LOAN_PURPOSE_Purchase of equipment',
        'LOAN_PURPOSE_Upgrading / Renovation', 'LOAN_PURPOSE_Working Capital',
        'FIN_GRADE_A1', 'FIN_GRADE_A2', 'FIN_GRADE_B3', 'FIN_GRADE_B4',
        'FIN_GRADE_C5', 'FIN_GRADE_C6', 'FIN_GRADE_D7', 'FIN_GRADE_D8',
        'FIN_GRADE_X1', 'Race_Chinese', 'Race_Indian', 'Race_Malay',
        'Race_Others']
    FEATURE_KEYS2 = ['INSTALLMENT_TENOR_MONTHS', 'APPLIED_AMOUNT', 'APPROVED_AMOUNT',
        'INTEREST_RATE_PA', 'FINAL_PD', 'RnR', 'Financing_Amount_Principal',
        'Financing_Amount_Interest', 'YIB', 'Female_Y', 'Avg_Age_When_apply',
        'Origination_fee', 'Total_investors', 'Avg_investor_investment',
        'Guarantor_invested', 'days_to_disb', 'Day_disbursed', 'Day_hosted',
        'Nature_of_Business_Accommodation & Food Service Activities',
        'Nature_of_Business_Administrative and Support Service Activities',
        'Nature_of_Business_Agriculture, Forestry and Fishing',
        'Nature_of_Business_Arts, Entertainment and Recreation',
        'Nature_of_Business_Construction', 'Nature_of_Business_Education',
        'Nature_of_Business_Financial and Insurance/Takaful Activities',
        'Nature_of_Business_Human Health and Social Work Activities',
        'Nature_of_Business_Information and Communication',
        'Nature_of_Business_Manufacturing',
        'Nature_of_Business_Other Service Activities',
        'Nature_of_Business_Professional, Scientific & Technical Activities',
        'Nature_of_Business_Real-Estate Activities',
        'Nature_of_Business_Transportation & Storage',
        'Nature_of_Business_Water, Sewerage & Waste Mgmt & Related Activities',
        'Nature_of_Business_Wholesale & Retail (incl Motor Vehicle Repairs)',
        'Entity_Partnership', 'Entity_Private Limited',
        'Entity_Sole Proprietor', 'STATE_JOHOR', 'STATE_KEDAH',
        'STATE_KELANTAN', 'STATE_Kedah', 'STATE_MELAKA',
        'STATE_NEGERI SEMBILAN', 'STATE_PAHANG', 'STATE_PERAK', 'STATE_PERLIS',
        'STATE_PULAU PINANG', 'STATE_Perak', 'STATE_SABAH', 'STATE_SARAWAK',
        'STATE_SELANGOR', 'STATE_Sarawak', 'STATE_TERENGGANU',
        'STATE_WILAYAH PERSEKUTUAN', 'LOAN_PURPOSE_Asset acquisition',
        'LOAN_PURPOSE_Contract financing',
        'LOAN_PURPOSE_Debt consolidation / refinancing',
        'LOAN_PURPOSE_Marketing and advertising',
        'LOAN_PURPOSE_Other business purpose',
        'LOAN_PURPOSE_Purchase of equipment',
        'LOAN_PURPOSE_Upgrading / Renovation', 'LOAN_PURPOSE_Working Capital',
        'FIN_GRADE_A1', 'FIN_GRADE_A2', 'FIN_GRADE_B3', 'FIN_GRADE_B4',
        'FIN_GRADE_C5', 'FIN_GRADE_C6', 'FIN_GRADE_D7', 'FIN_GRADE_D8',
        'FIN_GRADE_X1', 'Race_Chinese', 'Race_Indian', 'Race_Malay',
        'Race_Others']
    FEATURE_KEYS=[item.replace(" ", "").upper() for item in FEATURE_KEYS]
    
    scaler = load(open('files/scaler.joblib', 'rb'))

    # Read CSV file into a Pandas DataFrame
    df = pd.read_csv(csv_file)

    # Initialize an empty DataFrame for the processed data
    processed_data = pd.DataFrame()


    for index, row in df.iterrows():
        try:
            nan_present = any(pd.isna(element) or element == 'NaN' for element in row)
            if None in row or nan_present:
                result = "Incomplete data"
            else:
                result = 'Attempt Failed. Try again.'
                FEATURE_DEFAULTS = {key: 0.0 for key in FEATURE_KEYS}
                features = FEATURE_DEFAULTS.copy()
                features.update(zip(FEATURE_KEYS[:18], map(float, [str(item).replace(",", "") for item in row[:18]])))

                # Update features based on selected options
                if f'NATURE_OF_BUSINESS_{row[18].replace(" ", "").upper()}' in FEATURE_KEYS:
                    features[f'NATURE_OF_BUSINESS_{row[18].replace(" ", "").upper()}'] = 1.0
                else:
                    result = f'Invalid data: {row[18]}'
                if f'ENTITY_{row[19].replace(" ", "").upper()}' in FEATURE_KEYS:
                    features[f'ENTITY_{row[19].replace(" ", "").upper()}'] = 1.0
                else:
                    result = f'Invalid data: {row[19]}'
                if f'STATE_{row[20].replace(" ", "").upper()}' in FEATURE_KEYS:
                    features[f'STATE_{row[20].replace(" ", "").upper()}'] = 1.0
                else:
                    result = f'Invalid data: {row[20]}'
                if f'LOAN_PURPOSE_{row[21].replace(" ", "").upper()}' in FEATURE_KEYS:
                    features[f'LOAN_PURPOSE_{row[21].replace(" ", "").upper()}'] = 1.0
                else:
                    result = f'Invalid data: {row[21]}'
                if f'FIN_GRADE_{row[22].replace(" ", "").upper()}' in FEATURE_KEYS:
                    features[f'FIN_GRADE_{row[22].replace(" ", "").upper()}'] = 1.0
                else:
                    result = f'Invalid data: {row[8]}'
                if f'RACE_{row[23].replace(" ", "").upper()}' in FEATURE_KEYS:
                    features[f'RACE_{row[23].replace(" ", "").upper()}'] = 1.0
                else:
                    result = f'Invalid data: {row[23]}'
                if 'Invalid' not in result:

                    # Extract numerical values
                    numerical_values = list(features.values())

                    # Transform the numerical values
                    scaled_values_2d = scaler.transform(np.array(numerical_values).reshape(1, -1))
                    scaled_values = scaled_values_2d[0]

                    # Update the dictionary with the scaled values
                    scaled_dict = dict(zip(FEATURE_KEYS2, scaled_values))

                    # Prepare data for API request
                    data = {
                        "Inputs": {"data": [scaled_dict]},
                        "GlobalParameters": 0.0
                    }

                    # Encode data and make API request
                    body = str.encode(json.dumps(data))
                    url = 'http://b579b683-51a0-4526-8834-a3b9a8ee91be.eastus.azurecontainer.io/score'
                    headers = {'Content-Type': 'application/json'}
                    req = urllib.request.Request(url, body, headers)

                    max_retries = 5
                    retry_delay = 1  # seconds

                    for attempt in range(1, max_retries + 1):
                        try:
                            response = urllib.request.urlopen(req, timeout=10)
                            result = response.read().decode("utf8", 'ignore')  # Decode the result to a string
                            result = float(result[13:-3])
                            if result > 1:
                                result = 1
                            elif result < 0:
                                result = 0
                            print(f't: {result}')
                            result = round(result, 4)
                            time.sleep(1)
                            break  # Break out of the loop if successful
                        except (HTTPError, URLError) as error:
                            print(f"Attempt {attempt} failed. Retrying in {retry_delay} seconds...")
                            time.sleep(retry_delay)

            # Add the result to the row
            row['Result'] = result

            # Append the processed row to the DataFrame
            processed_data = processed_data.append(row, ignore_index=True)
            session['processed_data'] = processed_data.to_csv(index=False)
        except Exception as error:
            print(f"An error occurred: {error}")
            # Set result to 'error' in case of any exception
            row['Result'] = error
            # Append the row to the DataFrame with the error result
            processed_data = processed_data.append(row, ignore_index=True)
            session['processed_data'] = processed_data.to_csv(index=False)     
    # Return the HTML table
    return processed_data

@blueprint.route('/download_template')
def download_template():
    # Create a string with CSV template content
    template_content = '''INSTALLMENT_TENOR_MONTHS,APPLIED_AMOUNT,APPROVED_AMOUNT,INTEREST_RATE_PA,FINAL_PD,RnR(1forY/0forN),Financing_Amount_Principal,Financing_Amount_Interest,YIB,Female_Y(1forY/0forN),Avg_Age_When_apply,Origination_fee,Total_investors,Avg_investor_investment,Guarantor_invested(1forY/0forN),days_to_disb,Day_disbursed,Day_hosted,Nature_of_Business,Entity,STATE,LOAN_PURPOSE,FIN_GRADE,Race'''

    # Send the file for download
    return send_file(
        BytesIO(template_content.encode()),
        as_attachment=True,
        download_name='csv_template(all).csv',
        mimetype='text/csv'
    )

@blueprint.route('/download_processed_csv')
def download_processed_csv():
    # Retrieve the processed CSV data from the session
    processed_csv = session.get('processed_data')
    print(processed_csv)
    if processed_csv:

        # Send the file for download
        return send_file(
            BytesIO(processed_csv.encode()),
            as_attachment=True,
            download_name='result.csv',
            mimetype='text/csv'
        )
    else:
        return jsonify({'error': 'Processed data not found in session'})

@blueprint.route('/pre_manual_input', methods=['GET', 'POST'])
def pre_manual_input():
    scaler = load(open('files/prescaler.joblib', 'rb'))

    # Define feature keys and their default values
    FEATURE_KEYS = ['APPLIED_AMOUNT', 'YIB', 'Female_Y', 'Avg_Age_When_apply',
       'Nature_of_Business_Accommodation & Food Service Activities',
       'Nature_of_Business_Administrative and Support Service Activities',
       'Nature_of_Business_Agriculture, Forestry and Fishing',
       'Nature_of_Business_Arts, Entertainment and Recreation',
       'Nature_of_Business_Construction', 'Nature_of_Business_Education',
       'Nature_of_Business_Financial and Insurance/Takaful Activities',
       'Nature_of_Business_Human Health and Social Work Activities',
       'Nature_of_Business_Information and Communication',
       'Nature_of_Business_Manufacturing',
       'Nature_of_Business_Other Service Activities',
       'Nature_of_Business_Professional, Scientific & Technical Activities',
       'Nature_of_Business_Real-Estate Activities',
       'Nature_of_Business_Transportation & Storage',
       'Nature_of_Business_Water, Sewerage & Waste Mgmt & Related Activities',
       'Nature_of_Business_Wholesale & Retail (incl Motor Vehicle Repairs)',
       'Entity_Partnership', 'Entity_Private Limited',
       'Entity_Sole Proprietor', 'STATE_JOHOR', 'STATE_KEDAH',
       'STATE_KELANTAN', 'STATE_MELAKA', 'STATE_NEGERI SEMBILAN',
       'STATE_PAHANG', 'STATE_PERAK', 'STATE_PERLIS', 'STATE_PULAU PINANG',
       'STATE_SABAH', 'STATE_SARAWAK', 'STATE_SELANGOR', 'STATE_TERENGGANU',
       'STATE_WILAYAH PERSEKUTUAN', 'LOAN_PURPOSE_Asset acquisition',
       'LOAN_PURPOSE_Contract financing',
       'LOAN_PURPOSE_Debt consolidation / refinancing',
       'LOAN_PURPOSE_Invoice financing',
       'LOAN_PURPOSE_Marketing and advertising',
       'LOAN_PURPOSE_Other business purpose',
       'LOAN_PURPOSE_Purchase of equipment',
       'LOAN_PURPOSE_Upgrading / Renovation', 'LOAN_PURPOSE_Working Capital',
       'Race_Chinese', 'Race_Indian', 'Race_Malay', 'Race_Others']

    FEATURE_DEFAULTS = {key: 0.0 for key in FEATURE_KEYS}
    if request.method == 'POST':
        # Get form values
        form_values = [value for value in request.form.values()]
        # Prepare features
        features = FEATURE_DEFAULTS.copy()
        features.update(zip(FEATURE_KEYS[:4], map(float, [str(item).replace(",", "") for item in form_values[:4]])))

        # Update features based on selected options
        features[f'Nature_of_Business_{form_values[4]}'] = 1.0
        features[f'Entity_{form_values[5]}'] = 1.0
        features[f'STATE_{form_values[6]}'] = 1.0
        features[f'LOAN_PURPOSE_{form_values[7]}'] = 1.0
        features[f'Race_{form_values[8]}'] = 1.0

        # Extract numerical values
        numerical_values = list(features.values())
        
        # Transform the numerical values
        scaled_values_2d = scaler.transform(np.array(numerical_values).reshape(1, -1))
        # Update the dictionary with the scaled values
        scaled_values = [val for val in scaled_values_2d[0]]
        scaled_dict = dict(zip(features.keys(), scaled_values))


        # Prepare data for API request
        data = {
            "Inputs": {"data": [scaled_dict]},
            "GlobalParameters": 0.0
        }

        # Encode data and make API request
        body = str.encode(json.dumps(data))
        url = 'http://a83ce717-57dd-4207-a549-09b71aab95a0.eastus.azurecontainer.io/score'
        headers = {'Content-Type': 'application/json'}
        req = urllib.request.Request(url, body, headers)

        try:
            response = urllib.request.urlopen(req, timeout=10)
            result = response.read().decode("utf8", 'ignore')   # Decode the result to a string
            result=float(result[13:-3])
            if result > 1:
                result = 1
            elif result < 0:
                result = 0
            print(f't: {result}')
            result = round(result,4)
        except urllib.error.HTTPError as error:
            result = error.read().decode("utf8", 'ignore')

        # Pass the result and form values to the template
        return render_template('home/pre_manual.html', result=result, form_values=form_values)

    # If it's a GET request, just render the template with default values
    return render_template('home/pre_manual.html', result=None, form_values=None)

@blueprint.route('/pre_csv_upload', methods=['POST', 'GET'])
def pre_csv_upload():
    form = MyForm()  # Instantiate the form

    if request.method == 'POST' and form.validate_on_submit():
        csv_file = form.csv_file.data  # Access the uploaded file from the form

        global status_data
        status_data = (0,0)

        # Process the CSV file
        df = pre_process_csv(csv_file)

        table_html = df.to_html(classes='table table-striped', index=False)

        return render_template('home/pre_csv.html', table=table_html, form=form)

    # If it's a GET request or form is not valid, render the template with the form
    return render_template('home/pre_csv.html', table=None, form=form)

@blueprint.route('/pre_process', methods=['POST', 'GET'])
def pre_process():
    if 'csv_file' not in request.files:
        return jsonify({'error': 'No file uploaded'})

    csv_file = request.files['csv_file']

    if csv_file.filename == '':
        return jsonify({'error': 'No file selected'})

    # Process the CSV file
    df = pre_process_csv(csv_file)

    table_html = df.to_html(classes='table table-striped', index=False)

    return jsonify({'table': table_html})

def pre_process_csv(csv_file):
    global status_data
    FEATURE_KEYS = ['APPLIED_AMOUNT', 'YIB', 'Female_Y', 'Avg_Age_When_apply',
       'Nature_of_Business_Accommodation & Food Service Activities',
       'Nature_of_Business_Administrative and Support Service Activities',
       'Nature_of_Business_Agriculture, Forestry and Fishing',
       'Nature_of_Business_Arts, Entertainment and Recreation',
       'Nature_of_Business_Construction', 'Nature_of_Business_Education',
       'Nature_of_Business_Financial and Insurance/Takaful Activities',
       'Nature_of_Business_Human Health and Social Work Activities',
       'Nature_of_Business_Information and Communication',
       'Nature_of_Business_Manufacturing',
       'Nature_of_Business_Other Service Activities',
       'Nature_of_Business_Professional, Scientific & Technical Activities',
       'Nature_of_Business_Real-Estate Activities',
       'Nature_of_Business_Transportation & Storage',
       'Nature_of_Business_Water, Sewerage & Waste Mgmt & Related Activities',
       'Nature_of_Business_Wholesale & Retail (incl Motor Vehicle Repairs)',
       'Entity_Partnership', 'Entity_Private Limited',
       'Entity_Sole Proprietor', 'STATE_JOHOR', 'STATE_KEDAH',
       'STATE_KELANTAN', 'STATE_MELAKA', 'STATE_NEGERI SEMBILAN',
       'STATE_PAHANG', 'STATE_PERAK', 'STATE_PERLIS', 'STATE_PULAU PINANG',
       'STATE_SABAH', 'STATE_SARAWAK', 'STATE_SELANGOR', 'STATE_TERENGGANU',
       'STATE_WILAYAH PERSEKUTUAN', 'LOAN_PURPOSE_Asset acquisition',
       'LOAN_PURPOSE_Contract financing',
       'LOAN_PURPOSE_Debt consolidation / refinancing',
       'LOAN_PURPOSE_Invoice financing',
       'LOAN_PURPOSE_Marketing and advertising',
       'LOAN_PURPOSE_Other business purpose',
       'LOAN_PURPOSE_Purchase of equipment',
       'LOAN_PURPOSE_Upgrading / Renovation', 'LOAN_PURPOSE_Working Capital',
       'Race_Chinese', 'Race_Indian', 'Race_Malay', 'Race_Others']
    MODIFIED_FEATURE_KEYS=[item.replace(" ", "").upper() for item in FEATURE_KEYS]

    scaler = load(open('files/prescaler.joblib', 'rb'))

    # Read CSV file into a Pandas DataFrame
    df = pd.read_csv(csv_file)

    # Initialize an empty DataFrame for the processed data
    processed_data = pd.DataFrame()

    for index, row in df.iterrows():
        try:
            nan_present = any(pd.isna(element) or element == 'NaN' for element in row)
            if None in row or nan_present:
                result = "Incomplete data"
            else:
                result = 'Attempt Failed. Try again.'
                FEATURE_DEFAULTS = {key: 0.0 for key in MODIFIED_FEATURE_KEYS}
                features = FEATURE_DEFAULTS.copy()
                features.update(zip(MODIFIED_FEATURE_KEYS[:4], map(float, [str(item).replace(",", "") for item in row[:4]])))

                # Update features based on selected options
                if f'NATURE_OF_BUSINESS_{row[4].replace(" ", "").upper()}' in MODIFIED_FEATURE_KEYS:
                    features[f'NATURE_OF_BUSINESS_{row[4].replace(" ", "").upper()}'] = 1.0
                else:
                    result = f'Invalid data: {row[4]}'
                if f'ENTITY_{row[5].replace(" ", "").upper()}' in MODIFIED_FEATURE_KEYS:
                    features[f'ENTITY_{row[5].replace(" ", "").upper()}'] = 1.0
                else:
                    result = f'Invalid data: {row[5]}'
                if f'STATE_{row[6].replace(" ", "").upper()}' in MODIFIED_FEATURE_KEYS:
                    features[f'STATE_{row[6].replace(" ", "").upper()}'] = 1.0
                else:
                    result = f'Invalid data: {row[6]}'
                if f'LOAN_PURPOSE_{row[7].replace(" ", "").upper()}' in MODIFIED_FEATURE_KEYS:
                    features[f'LOAN_PURPOSE_{row[7].replace(" ", "").upper()}'] = 1.0
                else:
                    result = f'Invalid data: {row[7]}'
                if f'RACE_{row[8].replace(" ", "").upper()}' in MODIFIED_FEATURE_KEYS:
                    features[f'RACE_{row[8].replace(" ", "").upper()}'] = 1.0
                else:
                    result = f'Invalid data: {row[8]}'
                if 'Invalid' not in result:
                    # Extract numerical values
                    numerical_values = list(features.values())

                    # Transform the numerical values
                    scaled_values_2d = scaler.transform(np.array(numerical_values).reshape(1, -1))
                    scaled_values = scaled_values_2d[0]

                    # Update the dictionary with the scaled values
                    scaled_dict = dict(zip(FEATURE_KEYS, scaled_values))

                    # Prepare data for API request
                    data = {
                        "Inputs": {"data": [scaled_dict]},
                        "GlobalParameters": 0.0
                    }

                    # Encode data and make API request
                    body = str.encode(json.dumps(data))
                    url = 'http://a83ce717-57dd-4207-a549-09b71aab95a0.eastus.azurecontainer.io/score'
                    headers = {'Content-Type': 'application/json'}
                    req = urllib.request.Request(url, body, headers)

                    max_retries = 5
                    retry_delay = 1  # seconds

                    for attempt in range(1, max_retries + 1):
                        try:
                            response = urllib.request.urlopen(req, timeout=10)
                            result = response.read().decode("utf8", 'ignore')  # Decode the result to a string
                            result = float(result[13:-3])
                            if result > 1:
                                result = 1
                            elif result < 0:
                                result = 0
                            print(f't: {result}')
                            result = round(result, 4)
                            time.sleep(1)
                            break  # Break out of the loop if successful
                        except (HTTPError, URLError) as error:
                            print(f"Attempt {attempt} failed. Retrying in {retry_delay} seconds...")
                            time.sleep(retry_delay)

                # Add the result to the row
                row['Result'] = result

                # Append the processed row to the DataFrame
                processed_data = processed_data.append(row, ignore_index=True)
                session['processed_data'] = processed_data.to_csv(index=False)
        except Exception as error:
            print(f"An error occurred: {error}")
            # Set result to 'error' in case of any exception
            row['Result'] = error
            # Append the row to the DataFrame with the error result
            processed_data = processed_data.append(row, ignore_index=True)
            session['processed_data'] = processed_data.to_csv(index=False)     
    # Return the HTML table
    return processed_data

@blueprint.route('/download_pretemplate')
def download_pretemplate():
    # Create a string with CSV template content
    template_content = '''APPLIED_AMOUNT,YIB,Female_Y(1ForY/0ForN),Avg_Age_When_apply,Nature_of_Business,Entity,STATE,LOAN_PURPOSE,Race'''

    # Send the file for download
    return send_file(
        BytesIO(template_content.encode()),
        as_attachment=True,
        download_name='csv_template(pre).csv',
        mimetype='text/csv'
    )

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('home/page-404.html'), 404


# @blueprint.errorhandler(500)
# def internal_error(error):
#     return render_template('home/page-500.html'), 500
