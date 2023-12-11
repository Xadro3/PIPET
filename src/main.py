import PIL.Image
from PIL import Image
PIL.Image.MAX_IMAGE_PIXELS = None
import math
from slice import Slice
import os
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
        self.slide = openslide.OpenSlide(self.slide_path)
        print(self.slide.properties)
        self.define_slices()
    def close_slide(self):
        if self.slide is not None:
            self.slide.close()
            self.slide = None

    def process_slide(self):
        #dosomething
        return

    def stitch_slide(self,slice_list):
        stitched_image = Image.new('RGBA', self.slide.dimensions,"white")
        stitched_image.save(r"G:\Documents\Bachelor Data\slice complete.tiff",format="TIFF", compression ='7')
        for slice in slice_list:
            stitched_image.paste(slice.data, slice.location)
        self.save_slice(stitched_image, "complete")
        return

    def slice_slide(self, slice_positions):
        slice_list = []
        for slice_position in slice_positions:
            slice = self.slide.read_region(slice_position, 0, (self.slice_width, self.slice_height))
            temp_slice = Slice(slice,slice_position,self.slice_width,self.slice_height)
            slice_list.append(temp_slice)
            self.save_slice(slice, slice_position)
        print(len(slice_list))
        self.stitch_slide(slice_list)
        return

    def save_slice(self, slice, index):
        print("Writing slice"+ str(index))
        slice.save(r"G:\Documents\Bachelor Data\slice" + str(index)+ ".tiff",format="TIFF",compression ='7')
        return

    def define_slices(self):
        slide_width, slide_height = self.slide.dimensions
        vertical_slices = math.ceil(slide_height/self.slice_height)
        horizontal_slices = math.ceil(slide_width/self.slice_width)
        slice_positions =[]
        for i in range(horizontal_slices):
            for y in range(vertical_slices):
                slice_positions.append((i*self.slice_height,y*self.slice_width ))
        self.slice_slide(slice_positions)
        return


if __name__ == "__main__":
    slide_slicer = SlideSlicer(r'C:\Users\fabio\OneDrive\Studium\Semester 7\Bachelor\Openslided Images\sample.tif', 5000,5000)
    slide_slicer.open_slide()

