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
from flask import jsonify
from flask import Flask, request, render_template
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import FileField
from io import BytesIO
import base64
from flask import Response, stream_with_context
import pickle
import pdfplumber
import pandas as pd
from python.MBB import MBB_main
from python.CIMB import CIMB_main
from python.HLBB import HLBB_main
from python.PBB import PBB_main
from python.RHB import RHB_main
from python.RHB_reflex import RHB_reflex_main
from python.OCBC import OCBC_main
from python.AM import AM_main
from python.Islam import ISLAM_main
from python.UOB import UOB_main
from python.summary import summary_main
from python.chart import plot_to_html_image
from python.check import check_balance_within_month
from python.ALLIANCE import ALL_main
from python.type import type
from python.repetition import find_repeat
from python.font_check import text_extraction, process_fonts, extract_fonts, draw_rectangles
from python.cid import cidToChar
import re
import os
from fuzzywuzzy import fuzz
from collections import defaultdict
import calendar
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar
from pypdf import PdfReader, PdfWriter
from pypdf.annotations import Highlight
from pypdf.generic import ArrayObject, FloatObject
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from python.metadata import metadata
from datetime import datetime, timedelta

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
    
    session['continue'] = 'True'

    # Process the CSV file
    df = process_csv(csv_file)

    table_html = df.to_html(classes='table table-striped', index=False)

    return jsonify({'table': table_html})

@blueprint.route('/clear_session', methods=['GET'])
def clear_session():
    session.pop('continue', None)
    return jsonify(success=True)

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

    i = 0
    for index, row in df.iterrows():
        try:
            if session['continue'] is None:
                break
            nan_present = any(pd.isna(element) or element == 'NaN' for element in row)
            if None in row or nan_present:
                result = "Incomplete data"
            else:
                result = 'Attempt Failed. Try again.'
                print(f'{i+1}/{len(df)}')
                i = i + 1
                FEATURE_DEFAULTS = {key: 0.0 for key in FEATURE_KEYS}
                features = FEATURE_DEFAULTS.copy()
                features.update(zip(FEATURE_KEYS[0:18], map(float, [str(item).replace(",", "") for item in row[1:19]])))

                # Update features based on selected options
                if f'NATURE_OF_BUSINESS_{row[19].replace(" ", "").upper()}' in FEATURE_KEYS:
                    features[f'NATURE_OF_BUSINESS_{row[19].replace(" ", "").upper()}'] = 1.0
                else:
                    result = f'Invalid data: {row[19]}'
                if f'ENTITY_{row[20].replace(" ", "").upper()}' in FEATURE_KEYS:
                    features[f'ENTITY_{row[20].replace(" ", "").upper()}'] = 1.0
                else:
                    result = f'Invalid data: {row[20]}'
                if f'STATE_{row[21].replace(" ", "").upper()}' in FEATURE_KEYS:
                    features[f'STATE_{row[21].replace(" ", "").upper()}'] = 1.0
                else:
                    result = f'Invalid data: {row[21]}'
                if f'LOAN_PURPOSE_{row[22].replace(" ", "").upper()}' in FEATURE_KEYS:
                    features[f'LOAN_PURPOSE_{row[22].replace(" ", "").upper()}'] = 1.0
                else:
                    result = f'Invalid data: {row[22]}'
                if f'FIN_GRADE_{row[23].replace(" ", "").upper()}' in FEATURE_KEYS:
                    features[f'FIN_GRADE_{row[23].replace(" ", "").upper()}'] = 1.0
                else:
                    result = f'Invalid data: {row[23]}'
                if f'RACE_{row[24].replace(" ", "").upper()}' in FEATURE_KEYS:
                    features[f'RACE_{row[24].replace(" ", "").upper()}'] = 1.0
                else:
                    result = f'Invalid data: {row[24]}'
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
            processed_path = os.path.join(os.getenv('TMP', '/tmp'), "result.csv")
            processed_data.to_csv(processed_path, index=False)
        except Exception as error:
            print(f"An error occurred: {error}")
            # Set result to 'error' in case of any exception
            row['Result'] = error
            # Append the row to the DataFrame with the error result
            processed_data = processed_data.append(row, ignore_index=True)
            processed_path = os.path.join(os.getenv('TMP', '/tmp'), "result.csv")
            processed_data.to_csv(processed_path, index=False)   
    # Return the HTML table
    return processed_data

@blueprint.route('/download_template')
def download_template():
    # Create a string with CSV template content
    template_content = '''APPLICATION_ID, INSTALLMENT_TENOR_MONTHS,APPLIED_AMOUNT,APPROVED_AMOUNT,INTEREST_RATE_PA,FINAL_PD,RnR(1forY/0forN),Financing_Amount_Principal,Financing_Amount_Interest,YIB,Female_Y(1forY/0forN),Avg_Age_When_apply,Origination_fee,Total_investors,Avg_investor_investment,Guarantor_invested(1forY/0forN),days_to_disb,Day_disbursed,Day_hosted,Nature_of_Business,Entity,STATE,LOAN_PURPOSE,FIN_GRADE,Race'''

    # Send the file for download
    return send_file(
        BytesIO(template_content.encode()),
        as_attachment=True,
        download_name='csv_template(post).csv',
        mimetype='text/csv'
    )

@blueprint.route('/download_processed_csv')
def download_processed_csv():
    processed_path = os.path.join(os.getenv('TMP', '/tmp'), "result.csv")
    if os.path.exists(processed_path):
        return send_file(processed_path, as_attachment=True)
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
                features.update(zip(MODIFIED_FEATURE_KEYS[:4], map(float, [str(item).replace(",", "") for item in row[1:5]])))

                # Update features based on selected options
                if f'NATURE_OF_BUSINESS_{row[5].replace(" ", "").upper()}' in MODIFIED_FEATURE_KEYS:
                    features[f'NATURE_OF_BUSINESS_{row[5].replace(" ", "").upper()}'] = 1.0
                else:
                    result = f'Invalid data: {row[5]}'
                if f'ENTITY_{row[6].replace(" ", "").upper()}' in MODIFIED_FEATURE_KEYS:
                    features[f'ENTITY_{row[6].replace(" ", "").upper()}'] = 1.0
                else:
                    result = f'Invalid data: {row[6]}'
                if f'STATE_{row[7].replace(" ", "").upper()}' in MODIFIED_FEATURE_KEYS:
                    features[f'STATE_{row[7].replace(" ", "").upper()}'] = 1.0
                else:
                    result = f'Invalid data: {row[7]}'
                if f'LOAN_PURPOSE_{row[8].replace(" ", "").upper()}' in MODIFIED_FEATURE_KEYS:
                    features[f'LOAN_PURPOSE_{row[8].replace(" ", "").upper()}'] = 1.0
                else:
                    result = f'Invalid data: {row[8]}'
                if f'RACE_{row[9].replace(" ", "").upper()}' in MODIFIED_FEATURE_KEYS:
                    features[f'RACE_{row[9].replace(" ", "").upper()}'] = 1.0
                else:
                    result = f'Invalid data: {row[9]}'
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
            processed_path = os.path.join(os.getenv('TMP', '/tmp'), "result.csv")
            processed_data.to_csv(processed_path, index=False)   
        except Exception as error:
            print(f"An error occurred: {error}")
            # Set result to 'error' in case of any exception
            row['Result'] = error
            # Append the row to the DataFrame with the error result
            processed_data = processed_data.append(row, ignore_index=True)
            processed_path = os.path.join(os.getenv('TMP', '/tmp'), "result.csv")
            processed_data.to_csv(processed_path, index=False)     
    # Return the HTML table
    return processed_data

@blueprint.route('/download_pretemplate')
def download_pretemplate():
    # Create a string with CSV template content
    template_content = '''APPLICATION_ID,APPLIED_AMOUNT,YIB,Female_Y(1ForY/0ForN),Avg_Age_When_apply,Nature_of_Business,Entity,STATE,LOAN_PURPOSE,Race'''

    # Send the file for download
    return send_file(
        BytesIO(template_content.encode()),
        as_attachment=True,
        download_name='csv_template(pre).csv',
        mimetype='text/csv'
    )

### OCR
@blueprint.route('/OCR', methods=['GET', 'POST'])
def upload_file():
    file_path = None
    bank_selected = None  # Initialize the variable


    if request.method == 'POST':
        file = request.files['file']
        bank_selected = request.form.get('bank')  # Get the selected bank value
        sort = request.form.get('sort')
        fz = float(request.form.get('FZ'))

        if sort == "":
            sort = 1

        if file and bank_selected and sort and fz > 0:
            # Save the uploaded PDF file to the local storage directory
            file_path = os.path.join(os.getenv('TMP', '/tmp'), file.filename)
            print(file_path)
            # file_path = f'static/{file.filename}'
            file.save(file_path)

            # Store the file path in the session for access in the analysis route
            session['file_path'] = file_path
            session['bank_selected'] = bank_selected
            session['sort'] = sort
            session['FZ'] = fz


            return redirect(url_for('authentication_blueprint.analysis'))

    return render_template('home/index.html', bank_selected=bank_selected)

@blueprint.route('/analysis', methods=['GET'])
def analysis():
    try:
        current_page = 1
        page_num = 0
        text = ""
        file_path = session.get('file_path')
        bank_selected = session.get('bank_selected')
        sort = session.get('sort')
        fz = session.get('FZ')
        temp = 1
        if file_path and bank_selected:
            if bank_selected == 'HLBB':
                pdf = pdfplumber.open(file_path)

                df_list = []  # Use a list to store DataFrames

                for i in range(len(pdf.pages)):
                    page = pdf.pages[i]
                    table = page.extract_table(table_settings={"horizontal_strategy": "text"})

                    if table:
                        table_df = pd.DataFrame(table[2:])
                        if len(table_df.columns) == 5:
                            df_list.append(table_df)
                df, bal, df_null_date = HLBB_main(df_list, sort=1)
            elif bank_selected == 'UOB':
                bal = []
                pdf = pdfplumber.open(file_path)
                df_list = []
                for i in range(len(pdf.pages)):
                    page = pdf.pages[i]
                    if temp == 1:
                        table = page.extract_table(table_settings={"horizontal_strategy": "lines", "vertical_strategy": "explicit", "explicit_vertical_lines": [20,100,183,310,400,490,570]})
                    else:
                        table = page.extract_table(table_settings={"horizontal_strategy": "text", "vertical_strategy": "explicit", "explicit_vertical_lines": [40,85,140,196,300,360,440, 530]})
                    if table:
                        table_df = pd.DataFrame(table[2:])
                        df_list.append(table_df)
                df = UOB_main(df_list, 1, temp)
                df_null_date = pd.DataFrame(columns=['DATE', 'DESCRIPTION', 'AMOUNT', 'BALANCE', 'Date2'])
            elif bank_selected == 'ALLIANCE':
                bal = []
                pdf = pdfplumber.open(file_path)
                df_list = []
                for i in range(len(pdf.pages)):
                    page = pdf.pages[i]
                    table = page.extract_table(table_settings={"horizontal_strategy": "text", "vertical_strategy": "lines"})
                    if table:
                        table_df = pd.DataFrame(table[2:])
                        df_list.append(table_df)
                df,bal = ALL_main(df_list, 1)
                df_null_date = pd.DataFrame(columns=['DATE', 'DESCRIPTION', 'AMOUNT', 'BALANCE', 'Date2'])
            else:
                with pdfplumber.open(file_path) as pdf:
                    bal = []
                    text = ""
                    for page in pdf.pages:
                        page_num += 1
                        text = f'{text} \n{page.extract_text()}'

                rows = text.split('\n')

                updated_rows = []
                for x in rows:
                    if x != '' and x != '(cid:3)':         # merely to compact the output
                        abc = re.findall(r'\(cid\:\d+\)',x)
                        if len(abc) > 0:
                            for cid in abc: 
                                x=x.replace(cid, cidToChar(cid))
                        updated_rows.append(x)
                rows = updated_rows
                if bank_selected == "MBB":
                    bal = [(s, rows[i+1]) for i, s in enumerate(rows) if any(keyword.lower() in s.lower() for keyword in  ['BEGINNING BALANCE'])]
                    df, bal, df_null_date = MBB_main(rows,bal, 1)
                
                elif bank_selected == "CIMB":
                    bal = [(s, rows[i+1]) for i, s in enumerate(rows) if any(keyword.lower() in s.lower() for keyword in  ['OPENING BALANCE'])]
                    df, bal, df_null_date = CIMB_main(rows, bal, sort)

                elif bank_selected == "PBB":
                    df, bal, df_null_date = PBB_main(rows, sort)

                elif bank_selected == "RHB":
                    bal = [(s, rows[i+1]) for i, s in enumerate(rows) if any(keyword.lower() in s.lower() for keyword in  ['B/FBALANCE', 'B/F BALANCE'])]
                    cleaned_bal = []
                    for entry in bal:
                        text_match = re.search(r'(.+?)\s*BALANCE', entry[0])
                        balance_match = re.search(r'BALANCE (.+)', entry[0])
                        text = text_match.group(1).strip()
                        balance = balance_match.group(1).strip()
                        balance = re.sub(r'[^0-9.]', '', balance.replace(',', ''))

                        cleaned_bal.append((text + " Balance " + balance, entry[1]))
                    bal = cleaned_bal
                    df, bal = RHB_main(rows, bal, sort)
                    df_null_date = pd.DataFrame(columns=['DATE', 'DESCRIPTION', 'AMOUNT', 'BALANCE', 'Date2'])

                elif bank_selected == "RHB-reflex":
                    bal = [s for i, s in enumerate(rows) if any(keyword.lower() in s.lower() for keyword in  ['Beginning Balance'])]
                    df, bal = RHB_reflex_main(rows, bal, sort)
                    df_null_date = pd.DataFrame(columns=['DATE', 'DESCRIPTION', 'AMOUNT', 'BALANCE', 'Date2'])

                elif bank_selected == "OCBC":
                    bal = [(s, rows[i+1]) for i, s in enumerate(rows) if any(keyword.lower() in s.lower() for keyword in  ['Balance B/F'])]
                    df, bal, df_null_date = OCBC_main(rows, bal, sort)
                    
                elif bank_selected == "AM BANK":
                    bal = [(s, rows[i+1]) for i, s in enumerate(rows) if any(keyword.lower() in s.lower() for keyword in  ['Baki Bawa Ke Hadapan / Balance b/f'])]
                    df, bal, df_null_date = AM_main(rows, bal, sort)

                elif bank_selected == "BANK ISLAM":
                    bal = [(s, rows[i+1]) for i, s in enumerate(rows) if any(keyword.lower() in s.lower() for keyword in  ['BALB/F'])]
                    df, bal, df_null_date = ISLAM_main(rows, bal, sort)

            num_rows_per_page = 15
            num_pages = (len(df) + num_rows_per_page - 1) // num_rows_per_page
            df = df.reset_index(drop=True)
            final_df = df[['Date', 'Description', 'Amount', 'Balance']]
            # Convert DataFrame to HTML
            table_html = final_df.to_html(classes='table table-striped', index=False, table_id='transactions-table')
            p2p_keywords = ['Bay Smart', 'BM Ram Capital', 'B2B Finpal', 'Capsphere Services', 'Crowd Sense', 'P2P nusa kapital', 'fbm crowdtech', 'microleap', 'modalku ventures', 'moneysave', 'quickash']
            p2p_df = final_df[final_df.apply(lambda row: any(keyword.lower() in row['Description'].lower() for keyword in p2p_keywords), axis=1)]
            p2p_indices_list = (p2p_df.index.astype(int)).tolist()
            warning, warning_index = check_balance_within_month(df, bal, sort, bank_selected)
            summary_data = summary_main(df, bal, bank_selected)
            chart_data, average_daily_balances = plot_to_html_image(df, bal)
            type_data = type(df)
            repeat = find_repeat(final_df)
            df['Amount2'] = pd.to_numeric(df['Amount2'], errors='coerce')
            top5_amounts = df.loc[df['Amount2'].abs().nlargest(5).index]
            ending_balances = [entry['ENDING BALANCE'] for entry in summary_data.values()]
            average_ending_balance = sum(ending_balances) / len(ending_balances)
            df_null_date = df_null_date.drop('Date2', axis=1)
            df_null_date_html = df_null_date.to_html(classes='table table-striped', index=False, table_id='invalid-table')
            
            return render_template('home/dashboard.html', file_path=file_path.replace("\\","").split("/")[-1], table=table_html, num_pages=num_pages, bank_selected=bank_selected, 
                                   current_page=current_page, summary_data=summary_data, chart_data=chart_data, warning_index=warning_index, 
                                   p2p = p2p_indices_list, type_data=type_data, repeat=repeat, top5_amounts= top5_amounts, 
                                   average_ending_balance=average_ending_balance, average_daily_balances=average_daily_balances, FZ=fz, df_null_date=df_null_date_html)

        # Handle the case where data is not available
        return redirect(url_for('authentication_blueprint.upload_file'))
    except Exception as e:
        print(e)
        return render_template('home/error.html', error=f'{str(e)}')
        # pass
    
@blueprint.route('/download_annotated')
def download_annotated():
    annotated_path = os.path.join(os.getenv('TMP', '/tmp'), "annotated.pdf")
    if os.path.exists(annotated_path):
        return send_file(annotated_path, as_attachment=True)

@blueprint.route('/fraud')
def route_fraud():
    return render_template('home/fraud.html')

@blueprint.route('/fraud_process', methods=['POST'])
def fraud_process():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']
    bank_selected = request.form.get('bank')
    
    # Check if the file is empty
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    # Process the file as needed
    # For example, save it to a folder
    file_path = os.path.join(os.getenv('TMP', '/tmp'), "file.pdf")

    file.save(file_path)

    results = []
    for pagenum, page in enumerate(extract_pages(file_path)):

        # Iterate the elements that composed a page
        for element in page:

            # Check if the element is a text element
            if isinstance(element, LTTextContainer):
                result = text_extraction(element)
                results.append((pagenum, result))
    
    font_data = extract_fonts(file_path)
    print(font_data)
    print(bank_selected)
    empty=False
    if bank_selected == "MBB":
        fonts = [font_base for fonts in font_data for font_id, font_base in fonts.items() if font_id.startswith("/F")]
        if len(fonts) < 3:
            empty = True
            fonts = ["Tahoma", "NSimSun", "MicrosoftSansSerif"]
    elif bank_selected == "CIMB":
        fonts = [font_base for fonts in font_data for font_id, font_base in fonts.items() if font_id.startswith("/F")]
        if len(fonts) < 3:
            empty = True
            fonts = ["Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique"]
    elif bank_selected == "HLBB":
        fonts = [font_base for fonts in font_data for font_id, font_base in fonts.items() if font_id.startswith("/F")]
        if len(fonts) < 3:
            empty = True
            fonts = ["Dax-Regular", "Dax-Bold", "Dax-Italic", "Dax-BoldItalic"]
    elif bank_selected == "BANK ISLAM":
        fonts = [font_base for fonts in font_data for font_id, font_base in fonts.items() if font_id.startswith("/F")]
        if len(fonts) < 3:
            empty = True
            fonts = ["Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique"]
    elif bank_selected == "UOB":
        fonts = [font_base for fonts in font_data for font_id, font_base in fonts.items() if font_id.startswith("/F")]
        if len(fonts) < 3:
            empty = True
            fonts = ["Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique"]
    elif bank_selected == "RHB":
        fonts = [font_base for fonts in font_data for font_id, font_base in fonts.items() if font_id.startswith("/F") or font_id.startswith("/V")]
    elif bank_selected == "ALLIANCE":
        fonts = [font_base for fonts in font_data for font_id, font_base in fonts.items() if font_id.startswith("/F")]
        if len(fonts) < 3:
            empty = True
            fonts = ["ArialMT", "Arial-BoldMT", "Arial-ItalicMT", "Arial-BoldItalicMT"]
    elif bank_selected =="PBB" or bank_selected =="OCBC" or bank_selected =="AM BANK":
        fonts = []
    else:
        fonts = [font_base for fonts in font_data for font_id, font_base in fonts.items() if font_id.startswith("/F")]
    unique_list = list(set(fonts))
    print(unique_list)
    
    if len(unique_list) > 1:
        fraud_json = draw_rectangles(file_path, results, unique_list, empty)
    elif bank_selected =="PBB" or bank_selected =="OCBC" or bank_selected =="AM BANK":
        fraud_json = json.dumps({"Warning": "Font detection is currently not available for Public Bank, OCBC and Am bank."})
    else:
        fraud_json = json.dumps({"Warning": "The system detects that the PDF has been modified, but cannot pinpoint the modified content. These alterations may not necessarily pertain to changes in the transaction record; they could involve other aspects."})

    meta = metadata(file_path)
    if len(meta) > 0:
        meta = [{key: str(value.decode('windows-1252')) if isinstance(value, bytes) else value for key, value in entry.items()} for entry in meta]
    else:
        meta = [{'Message': 'No Metadata Found.'}]
    
    return jsonify({'meta': meta[0], 'font': fraud_json})

@blueprint.route('/preview_file')
def preview_file():
    annotated_path = os.path.join(os.getenv('TMP', '/tmp'), "annotated.pdf")
    return send_file(annotated_path, as_attachment=False)

@blueprint.errorhandler(Exception)
def handle_error(e):
    return render_template('home/error.html', error=str(e))
    # pass

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
