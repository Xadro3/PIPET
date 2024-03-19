import numpy
import cv2
import numpy as np


class Preprocessing:

    @staticmethod
    def apply_tissue_mask(image, thresholding_tech, threshold=127, filter=True, rm_noise=True, noise_filter_level=50, ):

        print("Starting masking process")
        image = np.asarray(image)
        original_image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        if rm_noise:
            print("Removing noise")
            kernel = numpy.ones((noise_filter_level, noise_filter_level), numpy.uint8)
            image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
            image = cv2.medianBlur(image, 5)
            image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)

        if thresholding_tech == "OTSU":
            mask = Preprocessing.otsus_binarization(image, filter)
        elif thresholding_tech == "ADAPTIVE":
            Preprocessing.adaptive_thresholding()
        elif thresholding_tech == "SIMPLE":
            Preprocessing.simple_thresholding(threshold)

        combined_image = Preprocessing.merge(original_image, mask)
        del original_image
        del mask

        return combined_image

    @staticmethod
    def otsus_binarization(image, filter):
        print("applying Otsus_binarization")
        if filter:
            blurred_image = cv2.GaussianBlur(image, (5, 5), 0)
            ret, mask = cv2.threshold(blurred_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        else:
            ret, mask = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return mask

    # def adaptive_thresholding(self):

    # def simple_thresholding(self, threshold):
    @staticmethod
    def merge(image, mask):
        print("merging mask with source.")
        kernel = numpy.ones((20, 20), numpy.uint8)

        mask = cv2.bitwise_not(mask)

        mask = cv2.dilate(mask, kernel, 1)

        combined_image = cv2.bitwise_and(image, image, mask=mask)

        height, width, _ = combined_image.shape

        black_pixels = np.where(
            (combined_image[:, :, 0] == 0) &
            (combined_image[:, :, 1] == 0) &
            (combined_image[:, :, 2] == 0)
        )
        combined_image[black_pixels] = [255, 255, 255]

        combined_image = cv2.cvtColor(combined_image, cv2.COLOR_BGR2RGB)

        return combined_image
