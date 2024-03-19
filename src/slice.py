import cv2
import numpy
from PIL.Image import fromarray
import os
vipshome = r'D:\Benutzer\Downloads\Stuff\vips-dev-w64-all-8.15.1\vips-dev-8.15\bin'
os.environ['PATH'] = vipshome + ';' + os.environ['PATH']
import utils


class Slice:
    def __init__(self, data, location, sizex, sizey):
        self.data = data
        self.location = location
        self.sizex = sizex
        self.sizey = sizey

    def close(self):
        del self

    def update_data(self, data):
        self.data = data

    def evaluate(self):

        temp_data = numpy.asarray(self.data)
        temp_data = cv2.cvtColor(temp_data, cv2.COLOR_RGB2GRAY)
        _, temp_data = cv2.threshold(temp_data, 127, 255, cv2.THRESH_BINARY)
        if cv2.countNonZero(temp_data) == temp_data.size:
            print("Slice does not contain data.")
            return False
        else:
            print("Slice does contain data")
            return True

    def apply_tissuemask(self, thresholding_tech):
        self.data = fromarray(utils.Preprocessing.apply_tissue_mask(self.data, thresholding_tech))
