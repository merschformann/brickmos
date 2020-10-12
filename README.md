# brick-mosaic
This is a simple tool for converting images to Lego mosaics such that their parts can be ordered quite easily from bricklink (https://www.bricklink.com/).
I wrote this for myself for a birthday present I worked on, but wanted to leave it here for others to re-use or as inspiration. :)

![process-steps](material/process-steps.svg)

(ltr: original image, pixelated image with original color, image with colors mapped to given Lego colors)

# Quickstart

## Prerequisites

- Python (I used python 3.8)
  - opencv-python (the version I used is defined in requirements.txt)

## Process an image

Convert an image by invoking the script as follows:

`python mosaic/brickify.py data/iron-man-portrait.jpg --output_directory="temp"`
