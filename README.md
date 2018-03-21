# SVGCode
This python library lets you export your `svgwrite` figures to gcode.
This is great because it lets you both create visualizations and actual laser cutting instructions in one go,
rather than creating one or the other and then attempting to convert it.

## Features
You **need** to import `svgcode.monkeypatch` before you import `svgwrite`, to use svgcode functions:
```
import svgcode.monkeypatch
import svgwrite
```
This puts `get_gcode` functions into svgwrite objects.

You can fill `Polygon` and `Rect` objects:
```
dwg = svgwrite.Drawing("test.svg", size=("6mm", "2mm"), viewBox=('0 0 28 12'))
dwg.add(dwg.rect((5, 0), (1, 1)).stroke("none").fill("black"))
dwg.save()
gcode = dwg.get_gcode(beam_size=1).tostring()
```
After which the svg will be saved, and you have the actual gcode in the `gcode` variable.

`line`, `polyline` and `path` objects are only "stroked".
Note that for `path`, only a single segment works for now.

## Installation
You need to have Python 3.6 or later and `svgwrite` and `numpy` installed. Then,

+ Clone or download this repository
+ Execute `python3 setup.py install` inside the downoaded directory (you may need to do this as root/adminstrator)
