'''
This is a simple OCR library that uses the Google Cloud Vision API to extract text from images.
'''

from .cloud_ocr import  OCR
from .recognizer import Recognize

__all__ = ['OCR', 'Recognize']
