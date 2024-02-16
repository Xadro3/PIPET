import cv2
import os
vipshome = r'D:\Benutzer\Downloads\Stuff\vips-dev-w64-all-8.15.1\vips-dev-8.15\bin'
os.environ['PATH'] = vipshome + ';' + os.environ['PATH']
import pyvips


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
        if cv2.countNonZero(self.data)<=0:
            return True
        else:
            return False
