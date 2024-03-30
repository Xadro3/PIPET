import PIL.Image
from PIL import Image
import math
from slice import Slice
import numpy
import torch
import onnx
import os
import tempfile
from skimage.transform import resize
from numpy import asarray
from onnx2torch import convert
from utils import Preprocessing
import configparser

config = configparser.ConfigParser()
config_file = 'config.ini'
if not os.path.exists(config_file):
    print(f"Error: Config file '{config_file}' not found.")
    exit(1)
config.read('config.ini')
paths_section = config['paths']
vipshome = paths_section.get('vipshome')
openslide_path = paths_section.get('openslide_path')
if not vipshome or not openslide_path:
    print("Error: 'vipshome' or 'openslide_path' not specified in config file.")
    exit(1)

os.environ['PATH'] = vipshome + ';' + os.environ['PATH']
import pyvips

if hasattr(os, 'add_dll_directory'):
    with os.add_dll_directory(openslide_path):
        import openslide
else:
    import openslide

PIL.Image.MAX_IMAGE_PIXELS = None


class PIPET:
    @staticmethod
    def segment_slide(slide_path, model_path, output_path, slice_width, slice_height, ml_input_width, ml_input_height,
                      tissue_mask,
                      thresholding_tech, threshold=127):

        try:
            # Attempt to open the image with openslide
            print("Opening slide...")
            if not tissue_mask:
                slide = openslide.open_slide(slide_path)
            else:
                temp_slide = pyvips.Image.new_from_file(slide_path)
                temp_slide = Preprocessing.apply_tissue_mask(temp_slide, thresholding_tech, threshold)
                temp_slide = pyvips.Image.new_from_array(temp_slide)
                temp_slide.write_to_file(r'G:\Documents\Bachelor Data\cleaned sample.tiff', pyramid=True, tile=True,
                                         compression="jpeg")
                # write a tempfile to disk
                with tempfile.NamedTemporaryFile(delete=False, suffix='.tiff') as temp_file:
                    temp_slide.write_to_file(temp_file.name, pyramid=True, tile=True, compression="jpeg")

                del temp_slide

                slide = openslide.open_slide(temp_file.name)

        except openslide.OpenSlideUnsupportedFormatError:
            print("Converting file...")
            # If openslide cannot open the image format, catch the error
            # and then open the image with pyvips to convert it to a format openslide can read
            temp_slide = pyvips.Image.new_from_file(slide_path)

            if tissue_mask:
                temp_slide = pyvips.Image.new_from_file(slide_path)
                temp_slide = Preprocessing.apply_tissue_mask(temp_slide, thresholding_tech, threshold)
                temp_slide = pyvips.Image.new_from_array(temp_slide)

            # write a tempfile to disk
            with tempfile.NamedTemporaryFile(delete=False, suffix='.tiff') as temp_file:
                temp_slide.write_to_file(temp_file.name, pyramid=True, tile=True, compression="jpeg")

            del temp_slide

            slide = openslide.open_slide(temp_file.name)

        onnx_model = onnx.load_model(model_path)
        onnx.checker.check_model(onnx_model)
        pytorch_model = convert(onnx_model)
        pytorch_model.eval()

        slide_dimensions = slide.dimensions
        print("Opened image with properties: ")
        print(slide.properties)

        # start the pipeline
        slice_positions = PIPET.define_slices(slide, slice_height, slice_width)
        slice_list = PIPET.slice_slide(slice_positions, slide, slice_width, slice_height)
        PIPET.close_slide(slide)

        vips_output = pyvips.Image.black(slide_dimensions[0], slide_dimensions[1])

        index1 = 0
        index2 = 0

        for slices in slice_list:
            index1, index2, evaluated_slice = PIPET.run_inference(slices, pytorch_model, ml_input_width,
                                                                  ml_input_height, index1, index2)
            vips_output = PIPET.stitch_slide(evaluated_slice, vips_output)

        PIPET.save_slide(vips_output, output_path)

        print("Evaluated: " + str(index1) + " Skipped: " + str(index2))

        return

    @staticmethod
    def close_slide(slide):
        if slide is not None:
            slide.close()

    @staticmethod
    def stitch_slide(slice, blank):
        print("Stitching slice to:" + str(slice.location))
        # We want to have the large file as PyVips, as this library is used to saving our large image in the end.
        vips_slice = pyvips.Image.new_from_array(asarray(slice.data))
        blank = blank.insert(vips_slice, slice.location[0], slice.location[1])
        slice.close()
        return blank

    @staticmethod
    def slice_slide(slice_positions, slide, slice_width, slice_height):
        slice_list = []
        for slice_position in slice_positions:
            print("Slicing " + f'{slice_position[0]}' + ':' + f'{slice_position[1]}')
            slice = slide.read_region(slice_position, 0, (slice_width, slice_height))
            temp_slice = Slice(slice, slice_position, slice_width, slice_height)
            slice_list.append(temp_slice)

        return slice_list

    @staticmethod
    def save_slide(slide, output_path):
        print("Writing finished image.")
        os.makedirs(output_path, exist_ok=True)
        output_file_path = os.path.join(output_path, "segmented_slide.tiff")
        slide.write_to_file(output_file_path, pyramid=True, tile=True,
                            compression="jpeg")

        return

    @staticmethod
    def define_slices(slide, slice_height, slice_width):
        print("Defining slices.")
        slide_width, slide_height = slide.dimensions
        vertical_slices = math.ceil(slide_height / slice_height)
        horizontal_slices = math.ceil(slide_width / slice_width)
        slice_positions = []

        for i in range(horizontal_slices):
            for y in range(vertical_slices):
                slice_positions.append((i * slice_height, y * slice_width))
        print("Defined: ", len(slice_positions), " Slices.")

        return slice_positions

    @staticmethod
    def run_inference(slice, pytorch_model, input_x, input_y, index1, index2):

        if slice.evaluate():
            print("evaluating...")
            slice.data = slice.data.convert("RGB")
            temp_slice = resize(asarray(slice.data), (input_x, input_y))
            transformed_input = torch.from_numpy(temp_slice).type(torch.float32).permute(2, 0, 1)

            output = pytorch_model(transformed_input)

            output = output.sigmoid()
            output = output.squeeze(0).squeeze(0)
            img_array = output.detach().numpy()
            img_array = resize(img_array, (slice.sizey, slice.sizex))

            slice.data = Image.fromarray((img_array * 255).astype(numpy.uint8))
            slice.data = slice.data.point(lambda x: 1 if x > 120 else 0, mode='1')
            index1 = index1 + 1

        else:
            print("skipped slice")
            index2 = index2 + 1

        return index1, index2, slice


if __name__ == "__main__":
    # Accept user input for file paths and parameters
    input_slide_path = input("Enter the path to the slide image: ")
    input_model_path = input("Enter the path to the segmentation model: ")
    output_path = input("Enter the path for the segmented image output: ")
    block_size_x = int(input("Enter the slice size (X): "))
    block_size_y = int(input("Enter the slice size (Y): "))
    patch_size_x = int(input("Enter the ml input size (X): "))
    patch_size_y = int(input("Enter the ml input size (Y): "))
    masking = input("Do you want to apply a tissue mask? (True/False): ").lower() == "true"
    if masking:
        method = input("Enter the thresholding method SIMPLE, OTSU or ADAPTIVE: ").upper()
    else:
        method = "none"
    if method == "SIMPLE":
        threshold = int(input("Enter the threshold value: "))
    else:
        threshold = 0


    PIPET.segment_slide(input_slide_path, input_model_path, output_path, block_size_x, block_size_y,
                        patch_size_x, patch_size_y, masking, method, threshold)

    #PIPET.segment_slide(r'C:\Users\fabio\OneDrive\Studium\Semester 7\Bachelor\Openslide Images\sample.tif',
    #                    r'C:\Users\fabio\OneDrive\Studium\Semester 7\Bachelor\ENTE\data\seg_mod_256_2023-02-15.onnx',
    #                    r'G:\Documents\Bachelor Data',
    #                    1024, 1024, 256, 256, True, "OTSU", 127)
