import openslide


class SlideSlicer:
    def __init__(self, slide_path, width, height):
        self.slide_path = slide_path
        self.width = width
        self.height = height
        self.slide = None

    def open_slide(self):
        self.slide = openslide.OpenSlide(self.slide_path)

