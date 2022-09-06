from .enums import HitObjectType, TimingPointType
from .curve import Curve, Point
from .util import difficulty_range
from collections import namedtuple
import pygame
import traceback


class HitObject:
    def __new__(cls, parent, data):
        # TODO: hit sound and hit sample objects
        data = data.split(",")
        x, y = int(data[0]), int(data[1])
        time = int(data[2])
        type = int(data[3])
        new_combo = bool(type & (1 << 2))
        combo_colour_skip = 0 if not new_combo else type & 0b01110000
        hit_sound = int(data[4]) if data[4] else None  # Got an error where the hit sound was missing :shrug:
        params = data[5:]
        hit_sample = params.pop(-1) if params and ":" in params[-1] else None
        if type & (1 << 0):
            return HitCircle(params, parent, x, y, time, new_combo, combo_colour_skip,
                             hit_sound, hit_sample)
        elif type & (1 << 1):
            return Slider(params, parent, x, y, time, new_combo, combo_colour_skip,
                          hit_sound, hit_sample)
        elif type & (1 << 3):
            return Spinner(params, parent, x, y, time, new_combo, combo_colour_skip,
                           hit_sound, hit_sample)
        elif type & (1 << 7):
            return ManiaHoldKey(params, parent, x, y, time, new_combo, combo_colour_skip,
                                hit_sound, hit_sample)
        else:
            raise ValueError("Hit object does not have a valid type specified.")


class HitObjectBase:
    OBJECT_RADIUS = 64
    PREEMPT_MIN = 450

    def __init__(self, parent, x, y, time, new_combo, combo_colour_skip,
                 hit_sound, hit_sample):
        self.parent = parent
        self.x = x
        self.y = y
        self.position = Point(x, y)
        self.end_position = self.position
        self.time = time
        self.end_time = time
        self.new_combo = new_combo
        self.combo_colour_skip = combo_colour_skip
        self.hit_sound = hit_sound
        self.hit_sample = hit_sample

        self.time_preempt = difficulty_range(parent.difficulty.approach_rate, 1800, 1200, self.PREEMPT_MIN)
        self.scale = (1.0 - 0.7 * (parent.difficulty.circle_size - 5) / 5) / 2
        self.radius = self.OBJECT_RADIUS * self.scale
        self.stack_height = None
        self.stack_offset = None
        self.stacked_position = None
        self.stacked_end_position = None
        self._set_stack_height(0)

    def _set_stack_height(self, stack_height):
        super().__setattr__("stack_height", stack_height)
        self.stack_offset = stack_height * self.scale * -6.4
        self.stacked_position = self.position + self.stack_offset
        self.stacked_end_position = self.end_position + self.stack_offset

    def __setattr__(self, key, value):
        is_updating = hasattr(self, key)
        if key == "stack_height" and is_updating:
            self._set_stack_height(value)
        else:
            super().__setattr__(key, value)
        if key == "end_position" and hasattr(self, "stack_height"):
            self._set_stack_height(self.stack_height)

    @property
    def start_time(self):
        return self.time


class HitCircle(HitObjectBase):
    type = HitObjectType.HITCIRCLE

    def __init__(self, params, parent, *args):
        super().__init__(parent, *args)


SliderObject = namedtuple("SliderObject", ["position", "stacked_position", "is_tick", "is_reverse"])


class Slider(HitObjectBase):
    type = HitObjectType.SLIDER

    def __init__(self, params, parent, *args):
        super().__init__(parent, *args)
        self.curve = Curve(params[0], self)
        self.nested_objects = []
        self.slides = int(params[1])
        self.length = float(params[2])
        # TODO: yeppers
        self.edge_sounds = params[3] if len(params) > 3 else None
        self.edge_sets = params[4] if len(params) > 4 else None

        # Calculate some slider attributes

        self.ui_timing_point = None
        self.i_timing_point = None
        self._set_timing_point_attributes()
        self.end_time = self._calculate_end_time()
        self.nested_objects = []
        self.span_duration = (self.end_time - self.time) / self.slides

        self.end_position = Point(*self.position_at_offset(self.end_time))
        self.lazy_end_position = None
        self.lazy_travel_distance = 0
        self.lazy_travel_time = 0
        self.surf = None

    def _set_timing_point_attributes(self):
        for timing_point in self.parent.timing_points:
            if timing_point.time <= self.time:
                if timing_point.type == TimingPointType.UNINHERITED:
                    self.ui_timing_point = timing_point
                else:
                    self.i_timing_point = timing_point
        if self.ui_timing_point is None:
            self.ui_timing_point = self.parent.timing_points[0]

    def _calculate_end_time(self):
        s_vel = self.i_timing_point.slider_velocity if self.i_timing_point is not None else 1
        return round(self.time + self.ui_timing_point.beat_duration * self.length * self.slides /
                     (self.parent.difficulty.slider_multiplier * s_vel * 100))

    def create_nested_objects(self):
        """
        To be run after stacking has been applied when hit objects are being loaded.
        """
        points = list(self.curve.curve_points)
        for s_i in range(self.slides):
            for i, point in enumerate(points):
                is_ticks = False  # TODO: implement
                is_reverse = True if i == len(points) - 1 and s_i < self.slides - 1 else False
                point = Point(point[0], point[1])
                stacked_point = point + self.stack_offset
                self.nested_objects.append(SliderObject(point, stacked_point, is_ticks, is_reverse))
            points.reverse()

    def render(self, screen_size, placement_offset, osu_pixel_multiplier=1, color=(0, 0, 0),
               border_color=(255, 255, 255), border_thickness=1):
        # TODO: some kind of auto coloring based on skin and beatmap combo colors etc.
        surf = pygame.Surface(screen_size)
        surf.set_colorkey((0, 0, 0))
        try:
            size = self.curve.radius_offset*osu_pixel_multiplier
            for c, r in ((border_color, size), (color, size-border_thickness)):
                for point in self.curve.curve_points:
                    pygame.draw.circle(surf, c, (point[0] * osu_pixel_multiplier + placement_offset[0],
                                                 point[1] * osu_pixel_multiplier + placement_offset[1]),
                                       r)
        except:
            print(f"Error occurred while rendering slider at {self.time} in {self.parent.path}.")
            traceback.print_exc()
        self.surf = surf

    def position_at(self, progress):
        return self.curve.curve_points[round(progress * (len(self.curve.curve_points) - 1))]

    def position_at_offset(self, offset):
        progress = round((offset - self.time) / (self.end_time - self.time)) * self.slides
        progress = progress - 2 * (progress // 2)
        if progress > 1:
            progress = 1 - progress
        return self.position_at(progress)


class Spinner(HitObjectBase):
    type = HitObjectType.SPINNER

    def __init__(self, params, parent, *args):
        super().__init__(parent, *args)
        self.end_time = int(params[0])
        self.x = 256
        self.y = 192
        self.position = Point(self.x, self.y)


class ManiaHoldKey(HitObjectBase):
    type = HitObjectType.MANIA_HOLD_KEY

    def __init__(self, params, parent, *args):
        super().__init__(parent, *args)
        self.end_time = int(self.hit_sample.split(":")[0])
        self.hit_sample = self.hit_sample[len(str(self.end_time))+1:]

    def get_column(self, total_columns):
        return self.x * total_columns // 512
