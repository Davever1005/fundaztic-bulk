# -*- coding: utf-8 -*-

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




# Create application
app = Flask(__name__)


# Generate a secret key
secret_key = os.urandom(24)
app.secret_key = secret_key

CORS(app)

scaler = load(open('files/scaler.joblib', 'rb'))

status_data = (0,0)

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


# Define template file
TEMPLATE_FILE = 'index.html'
MANUAL_FILE = 'manual.html'

class MyForm(FlaskForm):
    csv_file = FileField('Upload CSV File')

@app.route('/', methods=['POST', 'GET'])
def home():
    return render_template('index.html')

@app.route('/download_template')
def download_template():
    # Create a string with CSV template content
    template_content = '''INSTALLMENT_TENOR_MONTHS,APPLIED_AMOUNT,APPROVED_AMOUNT,INTEREST_RATE_PA,FINAL_PD,RnR(1forY/0forN),Financing_Amount_Principal,Financing_Amount_Interest,YIB,Female_Y(1forY/0forN),Avg_Age_When_apply,Origination_fee,Total_investors,Avg_investor_investment,Guarantor_invested(1forY/0forN),days_to_disb,Day_disbursed,Day_hosted,Nature_of_Business,Entity,STATE,LOAN_PURPOSE,FIN_GRADE,Race'''

    # Send the file for download
    return send_file(
        BytesIO(template_content.encode()),
        as_attachment=True,
        download_name='csv_template.csv',
        mimetype='text/csv'
    )

@app.route('/manual_input', methods=['POST', 'GET'])
def manual_input():
    FEATURE_DEFAULTS = {key: 0.0 for key in FEATURE_KEYS}
    if request.method == 'POST':
        # Get form values
        form_values = [value for value in request.form.values()]
        # Prepare features
        features = FEATURE_DEFAULTS.copy()
        features.update(zip(FEATURE_KEYS[:18], map(float, form_values[:18])))

        # Update features based on selected options
        features[f'Nature_of_Business_{form_values[18]}'] = 1.0
        features[f'Entity_{form_values[19]}'] = 1.0
        features[f'STATE_{form_values[20]}'] = 1.0
        features[f'LOAN_PURPOSE_{form_values[21]}'] = 1.0
        features[f'FIN_GRADE_{form_values[22]}'] = 1.0
        features[f'Race_{form_values[23]}'] = 1.0

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
        return render_template(MANUAL_FILE, result=result, form_values=form_values)

    # If it's a GET request, just render the template with default values
    return render_template(MANUAL_FILE, result=None, form_values=None)

@app.route('/csv_upload', methods=['POST', 'GET'])
def csv_upload():
    form = MyForm()  # Instantiate the form

    if request.method == 'POST' and form.validate_on_submit():
        csv_file = form.csv_file.data  # Access the uploaded file from the form

        global status_data
        status_data = (0,0)

        # Process the CSV file
        df = process_csv(csv_file)

        table_html = df.to_html(classes='table table-striped', index=False)

        return render_template('csv_upload.html', table=table_html, form=form)

    # If it's a GET request or form is not valid, render the template with the form
    return render_template('csv_upload.html', table=None, form=form)

@app.route('/process', methods=['POST', 'GET'])
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
    status_data = (0,0)
    # Read CSV file into a Pandas DataFrame
    df = pd.read_csv(csv_file)

    # Initialize an empty DataFrame for the processed data
    processed_data = pd.DataFrame()


    for index, row in df.iterrows():
        status_data = ((index + 1), len(df))
        result = -1
        # Send status message to the client
        # Prepare features
        FEATURE_DEFAULTS = {key: 0.0 for key in FEATURE_KEYS}
        features = FEATURE_DEFAULTS.copy()
        features.update(zip(FEATURE_KEYS[:18], map(float, row[:18])))

        # Update features based on selected options
        features[f'Nature_of_Business_{row[18]}'] = 1.0
        features[f'Entity_{row[19]}'] = 1.0
        features[f'STATE_{row[20]}'] = 1.0
        features[f'LOAN_PURPOSE_{row[21]}'] = 1.0
        features[f'FIN_GRADE_{row[22]}'] = 1.0
        features[f'Race_{row[23]}'] = 1.0

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
        url = 'http://b579b683-51a0-4526-8834-a3b9a8ee91be.eastus.azurecontainer.io/score'
        headers = {'Content-Type': 'application/json'}
        req = urllib.request.Request(url, body, headers)

        max_retries = 3
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
        # Send a message to the client to indicate the end of processing
    
    # Return the HTML table
    return processed_data



@app.route('/download_processed_csv')
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

@app.route('/get_status', methods=['GET'])
def get_status():
    def generate():
        global status_data
        print(status_data)
        if status_data[1] > 0:
            status_message = f'Processing {status_data[0]} of {status_data[1]}'
        else:
            status_message = '...'
        yield f"data: {json.dumps({'status': status_message})}\n\n"

    return Response(stream_with_context(generate()), content_type='text/event-stream')

@app.errorhandler(Exception)
def handle_error(e):
    return render_template('error.html', error=str(e))
    # pass


if __name__ == '__main__':
    # Run the application
    app.run(debug=True, port=8000)
