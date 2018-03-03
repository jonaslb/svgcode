from svgcode.gcode import GCodeG1, GCodeCollection
import numpy as np
import svgwrite.shapes
import svgwrite.base
import svgwrite.path


def base_get_gcode(self, beam_size=0.1):
    lines = GCodeCollection()
    for element in self.elements:
        if hasattr(element, "get_gcode"):
            lines.extend(element.get_gcode())
    return lines


svgwrite.base.BaseElement.get_gcode = base_get_gcode


def line_get_gcode(self, beam_size=0.1):
    # TODO: Shorten by beam_size
    return GCodeCollection([GCodeG1((self["x1"], self["y1"]), (self["x2"], self["y2"]))])


svgwrite.shapes.Line.get_gcode = line_get_gcode


def polyline_get_gcode(self, beam_size=0.1):
    # TODO: Shorten by beam_size
    return GCodeCollection([GCodeG1(*self.points)])


svgwrite.shapes.Polyline.get_gcode = polyline_get_gcode


def rect_get_gcode(self, beam_size=0.1):
    UL = np.array([self["x"], self["y"]])
    size = np.array([self["width"], self["height"]])
    rot = size[0] > size[1]
    if rot:
        UL = np.flipud(UL)
        size = np.flipud(size)
    def r(x, y):
        if rot:
            return y, x
        return x, y
    nlines, extra = divmod(size[0], beam_size)
    nlines = int(nlines)
    if extra > 0:
        nlines += 1
    spacing = size[0] / nlines
    lines = GCodeCollection()
    print(nlines)
    print(type(nlines))
    for i in range(nlines):
        x = beam_size / 2 + i * spacing
        y1 = UL[1] + spacing / 2
        y2 = UL[1] + size[1] - spacing / 2
        lines.append(GCodeG1(r(x, y1), r(x, y2)))
    return lines


svgwrite.shapes.Rect.get_gcode = rect_get_gcode


def path_get_gcode(self, beam_size=0.1):
    """Only supports paths that are essentially polylines."""
    lines = GCodeCollection()
    i = 0
    cur_points = None
    print(self.commands)
    while True:
        if i >= len(self.commands):
            break
        c = self.commands[i]
        if c is None:
            i += 1
        elif c == "M":
            if cur_points is not None:
                raise NotImplementedError("Only one line per path.. for now")
            cur_points = [self.commands[i+1:i+3]]
            i += 3
        elif c == "L":
            if cur_points is None:
                raise Exception("Shouldn't happen")
            cur_points += [self.commands[i+1:i+3]]
            i += 3
        elif c == "l":
            if cur_points is None:
                raise Exception("Nope")
            p = self.commands[i+1:i+3]
            p[0] += cur_points[-1][0]
            p[1] += cur_points[-1][1]
            cur_points += [p]
            i += 3
        else:
            raise NotImplementedError(f"This is an extemely superficial implementation. '{c}' not impemented")
    lines.append(GCodeG1(*cur_points))
    return lines


svgwrite.path.Path.get_gcode = path_get_gcode
