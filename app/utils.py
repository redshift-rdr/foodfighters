import cv2
from pyzbar.pyzbar import decode, ZBarSymbol
import numpy

def get_barcode_from_imagedata(imagedata : str):
    image_unchanged = cv2.imdecode(numpy.fromstring(imagedata, numpy.uint8), cv2.IMREAD_UNCHANGED)
    image_greyscale = cv2.imdecode(numpy.fromstring(imagedata, numpy.uint8), cv2.IMREAD_GRAYSCALE)
    ret, image_threshold = cv2.threshold(image_greyscale, 0, 255, cv2.THRESH_OTSU)

    bar_u = decode(image_unchanged)
    bar_g = decode(image_greyscale)
    bar_t = decode(image_threshold)

    barcodes = []
    barcodes.extend(bar_u)
    barcodes.extend(bar_g)
    barcodes.extend(bar_t)

    #blur = cv2.GaussianBlur(opencv_image, (5, 5), 0)
    #ret, bw_im = cv2.threshold(opencv_image, 0, 255, cv2.THRESH_OTSU)
    #cv2.imwrite('temp.png', bw_im)

    if not barcodes:
        return None
    
    return barcodes[0]