#import cv2, 
import requests
from pyzbar.pyzbar import decode, ZBarSymbol
#import numpy
from random import randint 
from PIL import Image
import io

recommended_nutrition = {
    "calories": 2000,
    "fibre": 30,
    "sugar": 30,
    "salt": 6,
    "carbohydrates": 300,
    "fat": 30,
    "protein": 50
}

def generate_random_colour():
    r = lambda: randint(0,255)
    return '#%02X%02X%02X' % (r(),r(),r())

def get_barcode_from_imagedata(imagedata : str):
    try:
        stream = io.BytesIO(imagedata)
        image_unchanged = Image.open(stream)
        image_greyscale = image_unchanged.convert('L')
        image_threshold = image_greyscale.point(lambda x: 255 if x > 100 else 0)
        # change this to use PIL
        #image_greyscale = cv2.imdecode(numpy.fromstring(imagedata, numpy.uint8), cv2.IMREAD_GRAYSCALE)
        #ret, image_threshold = cv2.threshold(image_greyscale, 0, 255, cv2.THRESH_OTSU)
        # image_unchanged = cv2.imdecode(numpy.fromstring(imagedata, numpy.uint8), cv2.IMREAD_UNCHANGED)
        # image_greyscale = cv2.imdecode(numpy.fromstring(imagedata, numpy.uint8), cv2.IMREAD_GRAYSCALE)
        # ret, image_threshold = cv2.threshold(image_greyscale, 0, 255, cv2.THRESH_OTSU)

        bar_u = decode(image_unchanged)
        bar_g = decode(image_greyscale)
        bar_t = decode(image_threshold)
    except Exception as e:
        return None

    barcodes = []
    barcodes.extend(bar_u)
    barcodes.extend(bar_g)
    barcodes.extend(bar_t)

    if not barcodes:
        return None
    
    return barcodes[0]

def add_nutrition_data(nutrition_iterable):
    """
        'nutrition_iterable' needs to be an iterable whose elements implement .nutrition() method
        that returns a dict of nutrition data
    """
    nutrition_info = {}

    for elem in nutrition_iterable:
        if getattr(elem, 'nutrition', None):
            for k,v in elem.nutrition().items():
                if not k in nutrition_info:
                    nutrition_info[k] = v
                else:
                    nutrition_info[k] += v

    return nutrition_info

def search_barcode(barcode):
    url = f'https://off:off@uk.openfoodfacts.net/api/v2/product/{barcode}'

    try:
        r = requests.get(url)
        data = r.json()
    except Exception as e:
        return f'there was an error: {e}'

    return data

def search_off_by_product_name(product_name):
    """ Searches the Open Food Facts API for products which match the product_name
    """

    # we dont want to send requests when product_name is blank
    if not product_name:
        return []

    off_api_url = 'https://uk.openfoodfacts.org/cgi/search.pl'
    search_url = f'{off_api_url}?search_terms={product_name}&json=1&fields=code,product_name,product_quantity,quantity,brands,nutriments&page_size=5'

    data = requests.get(search_url).json().get('products', [])
    return data