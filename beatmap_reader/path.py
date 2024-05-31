from .enums import CurveType
try:
    from .sliderpath import (
        approximate_bezier,
        approximate_circular_arc,
        approximate_catmull,
        calculate_length
    )
except ModuleNotFoundError:
    print("WARNING: Could not import sliderpath.pyd")
from .util import clamp
import math
import numpy as np


class Vector2:
    __slots__ = ("x", "y")

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def magnitude(self):
        return math.sqrt(math.pow(self.x, 2) + math.pow(self.y, 2))

    def normalize(self):
        magnitude = self.magnitude()
        if magnitude == 0:
            return Vector2(0, 0)
        return self / magnitude

    def dot(self, v):
        return self.x * v.x + self.y * v.y

    def distance_to(self, v):
        return math.sqrt(math.pow(self.x-v.x, 2) + math.pow(self.y-v.y, 2))

    @staticmethod
    def _parse_other(other):
        return (other.x, other.y) if hasattr(other, "x") and hasattr(other, "y") else (other, other)

    def __eq__(self, other):
        return other.x == self.x and other.y == self.y

    def __add__(self, other):
        x, y = self._parse_other(other)
        return Vector2(self.x + x, self.y + y)

    def __sub__(self, other):
        x, y = self._parse_other(other)
        return Vector2(self.x - x, self.y - y)

    def __mul__(self, other):
        x, y = self._parse_other(other)
        return Vector2(self.x * x, self.y * y)

    def __truediv__(self, other):
        x, y = self._parse_other(other)
        return Vector2(self.x / x, self.y / y)

    def __round__(self, n=None):
        return Vector2(round(self.x, n), round(self.y, n))

    def __getitem__(self, item):
        return (self.x, self.y)[item]

    def __iter__(self):
        return iter([self.x, self.y])

    def __repr__(self):
        return f"<{self.x}, {self.y}>"


class Point:
    __slots__ = ("position", "anchor_point")

    def __init__(self, position, anchor_point=False):
        self.position = Vector2(*position)
        self.anchor_point = anchor_point

    def __eq__(self, other):
        return self.position == other.position

    def __repr__(self):
        return ("A" if self.anchor_point else "N")+f"{self.position!r}"


class Points(list):
    def __init__(self, points):
        for i in range(len(points)):
            if i + 1 >= len(points):
                break
            if points[i] == points[i + 1]:
                points[i].anchor_point = True
                points.pop(i + 1)
        super().__init__(points)

    def split(self):
        points = [[self[0]]]
        for point in self[1:]:
            points[-1].append(point)
            if point.anchor_point:
                points.append([point])
        if len(points[-1]) == 1:
            points.pop(-1)
        return points

    @classmethod
    def from_string(cls, strings):
        return cls(
            list(map(
                lambda string: Point(tuple(map(
                    float, string.split(":")
                ))),
                strings
            )))


def approximate_linear(points):
    return points


class SliderPath:
    __slots__ = (
        "points", "expected_distance", "type", "calculated_path",
        "cumulative_distance", "segmentEnds", "calculated", "parent"
    )

    def __init__(self, curve_data, parent):
        curve_data = curve_data.split("|")
        curve_data.insert(1, f"{parent.x}:{parent.y}")
        self.parent = parent
        self.points = Points.from_string(curve_data[1:])
        self.expected_distance = parent.length
        self.type = CurveType(["L", "P", "B", "C"].index(curve_data[0].upper()))

        self.calculated_path = []
        self.cumulative_distance = []
        self.segmentEnds = []
        self.calculated = False

    def calculate(self):
        self.calculate_path()
        self.calculate_length()
        self.calculated_path = np.array(self.calculated_path)
        self.cumulative_distance = np.array(self.cumulative_distance)
        self.segmentEnds = np.array(self.segmentEnds)
        self.calculated = True

    def calculate_subpath(self, segment):
        segment = self.get_primitive_points(segment)
        if self.type == CurveType.PERFECT and len(segment) != 3:
            calc_func = approximate_bezier
        else:
            calc_func = globals()[
                "approximate_" + ("linear", "circular_arc", "bezier", "catmull")[int(self.type)]]

        path = calc_func(segment)
        if len(path) == 0:
            return approximate_bezier(segment)
        return path

    def calculate_path(self):
        self.calculated_path = []
        self.segmentEnds = []

        if len(self.points) == 0:
            return

        start = 0
        for i in range(len(self.points)):
            if (not self.points[i].anchor_point and i != 0) and i < len(self.points)-1:
                continue
            segment = self.points[start:i + 1]

            for point in self.calculate_subpath(segment):
                if len(self.calculated_path) == 0 or not self.compare_points(self.calculated_path[-1], point):
                    self.calculated_path.append(point)

            self.segmentEnds.append(len(self.calculated_path) - 1)
            start = i

    def calculate_length(self):
        self.calculated_path, self.segmentEnds, self.cumulative_distance = \
            calculate_length(self.get_primitive_points(self.points), self.calculated_path,
                             self.segmentEnds, self.expected_distance)

    def get_approximate_distance_index(self, distance):
        low = 0
        high = len(self.cumulative_distance)-1
        i = high // 2
        while self.cumulative_distance[i] != distance and high >= low:
            if self.cumulative_distance[i] < distance:
                low = i+1
            else:
                high = i-1
            i = (high + low) // 2
        return i+1

    def position_at(self, progress, pri=False):
        if len(self.calculated_path) == 0: return Vector2(0, 0)
        distance = clamp(progress, 0, 1) * self.calculated_distance
        index = self.get_approximate_distance_index(distance)

        if pri: print(distance, index, self.calculated_path[index])

        if index <= 0: return Vector2(*self.calculated_path[0])
        if index >= len(self.calculated_path): return Vector2(*self.calculated_path[-1])

        p0 = Vector2(*self.calculated_path[index - 1])
        p1 = Vector2(*self.calculated_path[index])
        d0 = self.cumulative_distance[index - 1]
        d1 = self.cumulative_distance[index]

        try:
            w = (distance - d0) / (d1 - d0)
            p = p0 + (p1 - p0) * w
            return p
        except (ZeroDivisionError, RuntimeWarning):
            return p0

    @property
    def calculated_distance(self):
        return 0 if len(self.cumulative_distance) == 0 else self.cumulative_distance[-1]

    @staticmethod
    def compare_points(p1, p2):
        return round(p1[0], 5) == round(p2[0], 5) and round(p1[1], 5) == round(p2[1], 5)

    @staticmethod
    def get_primitive_points(points):
        return [(point.position.x, point.position.y) for point in points]
