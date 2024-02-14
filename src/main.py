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

    def open_slide(self):
        temp_image = Image.open(self.slide_path)
        utils.Preprocessing.apply_tissue_mask(temp_image,"OTSU")
        exit()
        self.slide = openslide.ImageSlide(temp_image)
        print(self.slide.properties)
        self.define_slices()

    def close_slide(self):
        if self.slide is not None:
            self.slide.close()
            self.slide = None

    def process_slide(self):
        # dosomething
        return

    def stitch_slide(self, slice_list):
        stitched_image = Image.new('RGB', self.slide.dimensions, "white")
        for slice in slice_list:
            slice.data = Image.fromarray(slice.data)
            slice.data = slice.data.resize((1024, 1024))
            stitched_image.paste(slice.data, slice.location)
            #slice.close()
        self.save_slice(stitched_image,True)
        #out = pyvips.Image.arrayjoin(array_images, across=len(list_of_pictures))




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
                pyvips.Image.new_from_array(slice).write_to_file(r'G:\Documents\Bachelor Data\slice complete compressed.tiff',compression='jpeg')
        else:
                print("Writing:"+str(slice.location)+" ")
                slice.data.save(r'G:\Documents\Bachelor Data\scanned_slice '+str(slice.location) +'.tiff')

        slice.close()

        return

    def define_slices(self):
        slide_width, slide_height = self.slide.dimensions
        self.vertical_slices = math.ceil(slide_height / self.slice_height)
        self.horizontal_slices = math.ceil(slide_width / self.slice_width)
        slice_positions = []
        for i in range(self.horizontal_slices):
            for y in range(self.vertical_slices):
                slice_positions.append((i * self.slice_height, y * self.slice_width))
        self.slice_slide(slice_positions)
        return

    def resize_slices(self,slice_list, resize_size):
        for slice in slice_list:
            slice.data = slice.data.resize(resize_size)
        return slice_list


    def run_model(self, slice):

        onnx_model = onnx.load_model(r'C:\Users\fabio\OneDrive\Studium\Semester 7\Bachelor\ENTE\data\seg_mod_256_2023-02-15.onnx')
        temp_slice = slice.data.resize((256, 256))
        temp_slice = temp_slice.convert("RGB")
        temp_slice = numpy.array(temp_slice)
        transfromed_input = torch.from_numpy(temp_slice).type(torch.float32).permute(2, 0, 1)

        Image.fromarray(temp_slice).save(r'G:\Documents\Bachelor Data\scanned_slice '+str(slice.location) +'.tiff')

        print(transfromed_input.shape)

        print("Running onnmodel")

        pytorch_model = convert(onnx_model)

        pytorch_model.eval()


        logits = pytorch_model(transfromed_input)

        #logits = logits.sigmoid()
        logits = logits.squeeze()
        logits = logits.squeeze()

        img_array = logits.detach().numpy()

        img_array = np.array(img_array)

        vips_img = pyvips.Image.new_from_memory(img_array, img_array.shape[1], img_array.shape[0], 1, "float")

        vips_img.write_to_file(r'G:\Documents\Bachelor Data\slice_test.tiff', compression='jpeg')


        #pil_image = Image.fromarray(img_array)

        #pil_image = pil_image.resize((1024,1024))

        #vips_img = pyvips.Image.new_from_array(pil_image)

        slice.update_data(img_array)

        #self.save_slice(slice,False)

        return slice




if __name__ == "__main__":
    slide_slicer = SlideSlicer(r'C:\Users\fabio\OneDrive\Studium\Semester 7\Bachelor\Openslided Images\sample.jpf',
                               1024, 1024)
    slide_slicer.open_slide()
    #slide_slicer.load_onnx_model([])
