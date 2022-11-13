import cv2, requests
from pyzbar.pyzbar import decode, ZBarSymbol
import numpy
from random import randint

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
        image_unchanged = cv2.imdecode(numpy.fromstring(imagedata, numpy.uint8), cv2.IMREAD_UNCHANGED)
        image_greyscale = cv2.imdecode(numpy.fromstring(imagedata, numpy.uint8), cv2.IMREAD_GRAYSCALE)
        ret, image_threshold = cv2.threshold(image_greyscale, 0, 255, cv2.THRESH_OTSU)

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
    url = f'https://off:off@world.openfoodfacts.net/api/v2/product/{barcode}'

    try:
        r = requests.get(url)
        data = r.json()
    except Exception as e:
        return f'there was an error: {e}'

    return data
