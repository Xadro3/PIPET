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


class PIPET:
    @staticmethod
    def segment_slide(slide_path, model_path, slice_width, slice_height, ml_input_width, ml_input_height, tissue_mask,
                      thresholding_tech):

        try:
            # Attempt to open the image with openslide
            print("Opening slide...")
            slide = openslide.open_slide(slide_path)

        except openslide.OpenSlideUnsupportedFormatError:
            print("Openslide did not recognize this file, converting now...")
            # If openslide cannot open the image format, catch the error
            # and then open the image with pyvips to convert it to a format openslide can read
            temp_slide = pyvips.Image.new_from_file(slide_path)
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

        for slices in slice_list:
            evaluated_slice = PIPET.run_inference(slices, pytorch_model, ml_input_width, ml_input_height, tissue_mask,
                                                  thresholding_tech)
            vips_output = PIPET.stitch_slide(evaluated_slice, vips_output)

        PIPET.save_slide(vips_output)

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
    def save_slide(slide):
        print("Writing finished image.")
        slide.write_to_file(r'G:\Documents\Bachelor Data\slice complete compressed.tiff', pyramid=True, tile=True,
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
    def run_inference(slice, pytorch_model, input_x, input_y, tissue_mask, thresholding_tech):

        if tissue_mask:
            slice.apply_tissuemask(thresholding_tech)

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

        else:
            print("skipped slice")

        return slice


    @staticmethod #TODO Fix this, it somehow doesnt read the image correctly, puts white lines in between actual data, right side seems broken aswell
    def pil_to_pyvips(pil_image, tile_size):

        width, height = pil_image.size

        pyvips_image = pyvips.Image.black(width, height)


        for y in range(0, height, tile_size):
            for x in range(0, width, tile_size):

                # Extract the tile from the PIL image
                tile = pil_image.crop((x, y, x+tile_size, y+tile_size))

                # Convert the tile to a pyvips image
                tile_vips = pyvips.Image.new_from_memory(tile.tobytes(), tile.width, tile.height, bands=3,
                                                         format="uchar")

                # Paste the tile into the pyvips image
                pyvips_image = pyvips_image.insert(tile_vips, x, y)
                pyvips_image.write_to_file(r'G:\Documents\Bachelor Data\step '+str(y)+'.tiff', pyramid=True, tile=True,
                            compression="jpeg")

        return pyvips_image


if __name__ == "__main__":
    PIPET.segment_slide(r'C:\Users\fabio\OneDrive\Studium\Semester 7\Bachelor\Openslide Images\sample.tif',
                        r'C:\Users\fabio\OneDrive\Studium\Semester 7\Bachelor\ENTE\data\seg_mod_256_2023-02-15.onnx'
                        , 1024, 1024, 256, 256, True, "OTSU")
