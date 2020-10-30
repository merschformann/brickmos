import argparse
import csv
import cv2
import math
import os
import sys
from typing import Tuple
import xml.etree.cElementTree as xmlET


class BrickColor:
    """
    Defines a brick color with all information needed for processing and bricklink export.
    """

    def __init__(self, rgb, color_name, color_id, color_type):
        self.rgb = rgb
        self.colorName = color_name
        self.colorId = color_id
        self.colorType = color_type

    def __str__(self):
        return f"{self.rgb} / {self.colorName} / {self.colorId} / {self.colorType}"


class BrickColorStats:
    """
    Tracks some stats for the corresponding color.
    """

    def __init__(self, brick_color):
        self.brickColor = brick_color
        self.count = 0


def init_and_get_arguments():
    """
    Creates an argument parser, handles it and returns the prepared arguments.
    :return: The arguments.
    """
    parser = argparse.ArgumentParser(description="'Mosaicify' an image using brick colors and export bill of material")
    parser.add_argument('image_file', type=str, help='the image to process')
    parser.add_argument('--color_file', type=str, default='',
                        help='the csv-file defining the brick-colors to be used (if not given, colors.csv at script '
                             'location is attempted)')
    parser.add_argument('--output_directory', type=str, default='.',
                        help='the directory the output image and BOM is written to (default is current working dir)')
    parser.add_argument('--spares', type=int, default=0,
                        help='the number of spares to add per color/brick (bricklink), just in case of loosing some bricks')
    parser.add_argument('--width', type=int, default=48,
                        help='the width of the mosaic (default is 48)')
    parser.add_argument('--height', type=int, default=48,
                        help='the height of the mosaic (default is 48)')
    # Retrieve arguments
    args = parser.parse_args()
    # Use default color definition location, if not given
    default_color_file = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'colors.csv')
    if args.color_file == '':
        if not os.path.exists(default_color_file):
            print('No color definitions found, exiting ...')
            sys.exit(-1)
        args.color_file = default_color_file
    # Quick check for image file presence
    if not os.path.exists(args.image_file):
        print(f'Cannot find image file at {args.image_file}, exiting ...')
        sys.exit(-2)
    # Create output directory, if it does not exist
    os.makedirs(args.output_directory, exist_ok=True)
    return args


def read_colors(color_file: str) -> []:
    """
    Reads the color file and returns the color definitions.
    Expected CSV-format (with header, integer RGB): red,green,blue;color-name,bricklink-color-id,bricklink-brick-type
    :param color_file: The path to the color file.
    :return: All color definitions read from the file.
    """
    colors_read = []
    with open(color_file) as color_def_file:
        csv_reader = csv.reader(color_def_file, delimiter=';')
        next(csv_reader)
        for row in csv_reader:
            colors_read.append(BrickColor(tuple([int(i) for i in row[0].split(sep=',')]),
                                          row[1].strip(), row[2].strip(), row[3].strip()))
    return colors_read


def closest_color(rgb: Tuple[int, int, int], color_range: list) -> BrickColor:
    """
    Returns the color from the range which is closest to the given one.
    :param rgb: The given color to fine the closest one for.
    :param color_range: The range of possible colors.
    :return: The color closest to the given one.
    """
    # Get rgb values of color while adhering to cv2 BGR representation
    r, g, b = rgb
    # Assess euclidean distance of color to all brick colors given
    color_diffs = []
    for color in color_range:
        cr, cg, cb = color.rgb
        color_diff = math.sqrt(abs(r - cr) ** 2 + abs(g - cg) ** 2 + abs(b - cb) ** 2)
        color_diffs.append((color_diff, color))
    # Get color closest to the given one and update its stats
    return min(color_diffs, key=lambda x: x[0])[1]


def replace_with_brick_colors(img, brick_colors):
    """
    Replaces all colors in the image with the closest brick colors given.
    :param img: The image to process.
    :return: The color statistics collected in the process.
    """
    # Replace with nearest colors from pallet
    stats = {}
    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            # Get and set nearest color for pixel
            closest = closest_color(img[i, j][::-1], brick_colors)
            img[i, j] = closest.rgb[::-1]
            # Update color stats
            if closest not in stats:
                stats[closest] = BrickColorStats(closest)
            stats[closest].count = stats[closest].count + 1
    return stats


def write_xml(filename, stats, spares_per_lot=5):
    """
    Writes the necessary colored bricks collected in stats to a bricklink xml file.
    :param filename: The file to write to.
    :param stats: The stats to export.
    :param spares_per_lot: The number of spares to add per color/brick, just in case of loosing some.
    """
    root = xmlET.Element("INVENTORY")
    for colorStat in stats.items():
        count = colorStat[1].count + spares_per_lot
        color_root = xmlET.SubElement(root, "ITEM")
        xmlET.SubElement(color_root, "ITEMTYPE").text = "P"
        xmlET.SubElement(color_root, "ITEMID").text = colorStat[0].colorType
        xmlET.SubElement(color_root, "COLOR").text = colorStat[0].colorId
        xmlET.SubElement(color_root, "MINQTY").text = str(count)
        xmlET.SubElement(color_root, "CONDITION").text = "X"
    tree = xmlET.ElementTree(root)
    tree.write(filename)


# ===> Main start
# Get arguments
args = init_and_get_arguments()

# Read color info - find colors here: https://www.bricklink.com/catalogColors.asp
colors = read_colors(args.color_file)

# Input image
image_input = cv2.imread(args.image_file)

# Get input size
height, width = image_input.shape[:2]
# Desired "pixelated" size
w, h = (args.width, args.height)
# Desired output size
w_out, h_out = (1000, 1000)

# Resize input to "pixelated" size
image_pixelated = cv2.resize(image_input, (w, h), interpolation=cv2.INTER_LINEAR)
image_bricks = image_pixelated.copy()

# Replace with brick colors
statistics = replace_with_brick_colors(image_bricks, colors)

# Initialize output image
image_output = cv2.resize(image_bricks, (w_out, h_out), interpolation=cv2.INTER_NEAREST)

# Show some statistics
print(f"Colors ({len(statistics)} colors, {sum([i.count for i in statistics.values()])} tiles):")
for item in sorted(statistics.items(), key=lambda x: -x[1].count):
    print(f"{item[0].colorName}: {item[1].count}")

# Output bricklink xml
write_xml(os.path.join(args.output_directory, 'bricklink.xml'), statistics)

# Prepare pixelated image for analysis (just resize it)
image_input = cv2.resize(image_input, (w_out, h_out), interpolation=cv2.INTER_NEAREST)
image_pixelated = cv2.resize(image_pixelated, (w_out, h_out), interpolation=cv2.INTER_NEAREST)

# Write images
cv2.imwrite(os.path.join(args.output_directory, '1.input.jpg'), image_input)
cv2.imwrite(os.path.join(args.output_directory, '2.pixelated.jpg'), image_pixelated)
cv2.imwrite(os.path.join(args.output_directory, '3.output.jpg'), image_output)

# Show images
cv2.imshow('Input', image_input)
cv2.imshow('Pixelated', image_pixelated)
cv2.imshow('Output', image_output)

# Wait for user to quit
cv2.waitKey(0)
