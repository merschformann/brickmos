from . import defaults
import argparse
import csv
import cv2
import math
import os
import sys
from typing import Tuple, List
import xml.etree.cElementTree as xmlET


# ===> Constants

NO_GRID = "none"  # Argument value for deactivating the helper grid


# ===> Auxiliary classes


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


# ===> Argument handling


def init_and_get_arguments():
    """
    Creates an argument parser, handles it and returns the prepared arguments.
    :return: The arguments.
    """
    parser = argparse.ArgumentParser(
        description="brick-mosaic: 'Mosaicify' an image using brick colors and export bill of material"
    )
    parser.add_argument(
        "--image_file",
        "-i",
        required=True,
        type=str,
        help="the image to process",
    )
    parser.add_argument(
        "--color_file",
        type=str,
        default="",
        help="the csv-file defining the brick-colors to be used (if not given, colors.csv at script "
        "location is attempted)",
    )
    parser.add_argument(
        "--output_directory",
        "-o",
        type=str,
        default=".",
        help="the directory the output image and BOM is written to (default is current working dir)",
    )
    parser.add_argument(
        "--spares",
        type=int,
        default=0,
        help="the number of spares to add per color/brick (bricklink), just in case of loosing some bricks",
    )
    parser.add_argument(
        "--size",
        type=str,
        default="48x48",
        help="the size of the mosaic (default is 48x48 bricks)",
    )
    parser.add_argument(
        "--grid_cell",
        type=str,
        default="8x8",
        help=f"the size of a helper grid cell (default is 8x8 bricks, '{NO_GRID}' removes the grid)",
    )
    parser.add_argument(
        "--no_preview",
        dest="no_preview",
        action="store_true",
        default=False,
        help="indicates whether to skip immediately showing the images",
    )
    # Retrieve arguments
    args = parser.parse_args()
    # Use default color definition location, if not given
    if args.color_file != "" and not os.path.exists(args.color_file):
        print(f"No color definition file found at {args.color_file}, exiting ...")
        sys.exit(-1)
    # Quick check for image file presence
    if not os.path.exists(args.image_file):
        print(f"Cannot find image file at {args.image_file}, exiting ...")
        sys.exit(-2)
    # Get image size
    try:
        width, height = [int(a) for a in args.size.split("x")]
        args.width = width
        args.height = height
    except Exception:
        print(
            f"Cannot parse --size argument. Got {args.size}, but wanted something like 48x48"
        )
        sys.exit(-3)
    # Get helper grid cell size
    if args.grid_cell != NO_GRID:
        try:
            width, height = [int(a) for a in args.grid_cell.split("x")]
            args.grid_cell_width = width
            args.grid_cell_height = height
        except Exception:
            print(
                f"Cannot parse --grid_cell argument. Got {args.grid_cell}, but wanted something like 8x8"
            )
            sys.exit(-4)
    # Get helper grid size
    # Create output directory, if it does not exist
    os.makedirs(args.output_directory, exist_ok=True)
    return args


# ===> Functionality


def read_colors(color_csv: str) -> List[BrickColor]:
    """
    Reads the color CSV and returns the color definitions.
    Expected CSV-format (with header, integer RGB): red,green,blue;color-name,bricklink-color-id,bricklink-brick-type
    :param color_csv: The CSV content as a string.
    :return: All color definitions read from the file.
    """
    colors_read = []
    csv_reader = csv.reader(color_csv.splitlines(), delimiter=";")
    next(csv_reader)
    for row in csv_reader:
        colors_read.append(
            BrickColor(
                tuple([int(i) for i in row[0].split(sep=",")]),
                row[1].strip(),
                row[2].strip(),
                row[3].strip(),
            )
        )
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


def add_grid(img, pixels, spacing):
    line_frac = 0.002
    line_width = int(round(min(line_frac * img.shape[0], line_frac * img.shape[1])))
    for i in range(pixels[0] + 1):
        if i % spacing[0] == 0:
            x = int(round(float(i) / pixels[0] * img.shape[0]))
            cv2.line(img, (x, 0), (x, img.shape[0]), (0, 0, 0), line_width)
    for i in range(pixels[1] + 1):
        if i % spacing[1] == 0:
            y = int(round(float(i) / pixels[1] * img.shape[1]))
            cv2.line(img, (0, y), (img.shape[0], y), (0, 0, 0), line_width)


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


def main():
    # Get arguments
    args = init_and_get_arguments()

    # Read color info - find colors here: https://www.bricklink.com/catalogColors.asp
    color_info = ""
    if args.color_file == "":
        color_info = defaults.get_default_colors()
    else:
        with open(args.color_file, "r") as f:
            color_info = f.read()
    colors = read_colors(color_info)

    # Input image
    image_input = cv2.imread(args.image_file)

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
    image_output = cv2.resize(
        image_bricks, (w_out, h_out), interpolation=cv2.INTER_NEAREST
    )

    # Add helper grid
    grid_spacing = args.grid_cell_width, args.grid_cell_height
    if args.grid_cell != NO_GRID:
        add_grid(image_output, (w, h), grid_spacing)

    # Show some statistics
    print(
        f"Colors ({len(statistics)} colors, {sum([i.count for i in statistics.values()])} tiles):"
    )
    for item in sorted(statistics.items(), key=lambda x: -x[1].count):
        print(f"{item[0].colorName}: {item[1].count}")

    # Output bricklink xml
    write_xml(os.path.join(args.output_directory, "bricklink.xml"), statistics)

    # Prepare pixelated image for analysis (just resize it)
    image_input = cv2.resize(
        image_input, (w_out, h_out), interpolation=cv2.INTER_NEAREST
    )
    image_pixelated = cv2.resize(
        image_pixelated, (w_out, h_out), interpolation=cv2.INTER_NEAREST
    )

    # Write images
    cv2.imwrite(os.path.join(args.output_directory, "1.input.jpg"), image_input)
    cv2.imwrite(os.path.join(args.output_directory, "2.pixelated.jpg"), image_pixelated)
    cv2.imwrite(os.path.join(args.output_directory, "3.output.jpg"), image_output)

    # Show images
    if not args.no_preview:
        cv2.imshow("Input", image_input)
        cv2.imshow("Pixelated", image_pixelated)
        cv2.imshow("Output", image_output)
        # Wait for user to quit
        cv2.waitKey(0)


if __name__ == "__main__":
    main()
