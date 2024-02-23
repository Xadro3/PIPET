import cv2
import numpy
import os
vipshome = r'D:\Benutzer\Downloads\Stuff\vips-dev-w64-all-8.15.1\vips-dev-8.15\bin'
os.environ['PATH'] = vipshome + ';' + os.environ['PATH']


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
        temp_data = cv2.cvtColor(temp_data,cv2.COLOR_RGB2GRAY)
        if cv2.countNonZero(temp_data)<=0:
            print("Slice contains data.")
            return True
        else:
            print("Slice does not contain data")
            return False
