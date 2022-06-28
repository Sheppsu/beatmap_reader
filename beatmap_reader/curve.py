from .enums import CurveType
from typing import Sequence, Union
import math
import numpy as np


class Point:
    def __init__(self, x: int, y: int, anchor_points: bool = False):
        self.x = x
        self.y = y
        self.anchor_point = anchor_points

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.anchor_point == other.anchor_point

    def __str__(self):
        return f"({self.x}, {self.y})"


class Points:
    def __init__(self, points: list[Point]):
        offset = 0
        for i in range(len(points)-1):
            if i+offset+1 >= len(points):
                break
            if points[i+offset] == points[i+offset+1]:
                points[i+offset].anchor_point = True
                offset += 1
                points.pop(i+offset)
        self.points = points

    def split(self):
        points = [[]]
        for point in self.points:
            points[-1].append(point)
            if point.anchor_point:
                points.append([point])
        return points

    def __iter__(self):
        return iter(self.points)

    @classmethod
    def from_string(cls, strings: Sequence[str]):
        return cls(
            list(map(
                lambda string: Point(*tuple(map(
                    int, string.split(":")
                ))),
                strings
            )))


class CurveBase:
    def __init__(self, points, parent):
        self.points = points
        self.parent = parent
        self.curve_points_cache = None

    def _create_curve_functions(self):
        raise NotImplementedError()

    def _get_t_points(self):
        raise NotImplementedError()

    @property
    def curve_points(self):
        if self.curve_points_cache is not None:
            return self.curve_points_cache
        curve_function = self._create_curve_functions()
        t_points = self._get_t_points()
        self.curve_points_cache = (list(map(curve_function[0], t_points[0])), list(map(curve_function[1], t_points[1])))
        return self.curve_points_cache


class Bezier(CurveBase):
    type = CurveType.BEZIER

    def __init__(self, points, parent):
        super().__init__(points, parent)


class PerfectCircle(CurveBase):
    type = CurveType.PERFECT

    def __init__(self, points, parent):
        super().__init__(points, parent)

        self.radius1 = None
        self.radius2 = None

    def _get_t_points(self):
        if self.radius1 is None or self.radius2 is None:
            return
        return np.linspace(0, 1, math.ceil(math.pi*2*self.radius1)), \
               np.linspace(0, 1, math.ceil(math.pi*2*self.radius2))

    def _create_curve_functions(self):
        p0, p1, p2 = self.points
        print(p0, p1, p2)
        y = (p1.x**2 + p1.y**2 - p0.x**2 - p0.y**2) / \
            (2*(-(p2.y - p1.y)*(p1.x - p0.x)/(p2.x-p1.x) + p1.y - p0.y)) - \
            (p1.x - p0.x)*(p2.x**2 + p2.y**2 - p1.x**2 - p1.y**2) / \
            (2*(p2.x-p1.x)*(-(p2.y-p1.y)*(p1.x-p0.x)/(p2.x-p1.x)+p1.y-p0.y))
        x = (p2.x**2 + p2.y**2 - p1.x**2 - p1.y**2) / \
            (2*(p2.x-p1.x)) - \
            (p2.y - p1.y)*y / (p2.x - p1.x)
        m_point = Point(x, y)
        radius = math.sqrt((m_point.x-p0.x)**2 + (m_point.y - p0.y)**2)
        radius_offset = (54.4 - 4.48 * self.parent.parent.difficulty.circle_size) / 2
        self.radius1, self.radius2 = radius - radius_offset, radius + radius_offset
        circle = (
            lambda r: (
                lambda t: (
                    (r*math.cos((1-t)*2*math.pi) + m_point.x),
                    (r*math.sin((1-t)*2*math.pi) + m_point.y)
                )
            )
        )
        return circle(self.radius1), circle(self.radius2)


class Linear(CurveBase):
    type = CurveType.LINEAR

    def __init__(self, points, parent):
        super().__init__(points, parent)


class CatMull(CurveBase):
    type = CurveType.CATMULL

    def __init__(self, points, parent):
        super().__init__(points, parent)


class Curve:
    def __new__(cls, curve_data, parent) -> Union[Bezier, PerfectCircle, Linear, CatMull]:
        curve_data = curve_data.split("|")
        type = curve_data[0].upper()
        points = Points.from_string(curve_data[1:])
        points.points.insert(0, Point(parent.x, parent.y))
        return {
            "B": Bezier,
            "P": PerfectCircle,
            "L": Linear,
            "C": CatMull,
        }[type](points, parent)
