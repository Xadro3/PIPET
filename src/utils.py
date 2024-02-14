import numpy
import cv2


class Preprocessing:

    @staticmethod
    def apply_tissue_mask(image, thresholding_tech, threshold=127, filter=True, rm_noise=True,noise_filter_level=50,):

        image = cv2.cvtColor(numpy.array(image),cv2.COLOR_RGB2GRAY)

        if rm_noise:
            kernel = numpy.ones((noise_filter_level, noise_filter_level), numpy.uint8)
            image = cv2.morphologyEx(image,cv2.MORPH_OPEN,kernel)
            image = cv2.medianBlur(image,5)
            image = cv2.morphologyEx(image,cv2.MORPH_CLOSE,kernel)


        if thresholding_tech == "OTSU":
            mask = Preprocessing.otsus_binarization(image,filter)
            cv2.imwrite(r'G:\Documents\Bachelor Data\otsus.tiff', mask)
        elif thresholding_tech == "ADAPTIVE":
            Preprocessing.adaptive_thresholding()
        elif thresholding_tech == "SIMPLE":
            Preprocessing.simple_thresholding(threshold)

    @staticmethod
    def otsus_binarization(image, filter):

        if filter:
            blurred_image = cv2.GaussianBlur(image,(5,5),0)
            ret, mask = cv2.threshold(blurred_image,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        else:
            ret, mask = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return mask

    #def adaptive_thresholding(self):

    #def simple_thresholding(self, threshold):
