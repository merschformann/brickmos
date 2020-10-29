# brick-mosaic
This is a simple tool for converting images to Lego mosaics such that their parts can be ordered quite easily from bricklink (https://www.bricklink.com/).
I wrote this for myself for a birthday present I worked on, but wanted to leave it here for others to re-use or as inspiration. :)

![process-steps](material/process-steps.svg)

(ltr: original image, pixelated image with original color, image with colors mapped to given Lego colors)

# Quickstart

## Prerequisites

- Python (I used python 3.8)
  - opencv-python (the version I used is defined in _requirements.txt_)

## Process an image

Convert an image by invoking the script as follows:

`python mosaic/brickify.py data/iron-man-portrait.jpg --output_directory="temp"`

## Parameters

Find a short explanation of the parameter arguments below.

#### Required arguments
- image_file: the path to the (original) image to process, can be a _.jpg_ or _.png_ file

#### Optional arguments
- color_file: the csv-file defining the brick-colors to be used (if not given, colors.csv at script location is attempted), see format description below
- output_directory: the directory the output image and BOM is written to (default is current working directory)
- spares: the number of spares to add per color/brick (in bricklink BOM), just in case of loosing some bricks

## Color definition

The set of available colors is defined by the csv-file (`color_file`, see above). The following information is required.

```
rgb         ; Bricklink Color Name ; Bricklink Color ID ; Bricklink Part ID
255,255,255 ; White                ; 1                  ; 3024
175,181,199 ; LightBluishGray      ; 86                 ; 3024
89,93,96    ; DarkBluishGray       ; 85                 ; 3024
33,33,33    ; Black                ; 11                 ; 3024
```

This is an example set of colors for a 4 'color' black & white picture using 1x1 plates.
The example is already in expected format. The format requires a header line and semicolons as column delimiters.
The values used here should be aligned with the definitions on bricklink for the export to work properly (see [https://www.bricklink.com/catalogColors.asp](https://www.bricklink.com/catalogColors.asp)).

More details about each column:
- The first column is the RGB value of the corresponding color. There is no official definition of these from Lego, thus, use something as close as possible you can find. I picked the colors defined on the bricklink page.
- The second column is just a recognizable name for the color. Using the bricklink name seems reasonable.
- The third column is the bricklink color ID (see page mentioned before). This is important for the XML-export to function properly.
- The fourth column is the bricklink brick type ID. You can find these in bricklinks database. Since the script only considers 1x1 parts, only these should be used. The _3024_ from the example is the 1x1 plate (see [here](https://www.bricklink.com/v2/catalog/catalogitem.page?P=3024#T=C)). Other possible options include, but are not limited to, 1x1 tiles (3070b, see [here](https://www.bricklink.com/v2/catalog/catalogitem.page?P=3070b#T=C)) or 1x1 plate round (4073, see [here](https://www.bricklink.com/v2/catalog/catalogitem.page?P=4073#T=C)). Note that prices vary *a lot* with color **AND** brick type. For my own mosaic I used 1x1 plates, but replaced an expensive color with a much cheaper 1x1 tile. 
