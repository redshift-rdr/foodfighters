from lib2to3 import pytree
from flask import render_template, flash, redirect, request, url_for, session, make_response
from app import app, db
from app.models import *
from app.forms import *
from datetime import datetime, timedelta
import io 
from PIL import Image
import pytesseract

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/image/upload', methods=['POST'])
def upload():
    data = request.data
    
    image = Image.open(io.BytesIO(data))
    print(pytesseract.image_to_string(image))

    return 'cool'