from svgcode.gcode import GCodeG1, GCodeCollection
import numpy as np
import svgwrite.shapes
import svgwrite.base
import svgwrite.path
from math import sqrt


def base_get_gcode(self, beam_size=0.1, F=None, S=None):
    lines = GCodeCollection()
    for element in self.elements:
        if hasattr(element, "get_gcode"):
            lines.extend(element.get_gcode(beam_size=beam_size, F=F, S=S))
    return lines


svgwrite.base.BaseElement.get_gcode = base_get_gcode


def _shorten_line(points, beam_size=0.1):
    """Modifies points in-place to shorten the ends by beam_size/2."""
    v1 = points[0, :] - points[1, :]
    L = np.linalg.norm(v1)
    points[0, :] = points[1, :] + v1 * (L - beam_size / 2) / L
    v2 = points[-1, :] - points[-2, :]
    L = np.linalg.norm(v2)
    points[-1] = points[-2, :] + v2 * (L - beam_size / 2) / L
    return points


def line_get_gcode(self, beam_size=0.1, F=None, S=None):
    points = np.array([
        (self["x1"], self["y1"]), (self["x2"], self["y2"])
    ])
    _shorten_line(points, beam_size=beam_size)
    return GCodeCollection([GCodeG1(*points, S=S, F=F)])


svgwrite.shapes.Line.get_gcode = line_get_gcode


def polyline_get_gcode(self, beam_size=0.1, F=None, S=None):
    points = self.points.copy()
    _shorten_line(points, beam_size=beam_size)
    return GCodeCollection([GCodeG1(*points, F=F, S=S)])


svgwrite.shapes.Polyline.get_gcode = polyline_get_gcode


def rect_get_gcode(self, beam_size=0.1, F=None, S=None):
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
    # print(f"The division gave {nlines} lines and {extra} extra")
    if abs(float(extra)) > 1e-5:
        nlines += 1
    spacing = size[0] / nlines
    lines = GCodeCollection()
    for i in range(nlines):
        x = UL[0] + spacing / 2 + i * spacing
        y1 = UL[1] + spacing / 2
        y2 = UL[1] + size[1] - spacing / 2
        lines.append(GCodeG1(r(x, y1), r(x, y2), S=S, F=F))
    return lines


svgwrite.shapes.Rect.get_gcode = rect_get_gcode


def polygon_get_gcode(self, beam_size=0.1, F=None, S=None):
    """Stripe a Polygon. Striping is in the direction that the polygon is 'stretched'."""
    points = np.array(self.points)
    edges = points - np.roll(points, 1, axis=0)
    # edge_lengths = np.linalg.norm(edges, axis=1)
    edge_cov = np.cov(edges, rowvar=False)
    eig, eigv = np.linalg.eigh(edge_cov)
    # primary_direction = eigv[:, 1]  # Striping direction
    # secondary_direction = eigv[:, 0]
    points_b = np.linalg.inv(eigv).dot(points.T).T
    edges_b = points_b - np.roll(points_b, 1, axis=0)
    edges_b /= np.linalg.norm(edges_b, axis=1)[:, np.newaxis]  # Normalize the edges (used in margin)
    min_x = np.min(points_b[:, 0]) + beam_size/2
    max_x = np.max(points_b[:, 0]) - beam_size/2
    linepoints = []
    stripepoints = []
    isect = 0
    for x_value in np.arange(min_x, max_x + beam_size*0.1, beam_size):
        # Find intersections on this stripe
        for edge, p1, p2 in zip(edges_b, np.roll(points_b, 1, axis=0), points_b):
            if ((x_value <= p1[0] and x_value > p2[0]) or (x_value <= p2[0] and x_value > p1[0])):
                yv = edge[1]/edge[0] * (x_value - p1[0]) + p1[1]
                stripepoints.append([yv, edge])
                isect += 1

        # Ensure we found an even number of intersections
        if isect % 2:
            raise Exception("There ought to be an even number of intersections in each stripe....")

        # Sort the intersections -- ie. they enter, leave, enter, leave, ...
        stripepoints.sort(key=lambda i: i[0])

        # Add margin perpendicularly to edge
        for i, val in enumerate(stripepoints):
            val[0] -= (2*(i%2)-1) * beam_size / 2 / sqrt(1-val[1][1]**2)
        linepoints.extend([[x_value, yv] for yv, e in stripepoints])

    # Transform back
    linepoints = np.array(linepoints)
    linepoints = eigv.dot(linepoints.T).T

    # Make gcode commands
    cmds = GCodeCollection()
    for i in range(0, len(linepoints), 2):
        cmds.append(GCodeG1(linepoints[i], linepoints[i + 1], S=S, F=F))
    return cmds


svgwrite.shapes.Polygon.get_gcode = polygon_get_gcode


def path_get_gcode(self, beam_size=0.1, F=None, S=None):
    """Only supports paths that are essentially polylines."""
    lines = GCodeCollection()
    i = 0
    cur_points = None
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

    lines.append(GCodeG1(*cur_points, F=F, S=S))
    return lines


svgwrite.path.Path.get_gcode = path_get_gcode
