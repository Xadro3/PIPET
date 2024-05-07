
![grafik](https://github.com/Xadro3/PIPET/assets/22886138/4b5209bf-9e53-4ee2-b3ba-b27ee7412d3b)

PIPET: Pre-processed Image Preparator and Tiler

PIPET is a powerful tool designed to streamline the preparation of histological images for machine learning-based segmentation. It offers a comprehensive pipeline for processing whole slide images (WSIs), facilitating efficient data preparation for training ML models and evaluating their performance.
Features

    Tiled Image Generation: PIPET can generate tiled images of any specified size from input WSIs, enabling efficient handling of large-scale histological data.

    Resize and Stitch: Resize tiled images and seamlessly stitch them back into the original image size after evaluation, preserving data integrity and accuracy.

    Tissue Masking: Apply tissue masks to input images, crucial for identifying histopathological structures and enhancing segmentation accuracy.

    Interoperability: Ensure compatibility with a variety of ML-based segmentation algorithms, offering customizable inputs and outputs to suit different model requirements.

Technology

PIPET is developed in Python, leveraging its portability, extensive library ecosystem, and readability. Key packages utilized include OpenCV, Pillow, OpenSlide, NumPy, and PyVips, providing essential functionalities for image processing, manipulation, and handling.

Usage

To use PIPET, simply provide a ML model, a WSI, and preferred input parameters. PIPET can be run as a standalone tool from the command line or integrated into existing projects as a package.
