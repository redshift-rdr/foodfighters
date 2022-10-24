from base64 import decode
from lib2to3 import pytree
from flask import render_template, flash, redirect, request, url_for, session, make_response
from app import app, db
from app.models import *
from app.forms import *
from datetime import datetime, timedelta
from app.utils import get_barcode_from_imagedata
import requests

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/scan')
def scan():
    return render_template('scan.html')

@app.route('/scan_barcode', methods=['POST'])
def upload():
    data = request.data

    barcode = get_barcode_from_imagedata(data)
    if not barcode:
        return 'no barcode was detected', 400

    return redirect(url_for('search_barcode', barcode=barcode.data.decode()))

@app.route('/barcode/search/<barcode>')
def search_barcode(barcode):
    url = f'https://off:off@world.openfoodfacts.net/api/v2/product/{barcode}'

    try:
        r = requests.get(url)
        data = r.json()
    except Exception as e:
        return f'there was an error: {e}'

    return render_template('scanned.html', barcode=barcode, data=data)