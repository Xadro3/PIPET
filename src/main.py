import PIL.Image
import numpy as np
from PIL import Image
import math
from slice import Slice
import utils
import numpy
import torch
import onnx
import os
import tempfile
from onnx2torch import convert

vipshome = r'D:\Benutzer\Downloads\Stuff\vips-dev-w64-all-8.15.1\vips-dev-8.15\bin'
os.environ['PATH'] = vipshome + ';' + os.environ['PATH']
import pyvips
PIL.Image.MAX_IMAGE_PIXELS = None
OPENSLIDE_PATH = r'C:\Users\fabio\OneDrive\Studium\Semester 7\Bachelor\openslide-win64-20231011\openslide-win64-20231011\bin'

if hasattr(os, 'add_dll_directory'):
    with os.add_dll_directory(OPENSLIDE_PATH):
        import openslide
else:
    import openslide


class SlideSlicer:
    def __init__(self, slide_path, width, height):
        self.slide_path = slide_path
        self.slice_width = width
        self.slice_height = height
        self.slide = None

    def open_slide(self,tissue_mask):
        try:
            # Attempt to open the image with openslide
            temp_slide = openslide.open_slide(self.slide_path)
            # Apply tissue mask if necessary
            if tissue_mask:
                temp_slide = temp_slide.read_region((0, 0), 0, temp_slide.dimensions)
                temp_slide = utils.Preprocessing.apply_tissue_mask(numpy.array(temp_slide), "OTSU")
                # Write temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.tiff') as temp_file:
                    temp_vips = pyvips.Image.new_from_memory(temp_slide.data, temp_slide.shape[1], temp_slide.shape[0], 3, "uchar")
                    temp_vips.write_to_file(temp_file.name, pyramid=True, tile=True, compression="jpeg")

                temp_slide = openslide.open_slide(temp_file.name)
                del temp_vips

        except openslide.OpenSlideUnsupportedFormatError:
            print("Openslide did not recognize this file, converting now...")
            # If openslide cannot open the image format, catch the error
            # and then open the image with Pillow to convert it
            temp_slide = Image.open(self.slide_path)
            temp_array = np.array(temp_slide)

            if tissue_mask:
                temp_array = utils.Preprocessing.apply_tissue_mask(temp_array, "OTSU")

            with tempfile.NamedTemporaryFile(delete=False, suffix='.tiff') as temp_file:
                temp_vips = pyvips.Image.new_from_memory(temp_array.data, temp_array.shape[1], temp_array.shape[0], 3, "uchar")
                temp_vips.write_to_file(temp_file.name, pyramid=True, tile=True, compression="jpeg")

            temp_slide.close()
            del temp_array
            del temp_vips

            temp_slide = openslide.open_slide(temp_file.name)

        #this is for testing ONLY
        excerpt = temp_slide.read_region((0, 0), 0, temp_slide.dimensions)
        excerpt.save(r'G:\Documents\Bachelor Data\fresh_from_thresholding.tiff')

        self.slide = temp_slide
        print("Opened image with properties: ")
        print(self.slide.properties)
        self.define_slices()

    def close_slide(self):
        if self.slide is not None:
            self.slide.close()
            self.slide = None


    def stitch_slide(self, slice_list):
        stitched_image = Image.new('RGB', self.slide.dimensions, "white")
        for slice in slice_list:
            print("Stitching slice to:"+str(slice.location))
            slice.data = slice.data.resize((1024, 1024))
            stitched_image.paste(slice.data, slice.location)
            #slice.close()
        self.save_slice(stitched_image,True)





        return

    def slice_slide(self, slice_positions):
        slice_list = []
        for slice_position in slice_positions:
            print("Slicing "+f'{slice_position[0]}{slice_position[1]}')
            slice = self.slide.read_region(slice_position, 0, (self.slice_width, self.slice_height))
            temp_slice = Slice(slice, slice_position, self.slice_width, self.slice_height)
            slice_list.append(self.run_model(temp_slice))
        self.stitch_slide(slice_list)
        return

    #vips_img.write_to_file(r'G:\Documents\Bachelor Data\scanned_slice.tiff', pyramid=True, tile=True, compression="jpeg")
    def save_slice(self, slice, complete_slice):

        if complete_slice:
            print("Writing finished image.")
            pyvips.Image.new_from_array(slice).write_to_file(r'G:\Documents\Bachelor Data\slice complete compressed.tiff',pyramid=True, tile=True, compression="jpeg")
        else:
            print("Writing:"+str(slice.location)+" ")
            slice.data.save(r'G:\Documents\Bachelor Data\scanned_slice '+str(slice.location) +'.tiff')

        slice.close()

        return

    def define_slices(self):
        print("Defining slices.")
        slide_width, slide_height = self.slide.dimensions
        self.vertical_slices = math.ceil(slide_height / self.slice_height)
        self.horizontal_slices = math.ceil(slide_width / self.slice_width)
        slice_positions = []
        for i in range(self.horizontal_slices):
            for y in range(self.vertical_slices):
                slice_positions.append((i * self.slice_height, y * self.slice_width))
        print("Defined: ",len(slice_positions)," Slices.")
        self.slice_slide(slice_positions)
        return

    def resize_slices(self,slice_list, resize_size):
        for slice in slice_list:
            slice.data = slice.data.resize(resize_size)
        return slice_list


    def run_model(self, slice):

        onnx_model = onnx.load_model(r'C:\Users\fabio\OneDrive\Studium\Semester 7\Bachelor\ENTE\data\seg_mod_256_2023-02-15.onnx')
        pytorch_model = convert(onnx_model)
        pytorch_model.eval()

        temp_slice = slice.data.resize((256, 256))
        temp_slice = temp_slice.convert("RGB")
        temp_slice = numpy.array(temp_slice)
        transformed_input = torch.from_numpy(temp_slice).type(torch.float32).permute(2, 0, 1)

        output = pytorch_model(transformed_input)

        output = output.sigmoid()
        output = output.squeeze(0).squeeze(0)
        img_array = output.detach().numpy()

        slice.update_data(img_array)

        numpy_array = transformed_input.permute(1, 2, 0).cpu().numpy()
        # Convert the NumPy array to a PIL Image
        pil_image = Image.fromarray(numpy_array.astype('uint8'))

        Image.fromarray(img_array).save(r'G:\Documents\Bachelor Data\sigmoid-slice '+str(slice.location) +'.tiff')
        pil_image.save(r'G:\Documents\Bachelor Data\back-transmuted_slice '+str(slice.location) +'.tiff')

        slice.data = Image.fromarray((slice.data*255).astype(numpy.uint8))
        slice.data = slice.data.point(lambda x: 1 if x > 120 else 0, mode='1')

        return slice


if __name__ == "__main__":
    slide_slicer = SlideSlicer(r'C:\Users\fabio\OneDrive\Studium\Semester 7\Bachelor\Openslided Images\sample5K.tif',
                               1024, 1024)
    slide_slicer.open_slide(False)
