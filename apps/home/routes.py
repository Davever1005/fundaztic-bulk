# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.home import blueprint
from flask import render_template, redirect, request, url_for
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound


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
from python.UOB_others import UOB2_main
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
import ast
from collections import defaultdict
from python.SG_UOB import SG_UOB_main
from python.SG_OCBC import SG_OCBC_main
from python.SG_DBS import SG_DBS_main
from python.SG_DBS2 import SG_DBS2_main
from python.SG_check import SG_check_balance_within_month
from dotenv import load_dotenv
from functools import wraps
from werkzeug.exceptions import HTTPException
import traceback
import xml.dom.minidom
import xmltodict
from dateutil.relativedelta import relativedelta

load_dotenv()
# API_KEY = os.getenv('API_KEY')
API_KEY = "5aaf7548-68f9-4afb-9381-b5118712dfa6"

VALID_CATEGORIES = {
    'Nature_of_Business': [
        'Accommodation & Food Service Activities',
        'Administrative and Support Service Activities',
        'Agriculture, Forestry and Fishing',
        'Arts, Entertainment and Recreation',
        'Construction',
        'Education',
        'Financial and Insurance/Takaful Activities',
        'Human Health and Social Work Activities',
        'Information and Communication',
        'Manufacturing',
        'Other Service Activities',
        'Professional, Scientific & Technical Activities',
        'Real-Estate Activities',
        'Transportation & Storage',
        'Water, Sewerage & Waste Mgmt & Related Activities',
        'Wholesale & Retail (incl Motor Vehicle Repairs)'
    ],
    'Entity': [
        'Partnership', 'Private Limited', 'Sole Proprietor'
    ],
    'STATE': [
        'JOHOR', 'KEDAH', 'KELANTAN', 'MELAKA', 'NEGERI SEMBILAN',
        'PAHANG', 'PERAK', 'PERLIS', 'PULAU PINANG', 'SABAH',
        'SARAWAK', 'SELANGOR', 'TERENGGANU', 'WILAYAH PERSEKUTUAN'
    ],
    'LOAN_PURPOSE': [
        'Asset acquisition', 'Contract financing',
        'Debt consolidation / refinancing', 'Invoice financing',
        'Marketing and advertising', 'Other business purpose',
        'Purchase of equipment', 'Upgrading / Renovation',
        'Working Capital'
    ],
    'FIN_GRADE': [
        'A1', 'A2', 'B3', 'B4', 'C5', 'C6', 'D7', 'D8', 'X1'
    ],
    'Race': [
        'Chinese', 'Indian', 'Malay', 'Others'
    ]
}

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        provided_key = request.headers.get('X-API-Key')
        if not provided_key or provided_key != API_KEY:
            return jsonify({"error": "Invalid or missing API key"}), 401
        return f(*args, **kwargs)
    return decorated

@blueprint.errorhandler(Exception)
def handle_exception(e):
    # Pass through HTTP errors
    if isinstance(e, HTTPException):
        return jsonify(error=str(e)), e.code
    
    # Now handle non-HTTP exceptions
    return jsonify(error="An unexpected error occurred"), 500

# Load the models and scalers
ctos_scaler = load('files/Scaler3.joblib')
ctos_model = load('files/RandomForestRegressor.joblib')
pre_scaler = load('files/prescaler.joblib')
post_scaler = load('files/scaler.joblib')

def expand_features(data, feature_keys):
    expanded = {key: 0 for key in feature_keys}
    for key, value in data.items():
        if key in feature_keys:
            expanded[key] = value
        elif key in ['Nature_of_Business', 'Entity', 'STATE', 'LOAN_PURPOSE', 'FIN_GRADE', 'Race']:
            prefix = f"{key}_"
            matching_keys = [k for k in feature_keys if k.startswith(prefix)]
            for k in matching_keys:
                expanded[k] = 1 if k == f"{prefix}{value}" else 0
    return expanded

def flatten_list(nested_list):
    flattened = []
    for item in nested_list:
        if isinstance(item, list):
            flattened.extend(flatten_list(item))
        else:
            flattened.append(item)
    return flattened

def find_key_in_nested_dict(nested_dict, key):
    if isinstance(nested_dict, dict):
        if key in nested_dict:
            return nested_dict[key]
        else:
            # Recursively search in the nested dictionaries
            for value in nested_dict.values():
                result = find_key_in_nested_dict(value, key)
                if result is not None:
                    return result
    return None

def process_ccris_data(inst_arrears, acc_date, facilities, f_bal, f_ins, section_ccris_data):    
    temporal_arrears = defaultdict(list)
    
    accounts_data = find_key_in_nested_dict(section_ccris_data, "accounts")
    if accounts_data:
        accounts_account_data = find_key_in_nested_dict(accounts_data, "account")
        if accounts_account_data:
            if not isinstance(accounts_account_data, list):
                accounts_account_data = [accounts_account_data]
            
            for acc_data in accounts_account_data:
                approval_date = acc_data.get('approval_date')
                acc_date.append(approval_date)
                sub_accounts_data = find_key_in_nested_dict(acc_data, "sub_accounts")
                if sub_accounts_data:
                    sub_account_data = sub_accounts_data['sub_account']
                    if not isinstance(sub_account_data, list):
                        sub_account_data = [sub_account_data]
                    
                    for fac in sub_account_data:
                        facilities.append(fac['facility']['@code'])
                        cr_positions = fac['cr_positions']['cr_position']
                        
                        if not isinstance(cr_positions, list):
                            cr_positions = [cr_positions]
                        
                        for position in cr_positions:
                            f_bal.append(position.get("balance", "N/A"))
                            f_ins.append(position.get("inst_amount", "N/A"))
                            
                            position_date = position.get("position_date")
                            inst_arrears = position.get("inst_arrears", "N/A")
                            
                            if position_date and inst_arrears != "N/A":
                                try:
                                    date = datetime.strptime(position_date, '%d-%m-%Y')
                                    month_year = date.strftime('%Y-%m')
                                    temporal_arrears[month_year].append(inst_arrears)
                                except ValueError:
                                    print(f"Warning: Invalid date format: {position_date}")
    
    return temporal_arrears

def extract_features_from_xml(xml_data):
    # Parse XML
    xml_doc = xml.dom.minidom.parseString(xml_data)
    
    # Extract features (you'll need to adapt this based on your XML structure)
    features = {}
    # Initialize a dictionary to store the extracted data
    name_data_dict = {}
    all_status = []
    all_pos = []
    i = 0

    # Get all the field elements
    fields = xml_doc.getElementsByTagName('field')
    for field in fields:
        field_name = field.getAttribute('name')
        
        # Extract and print the guid value
        field_value = "Uploaded"
        features = {}
        
        # Extract and process the report_xml value
        if field_name == "report_xml":
            for child in field.childNodes:
                last_date_appointed = []
                dates = []
                company = []
                status = []
                position = []
                acc_date = []
                appro_date = []
                facilities = []
                f_code = None
                min_date = None
                A_application = None
                P_application = None
                borrower_limit = None
                borrower_fec_limit = None
                borrower_outstanding = None
                guarantor_limit = None
                guarantor_fec_limit = None
                guarantor_outstanding = None
                secure_no = None
                secure_total = None
                f_bal = []
                f_ins = []
                f_arr = []
                sum_fi = 0
                sum_non_fi = 0
                sum_lawyer = 0

                data = child.nodeValue
                data_dict = xmltodict.parse(data)
                data_json = json.dumps(data_dict, indent=4)
                enq_date = data_dict['report']['enq_report']['header']['enq_date']
                # Define the file path where you want to save the data

                section_c_data =  find_key_in_nested_dict(data_dict, "section_c")
                # last_date_appointed & owner_other_company
                if section_c_data:
                    section_c_records_data =  find_key_in_nested_dict(section_c_data, "record")
                    if isinstance(section_c_records_data, list):
                        for record_data in section_c_records_data:
                            app_date = None
                            com = None
                            stat = None
                            pos = None
                            if 'position' in record_data:
                                pos = record_data['position']
                            # Assuming each item in the list is a dictionary
                            if 'appoint' in record_data:
                                app_date=record_data['appoint']
                            if 'company_name' in record_data:
                                com=record_data['company_name']
                            if 'status' in record_data:
                                stat=record_data['status']
                            dates.append(app_date)
                            company.append(com)
                            status.append(stat)
                            all_status.append(stat)
                            position.append(pos)
                            all_pos.append(pos)
                    elif section_c_records_data:
                        app_date = None
                        com = None
                        stat = None
                        pos = None
                        if 'position' in section_c_records_data:
                            pos = section_c_records_data['position']
                        # Assuming each item in the list is a dictionary
                        if 'appoint' in section_c_records_data:
                            app_date=section_c_records_data['appoint']
                        if 'company_name' in section_c_records_data:
                            com=section_c_records_data['company_name']
                        if 'status' in section_c_records_data:
                            stat=section_c_records_data['status']
                        dates.append(app_date)
                        company.append(com)
                        status.append(stat)
                        all_status.append(stat)
                        position.append(pos)
                        all_pos.append(pos)
                    
                else:
                    enquiry_data =  find_key_in_nested_dict(data_dict, "enquiry")
                    section_c_data =  find_key_in_nested_dict(enquiry_data[-1], "section_c")
                    # last_date_appointed & owner_other_company
                    if section_c_data:
                        section_c_records_data =  find_key_in_nested_dict(section_c_data, "record")
                        if isinstance(section_c_records_data, list):
                            for record_data in section_c_records_data:
                                app_date = None
                                com = None
                                stat = None
                                pos = None
                                if 'position' in record_data:
                                    pos = record_data['position']
                                # Assuming each item in the list is a dictionary
                                if 'appoint' in record_data:
                                    app_date=record_data['appoint']
                                if 'company_name' in record_data:
                                    com=record_data['company_name']
                                if 'status' in record_data:
                                    stat=record_data['status']
                                dates.append(app_date)
                                company.append(com)
                                status.append(stat)
                                all_status.append(stat)
                                position.append(pos)
                                all_pos.append(pos)
                        elif section_c_records_data:
                            app_date = None
                            com = None
                            stat = None
                            pos = None
                            if 'position' in section_c_records_data:
                                pos = section_c_records_data['position']
                            # Assuming each item in the list is a dictionary
                            if 'appoint' in section_c_records_data:
                                app_date=section_c_records_data['appoint']
                            if 'company_name' in section_c_records_data:
                                com=section_c_records_data['company_name']
                            if 'status' in section_c_records_data:
                                stat=section_c_records_data['status']
                            dates.append(app_date)
                            company.append(com)
                            status.append(stat)
                            all_status.append(stat)
                            position.append(pos)
                            all_pos.append(pos)
                for date_str in dates:
                    if date_str is not None:
                        last_date_appointed.append(datetime.strptime(date_str, '%d-%m-%Y'))
                # A_application & P_application
                # No. of facilities_Borrower & No. of facilities_Guarantor
                section_ccris_data =  find_key_in_nested_dict(data_dict, "section_ccris")
                if section_ccris_data:
                    section_ccris_summary_data =  find_key_in_nested_dict(section_ccris_data, "summary")
                    if section_ccris_summary_data:
                        A_application = section_ccris_summary_data['application']['approved']["@count"]
                        P_application = section_ccris_summary_data['application']['pending']["@count"]
                        borrower_data = section_ccris_summary_data['liabilities']['borrower']
                        if isinstance(borrower_data, dict):
                            borrower_limit = borrower_data['@total_limit']
                            borrower_fec_limit = borrower_data['@fec_limit']
                            borrower_outstanding = borrower_data['#text']
                        guarantor_data = section_ccris_summary_data['liabilities']['guarantor']
                        if isinstance(guarantor_data, dict):
                            guarantor_limit = guarantor_data['@total_limit']
                            guarantor_fec_limit = guarantor_data['@fec_limit']
                            guarantor_outstanding = guarantor_data['#text']
                else:
                    enquiry_data =  find_key_in_nested_dict(data_dict, "enquiry")
                    section_ccris_data =  find_key_in_nested_dict(enquiry_data[-1], "section_ccris")
                    if section_ccris_data:
                        section_ccris_summary_data =  find_key_in_nested_dict(section_ccris_data, "summary")
                        if section_ccris_summary_data:
                            A_application = section_ccris_summary_data['application']['approved']["@count"]
                            P_application = section_ccris_summary_data['application']['pending']["@count"]
                            borrower_data = section_ccris_summary_data['liabilities']['borrower']
                            if isinstance(borrower_data, dict):
                                borrower_limit = borrower_data['@total_limit']
                                borrower_fec_limit = borrower_data['@fec_limit']
                                borrower_outstanding = borrower_data['#text']
                            guarantor_data = section_ccris_summary_data['liabilities']['guarantor']
                            if isinstance(guarantor_data, dict):
                                guarantor_limit = guarantor_data['@total_limit']
                                guarantor_fec_limit = guarantor_data['@fec_limit']
                                guarantor_outstanding = guarantor_data['#text']
                
                # Earliest_credit_vintage & No. of type of facilities
                bal = None
                ins = None
                facilities = []
                f_bal = []
                f_ins = []
                acc_date = []
                inst_arrears = []  # List to store all inst_arrears
                facility_arrears = []

                # Main processing logic
                section_ccris_data = find_key_in_nested_dict(data_dict, "section_ccris")
                if section_ccris_data:
                    temporal_arrears = process_ccris_data(inst_arrears, acc_date, facilities, f_bal, f_ins, section_ccris_data)
                else:
                    enquiry_data = find_key_in_nested_dict(data_dict, "enquiry")
                    if enquiry_data:
                        if isinstance(enquiry_data, list):
                            section_ccris_data = find_key_in_nested_dict(enquiry_data[-1], "section_ccris")
                        else:
                            section_ccris_data = find_key_in_nested_dict(enquiry_data, "section_ccris")
                        
                        if section_ccris_data:
                            temporal_arrears = process_ccris_data(section_ccris_data)
                def analyze_conduct(temporal_arrears, enq_date_str):
                    # Convert enq_date string to datetime object
                    enq_date = datetime.strptime(enq_date_str, '%Y-%m-%d')
                    
                    # Adjust enq_date to the end of the month
                    enq_date_end_of_month = enq_date.replace(day=1) + relativedelta(months=1) - relativedelta(days=1)

                    # Calculate the date 12 months before enq_date
                    twelve_months_ago = enq_date - relativedelta(months=11)
                    
                    # Adjust twelve_months_ago to the start of the month
                    twelve_months_ago = twelve_months_ago.replace(day=1)

                    # Initialize result dictionary
                    result = {
                        "last_12_months": 0,
                        "last_9_months": 0,
                        "last_6_months": 0,
                        "last_3_months": 0,
                        "earliest_3_months": 0,
                        "earliest_6_months": 0,
                        "earliest_9_months": 0
                    }

                    # If temporal_arrears is empty, return the initialized result
                    if not temporal_arrears:
                        return {
                            'result': result,
                            'twelve_months_ago': twelve_months_ago
                        }

                    def safe_int(x):
                        if x is None:
                            return 0
                        try:
                            return int(x)
                        except ValueError:
                            return 0

                    # Convert string keys to datetime objects and filter for last 12 months
                    sorted_arrears = sorted(
                        [(datetime.strptime(date, '%Y-%m'), value) 
                        for date, value in temporal_arrears.items()
                        if twelve_months_ago <= datetime.strptime(date, '%Y-%m') <= enq_date_end_of_month],
                        key=lambda x: x[0]
                    )

                    if not sorted_arrears:
                        return {
                            'result': result,
                            'twelve_months_ago': twelve_months_ago
                        }

                    total_months = len(sorted_arrears)

                    # Calculate for different periods
                    for index, (date, value_list) in enumerate(sorted_arrears):
                        months_from_latest = (enq_date_end_of_month.year - date.year) * 12 + enq_date_end_of_month.month - date.month
                        months_from_start = index

                        # Convert values to integers, handling None and non-digit strings
                        int_values = [safe_int(x) for x in value_list]
                        sum_values = sum(int_values)
                        
                        if months_from_latest < 3:
                            result["last_3_months"] += sum_values
                        if months_from_latest < 6:
                            result["last_6_months"] += sum_values
                        if months_from_latest < 9:
                            result["last_9_months"] += sum_values
                        result["last_12_months"] += sum_values

                        if months_from_start < 3:
                            result["earliest_3_months"] += sum_values
                        if months_from_start < 6:
                            result["earliest_6_months"] += sum_values
                        if months_from_start < 9:
                            result["earliest_9_months"] += sum_values

                    return {
                        'result': result,
                        'twelve_months_ago': twelve_months_ago
                    }
                result_dict = analyze_conduct(temporal_arrears, enq_date)
                conduct_analysis = result_dict['result']
                twelve_months_ago = result_dict['twelve_months_ago']
                for date_str in acc_date:
                    if date_str is not None:
                        appro_date.append(datetime.strptime(date_str, '%d-%m-%Y'))
                if len(appro_date) > 0:
                    min_date = min(appro_date).year
                
                #secure
                secure_no = None
                secure_total = None
                secure_limit = None
                ccris_data =  find_key_in_nested_dict(data_dict, "section_ccris")
                if ccris_data:
                    ccris_derivatives_data =  find_key_in_nested_dict(ccris_data, "derivatives")
                    if ccris_derivatives_data:
                        ccris_derivatives_facilities_data =  find_key_in_nested_dict(ccris_derivatives_data, "facilities")
                        if "secure" in ccris_derivatives_facilities_data:
                            secure_no = ccris_derivatives_facilities_data["secure"]['@total']
                            if 'outstanding' in ccris_derivatives_facilities_data["secure"]:
                                secure_total = ccris_derivatives_facilities_data["secure"]['outstanding']['#text']
                                secure_limit = ccris_derivatives_facilities_data["secure"]['outstanding']['@limit']
                else:
                    enquiry_data =  find_key_in_nested_dict(data_dict, "enquiry")
                    ccris_data =  find_key_in_nested_dict(enquiry_data[-1], "section_ccris")
                    if ccris_data:
                        ccris_derivatives_data =  find_key_in_nested_dict(ccris_data, "derivatives")
                        if ccris_derivatives_data:
                            ccris_derivatives_facilities_data =  find_key_in_nested_dict(ccris_derivatives_data, "facilities")
                            if "secure" in ccris_derivatives_facilities_data:
                                secure_no = ccris_derivatives_facilities_data["secure"]['@total']
                                if 'outstanding' in ccris_derivatives_facilities_data["secure"]:
                                    secure_total = ccris_derivatives_facilities_data["secure"]['outstanding']['#text']
                                    secure_limit = ccris_derivatives_facilities_data["secure"]['outstanding']['@limit']
                #unsecure
                unsecure_no = None
                unsecure_total = None
                unsecure_limit = None
                ccris_data =  find_key_in_nested_dict(data_dict, "section_ccris")
                if ccris_data:
                    ccris_derivatives_data =  find_key_in_nested_dict(ccris_data, "derivatives")
                    if ccris_derivatives_data:
                        ccris_derivatives_facilities_data =  find_key_in_nested_dict(ccris_derivatives_data, "facilities")
                        if "unsecure" in ccris_derivatives_facilities_data:
                            unsecure_no = ccris_derivatives_facilities_data["unsecure"]['@total']
                            if 'outstanding' in ccris_derivatives_facilities_data["unsecure"]:
                                unsecure_total = ccris_derivatives_facilities_data["unsecure"]['outstanding']['#text']
                                unsecure_limit = ccris_derivatives_facilities_data["unsecure"]['outstanding']['@limit']
                else:
                    enquiry_data =  find_key_in_nested_dict(data_dict, "enquiry")
                    ccris_data =  find_key_in_nested_dict(enquiry_data[-1], "section_ccris")
                    if ccris_data:
                        ccris_derivatives_data =  find_key_in_nested_dict(ccris_data, "derivatives")
                        if ccris_derivatives_data:
                            ccris_derivatives_facilities_data =  find_key_in_nested_dict(ccris_derivatives_data, "facilities")
                            if "unsecure" in ccris_derivatives_facilities_data:
                                unsecure_no = ccris_derivatives_facilities_data["unsecure"]['@total']
                                if 'outstanding' in ccris_derivatives_facilities_data["unsecure"]:
                                    unsecure_total = ccris_derivatives_facilities_data["unsecure"]['outstanding']['#text']
                                    unsecure_limit = ccris_derivatives_facilities_data["unsecure"]['outstanding']['@limit']
                
                #tr_report
                tr_report = 0
                tr =  find_key_in_nested_dict(data_dict, "tr_report")
                if tr:
                    tr_report = 1

                #ETR PLUS
                etr_plus = 0
                etr =  find_key_in_nested_dict(data_dict, "section_etr_plus")
                if etr:
                    if "@data" in etr:
                        if etr["@data"] == 'true':
                            etr_plus = 1

                # HISTORICAL ENQUIRY
                history = {}
                section_b_data =  find_key_in_nested_dict(data_dict, "section_b")
                if section_b_data:
                    if "@data" in section_b_data:
                        if section_b_data["@data"]=="true":
                            if "history" in section_b_data:
                                for y in section_b_data["history"]:
                                    year = y["@year"]
                                    if year not in history:
                                        history[year] = {}
                                    for p in y["period"]:
                                        month = p["@month"]
                                        value = p["entity"]
                                        history[year][month] = value
                else:
                    enquiry_data =  find_key_in_nested_dict(data_dict, "enquiry")
                    section_b_data =  find_key_in_nested_dict(enquiry_data[-1], "section_b")
                    if section_b_data:
                        if "@data" in section_b_data:
                            if section_b_data["@data"]=="true":
                                if "history" in section_b_data:
                                    for y in section_b_data["history"]:
                                        year = y["@year"]
                                        if year not in history:
                                            history[year] = {}
                                        for p in y["period"]:
                                            month = p["@month"]
                                            value = p["entity"]
                                            history[year][month] = value

                # FICO
                fico = None
                fico_factor=[]
                enq_sum =  find_key_in_nested_dict(data_dict, "enq_sum")
                if enq_sum:
                    if isinstance(enq_sum, list):
                        if 'fico_index' in enq_sum[1]:
                            fico = enq_sum[1]['fico_index']['@score']
                            fico_factor = enq_sum[1]['fico_index']['fico_factor']
                    elif 'fico_index' in enq_sum:
                        fico = enq_sum['fico_index']['@score']
                        fico_factor = enq_sum['fico_index']['fico_factor']
                else:
                    enquiry_data =  find_key_in_nested_dict(data_dict, "enquiry")
                    try:
                        ficoElement =  find_key_in_nested_dict(enquiry_data[-1], "fico_index")
                        if ficoElement:
                            fico = ficoElement['@score']
                            fico_factor = ficoElement['fico_factor']
                    except Exception as e:
                        pass
                status_types = status_types = {
                    'TERMINATED',
                    'STRIKING OFF',
                    'ACTIVE',
                    'EXPIRED',
                    'EXISTING',
                    'NONE',
                    'WINDING UP',
                    'DISSOLVED'
                }
                status_counts = {key: 0 for key in status_types}
                for stat in status:
                    if stat in status_counts:
                        status_counts[stat] += 1

                pos_types = {
                    'DIRECTOR  /  SHARE HOLDER',
                    'DIRECTOR',
                    'SOLE PROPRIETOR',
                    'SHARE HOLDER',
                    'PARTNER'
                }
                pos_counts = {key: 0 for key in pos_types}
                for pos in position:
                    if pos in pos_counts:
                        pos_counts[pos] += 1

                for year_data in history.values():
                    for month_data in year_data.values():
                        for item in month_data:
                            if item['@type'] == 'FI':
                                sum_fi += int(item['@value'])
                            elif item['@type'] == 'NON-FI':
                                sum_non_fi += int(item['@value'])
                            elif item['@type'] == 'LAWYER':
                                sum_lawyer += int(item['@value'])

                fico_factor_count = 0
                for item in fico_factor:
                    if '@code' in item and item['@code'] != '':
                        fico_factor_count += 1
                

                features['NO_OF_COMPANY'] = len(company)
                for status_type in status_types:
                    status_key = f"STATUS_{status_type}" if status_type is not None else "STATUS_NONE"
                    features[status_key] = status_counts[status_type]
                for pos_type in pos_types:
                    pos_key = f"POSITION_{pos_type}" if pos_type is not None else "POSITION_NONE"
                    features[pos_key] = pos_counts[pos_type]
                features['APPLICATION_APPROVED'] = A_application
                features['APPLICATION_PENDING'] = P_application
                features['BORROWER_LIMIT'] = borrower_limit
                features['BORROWER_OUTSTANDING'] = borrower_outstanding
                features['MIN_DATE_YEAR'] = min_date
                flattened_f_ins = flatten_list(f_ins)
                f_ins_cleaned = [int(x.replace(',', '')) for x in flattened_f_ins if x is not None]
                f_ins_sum = sum(f_ins_cleaned)

                features['FACILITIES_INSTALLMENT'] = f_ins_sum
                features['CONDUCT_LAST_12_MONTHS'] = conduct_analysis['last_12_months']
                features['CONDUCT_LAST_9_MONTHS'] = conduct_analysis['last_9_months']
                features['CONDUCT_LAST_6_MONTHS'] = conduct_analysis['last_6_months']
                features['CONDUCT_LAST_3_MONTHS'] = conduct_analysis['last_3_months']
                features['CONDUCT_EARLIEST_3_MONTHS'] = conduct_analysis['earliest_3_months']
                features['CONDUCT_EARLIEST_6_MONTHS'] = conduct_analysis['earliest_6_months']
                features['CONDUCT_EARLIEST_9_MONTHS'] = conduct_analysis['earliest_9_months']
                features['NO_OF_SECURE'] = secure_no
                features['TOTAL_SECURE'] = secure_total
                features['%_LIMIT_SECURE'] = secure_limit
                features['NO_OF_UNSECURE'] = unsecure_no
                features['TOTAL_UNSECURE'] = unsecure_total
                features['%_LIMIT_UNSECURE'] = unsecure_limit
                features['TRADE_REF'] = tr_report
                features['ETR_PLUS'] = etr_plus
                features['ENQUIRY_FI'] = sum_fi
                features['ENQUIRY_NONFI'] = sum_non_fi
                features['ENQUIRY_LAWYER'] = sum_lawyer
        
        return features

@blueprint.route('/api/ctos_predict', methods=['POST'])
@require_api_key
def ctos_predict():
    try:
        xml_data = request.data  # Assume the XML is sent in the request body
        
        # Parse XML and extract features
        extracted_features = extract_features_from_xml(xml_data)
        
        # Get the expected feature names from the model
        FEATURE_KEYS = ctos_model.feature_names_in_.tolist()
        
        # Create a dictionary with all features initialized to 0
        features = {key: 0 for key in FEATURE_KEYS}
        
        # Update the features dictionary with extracted values
        for key, value in extracted_features.items():
            if key in FEATURE_KEYS:
                features[key] = value
        
        # Convert to DataFrame, ensuring the order matches the model's expectations
        df = pd.DataFrame([features])
        
        # Ensure all required features are present
        if not all(key in df.columns for key in FEATURE_KEYS):
            missing_keys = [key for key in FEATURE_KEYS if key not in df.columns]
            return jsonify({"error": f"Missing features: {', '.join(missing_keys)}"}), 400

        # Scale features
        scaled_features = pd.DataFrame(ctos_scaler.transform(df), columns=FEATURE_KEYS)
        
        # Make prediction
        prediction = round(ctos_model.predict(scaled_features)[0], 4)
        
        return jsonify({"prediction": prediction})
    except Exception as e:
        return jsonify({"error": f"An error occurred in ctos_predict: {str(e)}"}), 500

@blueprint.route('/api/pre_predict', methods=['POST'])
@require_api_key
def pre_predict():
    try:
        data = request.json
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
        # Validate categorical fields
        for field in ['Nature_of_Business', 'Entity', 'STATE', 'LOAN_PURPOSE', 'FIN_GRADE', 'Race']:
            if field in data:
                valid_values = VALID_CATEGORIES.get(field, [])
                if data[field] not in valid_values:
                    return jsonify({"error": f"Invalid value for {field}: {data[field]}"}), 400
        expanded_data = expand_features(data, FEATURE_KEYS)
        features = pd.DataFrame([expanded_data])
        
        scaled_features = pd.DataFrame(pre_scaler.transform(features), columns=FEATURE_KEYS)
        
        # Prepare data for API request
        api_data = {
            "Inputs": {"data": scaled_features.to_dict('records')},
            "GlobalParameters": 0.0
        }

        # Encode data and make API request
        body = str.encode(json.dumps(api_data))
        url = 'http://a83ce717-57dd-4207-a549-09b71aab95a0.eastus.azurecontainer.io/score'
        headers = {'Content-Type': 'application/json'}
        req = urllib.request.Request(url, body, headers)

        try:
            response = urllib.request.urlopen(req, timeout=10)
            result = response.read().decode("utf8", 'ignore')
            prediction = float(result[13:-3])
            prediction = max(0, min(1, prediction))  # Clip between 0 and 1
            prediction = round(prediction, 4)
            return jsonify({"prediction": prediction})
        except urllib.error.HTTPError as error:
            return jsonify({"error": error.read().decode("utf8", 'ignore')}), 500
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred during prediction"}), 500

@blueprint.route('/api/post_predict', methods=['POST'])
@require_api_key
def post_predict():
    try:
        data = request.json
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
        
        # Validate categorical fields
        for field in ['Nature_of_Business', 'Entity', 'STATE', 'LOAN_PURPOSE', 'FIN_GRADE', 'Race']:
            if field in data:
                valid_values = VALID_CATEGORIES.get(field, [])
                if data[field] not in valid_values:
                    return jsonify({"error": f"Invalid value for {field}: {data[field]}"}), 400
                
        expanded_data = expand_features(data, FEATURE_KEYS)
        features = pd.DataFrame([expanded_data])
        
        scaled_features = pd.DataFrame(post_scaler.transform(features), columns=FEATURE_KEYS)
        
        # Prepare data for API request
        api_data = {
            "Inputs": {"data": scaled_features.to_dict('records')},
            "GlobalParameters": 0.0
        }

        # Encode data and make API request
        body = str.encode(json.dumps(api_data))
        url = 'http://b579b683-51a0-4526-8834-a3b9a8ee91be.eastus.azurecontainer.io/score'
        headers = {'Content-Type': 'application/json'}
        req = urllib.request.Request(url, body, headers)

        try:
            response = urllib.request.urlopen(req, timeout=10)
            result = response.read().decode("utf8", 'ignore')
            prediction = float(result[13:-3])
            prediction = max(0, min(1, prediction))  # Clip between 0 and 1
            prediction = round(prediction, 4)
            return jsonify({"prediction": prediction})
        except urllib.error.HTTPError as error:
            return jsonify({"error": error.read().decode("utf8", 'ignore')}), 500
    except Exception as e:
        return jsonify({"error": f"An error occurred in post_predict: {str(e)}"}), 500


@blueprint.route('/home')
@login_required
def index():
    return render_template('home/Home.html')

@blueprint.route('/ctos_manual', methods=['GET', 'POST'])
@login_required
def ctos_manual():
    print(dir(current_user))
    scaler = load(open('files/Scaler3.joblib', 'rb'))
    model = load('files/RandomForestRegressor.joblib')

    # Get the correct feature names and order from the model
    FEATURE_KEYS = model.feature_names_in_.tolist()
    
    FEATURE_DEFAULTS = {key: 0.0 for key in FEATURE_KEYS}

    if request.method == 'POST':
        try:
            # Create a dictionary to store form values
            form_data = {}
            for key in FEATURE_KEYS:
                value = request.form.get(key, FEATURE_DEFAULTS[key])
                form_data[key] = float(str(value).replace(",", ""))

            # Create a DataFrame with the correct feature order
            df = pd.DataFrame([form_data])

            # Scale the features
            scaled_df = pd.DataFrame(scaler.transform(df), columns=FEATURE_KEYS)

            # Make prediction
            prediction = round(model.predict(scaled_df)[0], 4)

            # Pass the result and form values to the template
            return render_template('home/ctos_manual.html', result=prediction, form_values=list(form_data.values()))

        except Exception as e:
            # Log the error and return an error message
            print(f"An error occurred: {str(e)}")
            return render_template('home/ctos_manual.html', error="An error occurred while processing your request. Please try again.")

    # If it's a GET request, just render the template with default values
    return render_template('home/ctos_manual.html', result=None, form_values=None)

@blueprint.route('/ctos_csv_upload', methods=['GET'])
@login_required
def ctos_csv_upload():
    form = MyForm()
    return render_template('home/ctos_csv.html', form=form)


@blueprint.route('/ctos_process', methods=['POST'])
@login_required
def ctos_process():
    if 'csv_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    csv_file = request.files['csv_file']

    if csv_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        df = ctos_process_csv(csv_file)
        table_html = df.to_html(classes='table table-striped', index=False)
        return jsonify({'table': table_html})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def ctos_process_csv(csv_file):
    scaler = load(open('files/Scaler3.joblib', 'rb'))
    model = load('files/RandomForestRegressor.joblib')

    # Get feature names from the model
    FEATURE_KEYS = model.feature_names_in_.tolist()
    df = pd.read_csv(csv_file)
    if not all(key in df.columns for key in FEATURE_KEYS):
        missing_keys = [key for key in FEATURE_KEYS if key not in df.columns]
        raise ValueError(f"Missing columns in CSV: {', '.join(missing_keys)}")

    df['Result'] = df.apply(lambda row: process_row(row, FEATURE_KEYS, scaler, model), axis=1)

    processed_path = os.path.join(os.getenv('TMP', '/tmp'), "result.csv")
    df.to_csv(processed_path, index=False)

    return df

def process_row(row, feature_keys, scaler, model):
    try:
        if row.isnull().any():
            return "Incomplete data"

        features = {key: float(str(row[key]).replace(",", "")) for key in feature_keys}
        
        # Create a DataFrame with feature names
        features_df = pd.DataFrame([features], columns=feature_keys)
        
        # Scale the features
        scaled_features = pd.DataFrame(scaler.transform(features_df), columns=feature_keys)
        
        # Make prediction
        return round(model.predict(scaled_features)[0], 4)
    except Exception as e:
        return f"Error: {str(e)}"


@blueprint.route('/download_ctostemplate')
@login_required
def download_ctostemplate():
    # Create a string with CSV template content
    template_content = '''NO_OF_COMPANY,STATUS_ACTIVE,STATUS_DISSOLVED,STATUS_EXISTING,STATUS_TERMINATED,STATUS_WINDING UP,STATUS_NONE,STATUS_EXPIRED,STATUS_STRIKING OFF,POSITION_DIRECTOR  /  SHARE HOLDER,POSITION_DIRECTOR,POSITION_SOLE PROPRIETOR,POSITION_SHARE HOLDER,POSITION_PARTNER,APPLICATION_APPROVED,APPLICATION_PENDING,BORROWER_LIMIT,BORROWER_OUTSTANDING,MIN_DATE_YEAR,FACILITIES_INSTALLMENT,CONDUCT_LAST_12_MONTHS,CONDUCT_LAST_9_MONTHS,CONDUCT_LAST_6_MONTHS,CONDUCT_LAST_3_MONTHS,CONDUCT_EARLIEST_3_MONTHS,CONDUCT_EARLIEST_6_MONTHS,CONDUCT_EARLIEST_9_MONTHS,NO_OF_SECURE,TOTAL_SECURE,%_LIMIT_SECURE,NO_OF_UNSECURE,TOTAL_UNSECURE,%_LIMIT_UNSECURE,TRADE_REF,ETR_PLUS,ENQUIRY_FI,ENQUIRY_NONFI,ENQUIRY_LAWYER'''

    # Send the file for download
    return send_file(
        BytesIO(template_content.encode()),
        as_attachment=True,
        download_name='csv_template(ctos).csv',
        mimetype='text/csv'
    )

@blueprint.route('/manual_input', methods=['GET', 'POST'])
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
def download_processed_csv():
    processed_path = os.path.join(os.getenv('TMP', '/tmp'), "result.csv")
    if os.path.exists(processed_path):
        return send_file(processed_path, as_attachment=True)
    else:
        return jsonify({'error': 'Processed data not found in session'})
    

@blueprint.route('/pre_manual_input', methods=['GET', 'POST'])
@login_required
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
@login_required
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
@login_required
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
@login_required
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

@blueprint.route('/OCRMY', methods=['GET', 'POST'])
@login_required
def upload_file():
    file_path = None
    bank_selected = None  # Initialize the variable


    if request.method == 'POST':
        file = request.files['file']
        bank_selected = request.form.get('bank')  # Get the selected bank value
        sort = request.form.get('sort')

        if sort == "":
            sort = 1

        if file and bank_selected and sort:
            # Save the uploaded PDF file to the local storage directory
            file_path = os.path.join(os.getenv('TMP', '/tmp'), file.filename)
            print(file_path)
            # file_path = f'static/{file.filename}'
            file.save(file_path)

            # Store the file path in the session for access in the analysis route
            session['file_path'] = file_path
            session['bank_selected'] = bank_selected
            session['sort'] = sort


            return redirect(url_for('home_blueprint.analysis'))

    return render_template('home/index.html', bank_selected=bank_selected)

def split_rows(row):
    # Split the row by '\n' if any element contains '\n'
    if any(isinstance(val, str) and '\n' in val for val in row):
        split_values = [str(val).split('\n') if isinstance(val, str) else [val] for val in row]
        # Determine the maximum length of sublists in the original data
        max_length = max(len(sublist) for sublist in split_values)
        # Fill shorter sublists with empty strings to match the maximum length
        filled_data = [sublist + [''] * (max_length - len(sublist)) for sublist in split_values]
        # Use zip to transpose the list and then convert it to a list of lists
        restructured_data = [list(row) for row in zip(*filled_data)]
        return restructured_data
    else:
        return [list(row)]


@blueprint.route('/analysis', methods=['GET'])
@login_required
def analysis():
    try:
        current_page = 1
        page_num = 0
        text = ""
        file_path = session.get('file_path')
        bank_selected = session.get('bank_selected')
        sort = session.get('sort')
        temp = 1
        begin_bal = 0
        print(file_path, bank_selected)
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
                            for _, row in table_df.iterrows():
                                split_row_list = split_rows(row)
                                for split_row in split_row_list:
                                    df_list.append(pd.DataFrame([split_row], columns=table_df.columns))
                with pdfplumber.open(file_path) as pdf:
                    alltext = []
                    for page in pdf.pages:
                        alltext.extend(page.extract_text().split('\n'))
                df, bal, df_null_date = HLBB_main(df_list, alltext, sort=1)
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
            elif bank_selected == 'UOB_others':
                bal = []
                pdf = pdfplumber.open(file_path)
                df_list = []
                for i in range(len(pdf.pages)):
                    page = pdf.pages[i]
                    table = page.extract_table(table_settings={"horizontal_strategy": "text", "vertical_strategy": "explicit", "explicit_vertical_lines": [57,110,165,340,410,480,560]})
                    if table:
                        table_df = pd.DataFrame(table[2:])
                        df_list.append(table_df)
                df = UOB2_main(df_list, 1, temp)
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
                    bal = [(s, rows[i+1]) for i, s in enumerate(rows) if any(keyword.lower() in s.lower() for keyword in  ['BEGINNING BALANCE', 'BEGINNINGBALANCE'])]
                    df, bal, df_null_date = MBB_main(rows,bal, 1)
                
                elif bank_selected == "CIMB":
                    bal = [(s, rows[i+1]) for i, s in enumerate(rows) if any(keyword.lower() in s.lower() for keyword in  ['OPENING BALANCE'])]
                    df, bal, df_null_date = CIMB_main(rows, bal, sort)

                elif bank_selected == "PBB":
                    df, bal, df_null_date, begin_bal = PBB_main(rows, sort, begin_bal)

                elif bank_selected == "RHB":
                    bal = [(s, rows[i+1]) for i, s in enumerate(rows) if any(keyword.lower() in s.lower() for keyword in  ['B/FBALANCE', 'B/F BALANCE'])]
                    cleaned_bal = []
                    for entry in bal:
                        text_match = re.search(r'(.+?)\s*BALANCE', entry[0])
                        balance_match = re.search(r'BALANCE (.+)', entry[0])
                        text = text_match.group(1).strip()
                        balance = balance_match.group(1).strip()
                        
                        # Check if the balance ends with a negative or positive sign
                        if balance.endswith('-') or balance.endswith('+'):
                            sign = balance[-1]
                            balance = sign + balance[:-1]  # Move the sign to the front
                        
                        # Remove any remaining non-numeric characters except the decimal point and signs
                        balance = re.sub(r'[^0-9.+-]', '', balance.replace(',', ''))

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
                    bal = [(s, rows[i+1]) for i, s in enumerate(rows) if any(keyword.lower() in s.lower() for keyword in  ['Baki Bawa Ke Hadapan', 'Balance b/f', 'Balance Brought Fwd'])]
                    print(bal)
                    df, bal, df_null_date = AM_main(rows, bal, sort)

                elif bank_selected == "BANK ISLAM":
                    bal = [(s, rows[i+1]) for i, s in enumerate(rows) if any(keyword.lower() in s.lower() for keyword in  ['BALB/F', 'BAL B/F'])]
                    df, bal, df_null_date = ISLAM_main(rows, bal, sort)

            num_rows_per_page = 15
            num_pages = (len(df) + num_rows_per_page - 1) // num_rows_per_page
            df = df.reset_index(drop=True)
            final_df = df[['Date', 'Description', 'Amount', 'Balance']]
            # Convert DataFrame to HTML
            table_html = final_df.to_html(classes='table table-striped', index=False, table_id='transactions-table')
            p2p_keywords = ['Bay Smart', 'BM Ram Capital', 'B2B Finpal', 'Capsphere Services', 'Crowd Sense', 'P2P nusa kapital', 'fbm crowdtech', 'microleap', 'modalku ventures', 'moneysave', 'quickash', 'Peoplender']
            p2p_df = final_df[final_df.apply(lambda row: any(keyword.lower().replace(" ", "") in row['Description'].lower().replace(" ", "") for keyword in p2p_keywords), axis=1)]
            p2p_indices_list = (p2p_df.index.astype(int)).tolist()
            warning, warning_index = check_balance_within_month(df, bal, sort, bank_selected)
            summary_data = summary_main(df, bal, bank_selected, begin_bal)
            print(summary_data)
            chart_data, average_daily_balances = plot_to_html_image(df, bal)
            type_data = type(df)
            repeat = find_repeat(final_df)
            df['Amount2'] = pd.to_numeric(df['Amount2'], errors='coerce')
            df_abs = df.copy()
            df_abs = df_abs.sort_values('Amount2', ascending=False)

            # Get the top 5 rows
            top5_amounts = df_abs.head(5)

            # Create separate debit and credit columns
            top5_amounts['Debit'] = np.where(top5_amounts['Amount'].str[-1] == '-', 
                                            top5_amounts['Amount'].str[:-1], '')
            top5_amounts['Credit'] = np.where(top5_amounts['Amount'].str[-1] == '+', 
                                            top5_amounts['Amount'].str[:-1], '')

            # Select and reorder columns
            columns_to_display = ['Date', 'Description', 'Debit', 'Credit']
            top5_amounts = top5_amounts[columns_to_display]
            top5_amounts_table = top5_amounts.to_html(classes='table table-striped table-bordered', index=False)

            ending_balances = [entry['ENDING BALANCE'] for entry in summary_data.values()]
            average_ending_balance = sum(ending_balances) / len(ending_balances)
            df_null_date = df_null_date.drop('Date2', axis=1)
            df_null_date_html = df_null_date.to_html(classes='table table-striped', index=False, table_id='invalid-table')
            
            return render_template('home/dashboard.html', file_path=file_path.replace("\\","").split("/")[-1], table=table_html, num_pages=num_pages, bank_selected=bank_selected, 
                                   current_page=current_page, summary_data=summary_data, chart_data=chart_data, warning_index=warning_index, 
                                   p2p = p2p_indices_list, type_data=type_data, repeat=repeat, top5_amounts= top5_amounts_table, 
                                   average_ending_balance=average_ending_balance, average_daily_balances=average_daily_balances, df_null_date=df_null_date_html,
                                    df_null_date_len=len(df_null_date))

        # Handle the case where data is not available
        return redirect(url_for('home_blueprint.upload_file'))
    except Exception as e:
        print(e)
        return render_template('home/error.html', error=f'{str(e)}')
        # pass


@blueprint.route('/OCRSG', methods=['GET', 'POST'])
@login_required
def upload_file_sg():
    file_path = None
    bank_selected = None  # Initialize the variable


    if request.method == 'POST':
        file = request.files['file']
        bank_selected = request.form.get('bank')  # Get the selected bank value
        print(file)
        print(bank_selected)
        sort = 1

        if file and bank_selected and sort:
            # Save the uploaded PDF file to the local storage directory
            file_path = os.path.join(os.getenv('TMP', '/tmp'), file.filename)
            print(file_path)
            # file_path = f'static/{file.filename}'
            file.save(file_path)

            # Store the file path in the session for access in the analysis route
            session['file_path'] = file_path
            session['bank_selected'] = bank_selected
            session['sort'] = sort


            return redirect(url_for('home_blueprint.analysis_sg'))

    return render_template('home/ocr_sg.html', bank_selected=bank_selected)


@blueprint.route('/analysis_sg', methods=['GET'])
@login_required
def analysis_sg():
    try:
        current_page = 1
        page_num = 0
        text = ""
        file_path = session.get('file_path')
        bank_selected = session.get('bank_selected')
        sort = session.get('sort')
        temp = 1
        begin_bal = 0
        print(file_path, bank_selected)
        if file_path and bank_selected:
            if bank_selected == 'UOB':
                pdf = pdfplumber.open(file_path)
                bal = []
                df_list = []  # Use a list to store DataFrames

                for i in range(len(pdf.pages)):
                    page = pdf.pages[i]
                    table = page.extract_table(table_settings={"horizontal_strategy": "lines", "vertical_strategy": "explicit", "explicit_vertical_lines": [20,100,175,310,380,460,570]})
                    if table:
                        table_df = pd.DataFrame(table[2:])
                        for _, row in table_df.iterrows():
                            split_row_list = split_rows(row)
                            for split_row in split_row_list:
                                df_list.append(pd.DataFrame([split_row], columns=table_df.columns))
                with pdfplumber.open(file_path) as pdf:
                    alltext = []
                    for page in pdf.pages:
                        alltext.extend(page.extract_text().split('\n'))
                df = SG_UOB_main(df_list, sort=1)
                df_null_date = pd.DataFrame(columns=['DATE', 'DESCRIPTION', 'AMOUNT', 'BALANCE', 'Date2'])
            elif bank_selected == 'OCBC':
                pdf = pdfplumber.open(file_path)
                bal = []
                df_list = []  # Use a list to store DataFrames

                for i in range(len(pdf.pages)):
                    page = pdf.pages[i]
                    custom_table_settings = {
                        "vertical_strategy": "explicit",
                        "horizontal_strategy": "text",
                        "explicit_vertical_lines": [45, 90, 135, 230, 325, 425, 465, 570],
                    }
                    
                    # Extract table with custom settings
                    table = page.extract_table(table_settings=custom_table_settings)
                    if table:
                        table_df = pd.DataFrame(table[2:])
                        for _, row in table_df.iterrows():
                            split_row_list = split_rows(row)
                            for split_row in split_row_list:
                                df_list.append(pd.DataFrame([split_row], columns=table_df.columns))
                with pdfplumber.open(file_path) as pdf:
                    alltext = []
                    for page in pdf.pages:
                        alltext.extend(page.extract_text().split('\n'))
                df = SG_OCBC_main(df_list, sort=1)
                print(bal)
                df_null_date = pd.DataFrame(columns=['DATE', 'DESCRIPTION', 'AMOUNT', 'BALANCE', 'Date2'])
            elif bank_selected == 'DBS':
                bal = []
                pdf = pdfplumber.open(file_path)
                df_list = []
                for i in range(len(pdf.pages)):
                    page = pdf.pages[i]
                    custom_table_settings = {
                        "vertical_strategy": "explicit",
                        "horizontal_strategy": "text",
                        "explicit_vertical_lines": [60, 125, 170, 355, 455, 535, 575],
                    }
                    
                    # Extract table with custom settings
                    table = page.extract_table(table_settings=custom_table_settings)
                    if table:
                        table_df = pd.DataFrame(table[2:])
                        df_list.append(table_df)
                df = SG_DBS_main(df_list, sort=1)
                df_null_date = pd.DataFrame(columns=['DATE', 'DESCRIPTION', 'AMOUNT', 'BALANCE', 'Date2'])
            else:
                print("DBS2")
                bal = []
                pdf = pdfplumber.open(file_path)
                df_list = []
                for i in range(len(pdf.pages)):
                    page = pdf.pages[i]
                    custom_table_settings = {
                        "vertical_strategy": "explicit",
                        "horizontal_strategy": "text",
                        "explicit_vertical_lines": [35, 115, 193, 363, 430, 493, 560],
                    }
                    # Extract table with custom settings
                    table = page.extract_table(table_settings=custom_table_settings)
                    if table:
                        table_df = pd.DataFrame(table[2:])
                        df_list.append(table_df)
                df = SG_DBS2_main(df_list, sort=1)
                df_null_date = pd.DataFrame(columns=['DATE', 'DESCRIPTION', 'AMOUNT', 'BALANCE', 'Date2'])


            num_rows_per_page = 15
            num_pages = (len(df) + num_rows_per_page - 1) // num_rows_per_page
            df = df.reset_index(drop=True)
            final_df = df[['Date', 'Description', 'Amount', 'Balance']]
            print(final_df)
            # Convert DataFrame to HTML
            table_html = final_df.to_html(classes='table table-striped', index=False, table_id='transactions-table')
            warning, warning_index = SG_check_balance_within_month(df, bal, sort, bank_selected)
            summary_data = summary_main(df, bal, bank_selected, begin_bal)
            chart_data, average_daily_balances = plot_to_html_image(df, bal)
            repeat = find_repeat(final_df)
            df['Amount2'] = pd.to_numeric(df['Amount2'], errors='coerce')
            df_abs = df.copy()
            df_abs = df_abs.sort_values('Amount2', ascending=False)
            # Get the top 5 rows
            top5_amounts = df_abs.head(5)

            # Create separate debit and credit columns
            top5_amounts['Debit'] = np.where(top5_amounts['Amount'].str[-1] == '-', 
                                            top5_amounts['Amount'].str[:-1], '')
            top5_amounts['Credit'] = np.where(top5_amounts['Amount'].str[-1] == '+', 
                                            top5_amounts['Amount'].str[:-1], '')
            # Select and reorder columns
            columns_to_display = ['Date', 'Description', 'Debit', 'Credit']
            top5_amounts = top5_amounts[columns_to_display]
            top5_amounts_table = top5_amounts.to_html(classes='table table-striped table-bordered', index=False)

            ending_balances = [entry['ENDING BALANCE'] for entry in summary_data.values()]
            average_ending_balance = sum(ending_balances) / len(ending_balances)
            df_null_date = df_null_date.drop('Date2', axis=1)
            df_null_date_html = df_null_date.to_html(classes='table table-striped', index=False, table_id='invalid-table')
            
            return render_template('home/dashboard_sg.html', file_path=file_path.replace("\\","").split("/")[-1], table=table_html, num_pages=num_pages, bank_selected=bank_selected, 
                                   current_page=current_page, summary_data=summary_data, chart_data=chart_data, warning_index=warning_index, 
                                   repeat=repeat, top5_amounts= top5_amounts_table, 
                                   average_ending_balance=average_ending_balance, average_daily_balances=average_daily_balances, df_null_date=df_null_date_html,
                                    df_null_date_len=len(df_null_date))

        # Handle the case where data is not available
        return redirect(url_for('blueprint.upload_file_sg'))
    except Exception as e:
        print(e)
        return render_template('home/error.html', error=f'{str(e)}')
        # pass


@blueprint.route('/download_annotated')
@login_required
def download_annotated():
    annotated_path = os.path.join(os.getenv('TMP', '/tmp'), "annotated.pdf")
    if os.path.exists(annotated_path):
        return send_file(annotated_path, as_attachment=True)
    

@blueprint.route('/fraud_process', methods=['POST'])
@login_required
def fraud_process():
    try:
        file_path = session.get('file_path')
        bank_selected = session.get('bank_selected')
        print(file_path, bank_selected)
        # Check if the file is empty
        if file_path == '':
            return jsonify({'error': 'No selected file'})

        # Process the file as needed
        # For example, save it to a folder

        results = []
        for pagenum, page in enumerate(extract_pages(file_path)):

            # Iterate the elements that composed a page
            for element in page:

                # Check if the element is a text element
                if isinstance(element, LTTextContainer):
                    result = text_extraction(element)
                    results.append((pagenum, result))
        
        font_data = extract_fonts(file_path)
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
        elif bank_selected == "UOB_others":
            fonts = [font_base for fonts in font_data for font_id, font_base in fonts.items() if font_id.startswith("/F") or font_id.startswith("/V")]
            if len(fonts) < 3:
                empty = True
                fonts = ["Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique", "Arial"]
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
        if len(unique_list) > 1:
            fraud_json = draw_rectangles(file_path, results, unique_list, empty)
        elif bank_selected =="PBB" or bank_selected =="OCBC" or bank_selected =="AM BANK":
            fraud_json = json.dumps({"Warning": "Font detection is currently not available for Public Bank, OCBC and Am bank."})
        else:
            fraud_json = json.dumps({"Warning": "The system detects that the PDF has been modified, but cannot pinpoint the modified content. These alterations may not necessarily pertain to changes in the transaction record; they could involve other aspects."})

        meta = metadata(file_path)
        print(meta)
        if len(meta) > 0:
            meta = [{key: str(value.decode('windows-1252')) if isinstance(value, bytes) else value for key, value in entry.items()} for entry in meta]
            meta = str(meta[0])
            # Remove the forward slash before 'False' or 'True'
            corrected_string = re.sub(r"/'(False|True|Unknown)'", r"'\1'", meta)

            # Convert single quotes to double quotes, except within values
            json_string = re.sub(r"(?<!\\)'([^']+)'(?=:)", r'"\1"', corrected_string)
            # Parse the string as JSON
            meta = ast.literal_eval(corrected_string)
        else:
            meta = {'Message': 'No Metadata Found.'}
        return jsonify({'meta': meta, 'font': fraud_json})
    except Exception as e:
        print(e)
        return jsonify({'meta': None, 'font': None})


@blueprint.route('/fraud_process_sg', methods=['POST'])
@login_required
def fraud_process_sg():
    try:
        file_path = session.get('file_path')
        bank_selected = session.get('bank_selected')
        print(file_path, bank_selected)
        # Check if the file is empty
        if file_path == '':
            return jsonify({'error': 'No selected file'})

        # Process the file as needed
        # For example, save it to a folder

        results = []
        for pagenum, page in enumerate(extract_pages(file_path)):

            # Iterate the elements that composed a page
            for element in page:

                # Check if the element is a text element
                if isinstance(element, LTTextContainer):
                    result = text_extraction(element)
                    results.append((pagenum, result))
        
        font_data = extract_fonts(file_path)
        empty=False
        if bank_selected == "OCBC":
            fonts = [font_base for fonts in font_data for font_id, font_base in fonts.items() if font_id.startswith("/F")]
            fonts.append("Helvetica")
            fonts.append("Helvetica-Bold")
            fonts.append("AAAAAJ+ArialMT")
            if len(fonts) < 2:
                empty = True
                fonts = ["Arial,Bold", "Arial"]
        elif bank_selected == "UOB":
            fonts = [font_base for fonts in font_data for font_id, font_base in fonts.items() if font_id.startswith("/F")]
            if len(fonts) < 3:
                empty = True
                fonts = ["Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique"]
        else:
            fonts = [font_base for fonts in font_data for font_id, font_base in fonts.items() if font_id.startswith("/F")]
        unique_list = list(set(fonts))
        if len(unique_list) > 1:
            fraud_json = draw_rectangles(file_path, results, unique_list, empty)
        elif bank_selected =="PBB" or bank_selected =="OCBC" or bank_selected =="AM BANK":
            fraud_json = json.dumps({"Warning": "Font detection is currently not available for Public Bank, OCBC and Am bank."})
        else:
            fraud_json = json.dumps({"Warning": "The system detects that the PDF has been modified, but cannot pinpoint the modified content. These alterations may not necessarily pertain to changes in the transaction record; they could involve other aspects."})

        meta = metadata(file_path)
        print(meta)
        if len(meta) > 0:
            meta = [{key: str(value.decode('windows-1252')) if isinstance(value, bytes) else value for key, value in entry.items()} for entry in meta]
            meta = str(meta[0])
            # Remove the forward slash before 'False' or 'True'
            corrected_string = re.sub(r"/'(False|True|Unknown)'", r"'\1'", meta)

            # Convert single quotes to double quotes, except within values
            json_string = re.sub(r"(?<!\\)'([^']+)'(?=:)", r'"\1"', corrected_string)
            # Parse the string as JSON
            meta = ast.literal_eval(corrected_string)
        else:
            meta = {'Message': 'No Metadata Found.'}
        return jsonify({'meta': meta, 'font': fraud_json})
    except Exception as e:
        print(e)
        return jsonify({'meta': None, 'font': None})


@blueprint.route('/preview_file')
@login_required
def preview_file():
    annotated_path = os.path.join(os.getenv('TMP', '/tmp'), "annotated.pdf")
    return send_file(annotated_path, as_attachment=False)