from .enums import HitObjectType, TimingPointType, SliderEventType
from .path import Vector2, SliderPath
from .util import difficulty_range, clamp
from numpy import arange
from collections import namedtuple


def get_hit_object(parent, data, index):
    data = data.split(",")
    x, y = float(data[0]), float(data[1])
    time = int(data[2])
    type = int(data[3])
    new_combo = bool(type & (1 << 2))
    combo_colour_skip = 0 if not new_combo else type & 0b01110000
    hit_sound = int(data[4]) if data[4] else None  # Got an error where the hit sound was missing :shrug:
    params = data[5:]
    hit_sample = params.pop(-1) if params and ":" in params[-1] else None
    if type & (1 << 0):
        return HitCircle(params, parent, x, y, time, new_combo, combo_colour_skip,
                         hit_sound, hit_sample, index)
    elif type & (1 << 1):
        return Slider(params, parent, x, y, time, new_combo, combo_colour_skip,
                      hit_sound, hit_sample, index)
    elif type & (1 << 3):
        return Spinner(params, parent, x, y, time, new_combo, combo_colour_skip,
                       hit_sound, hit_sample, index)
    elif type & (1 << 7):
        return ManiaHoldKey(params, parent, x, y, time, new_combo, combo_colour_skip,
                            hit_sound, hit_sample, index)
    else:
        raise ValueError("Hit object does not have a valid type specified.")


class HitObjectBase:
    OBJECT_RADIUS = 64
    PREEMPT_MIN = 450
    BASE_SCORING_DISTANCE = 100

    def __init__(self, parent, x, y, time, new_combo, combo_colour_skip,
                 hit_sound, hit_sample, index):
        self.parent = parent
        self.x = x
        self.y = y
        self.position = Vector2(x, y)
        self.end_position = self.position
        self.time = time
        self.end_time = time
        self.new_combo = new_combo
        self.combo_colour_skip = combo_colour_skip
        self.hit_sound = hit_sound
        self.hit_sample = hit_sample
        self.index = index

        self.ui_timing_point = None
        self.i_timing_point = None
        self.time_preempt = difficulty_range(parent.difficulty.approach_rate, 1800, 1200, self.PREEMPT_MIN)
        self.time_fade_in = 400 * min(1, self.time_preempt / self.PREEMPT_MIN)
        self.scale = (1.0 - 0.7 * (parent.difficulty.circle_size - 5) / 5) / 2
        self.radius = self.OBJECT_RADIUS * self.scale
        self.stack_height = None
        self.stack_offset = None
        self.stacked_position = None
        self.stacked_end_position = None
        self._set_stack_height(0)

    def on_difficulty_change(self):
        # Recalculate attributes that are based on a map's difficulty values
        self.time_preempt = difficulty_range(self.parent.difficulty.approach_rate, 1800, 1200, self.PREEMPT_MIN)
        self.time_fade_in = 400 * min(1, self.time_preempt / self.PREEMPT_MIN)
        self.scale = (1.0 - 0.7 * (self.parent.difficulty.circle_size - 5) / 5) / 2
        self.radius = self.OBJECT_RADIUS * self.scale
        self._set_stack_height(self.stack_height)

    def _set_stack_height(self, stack_height):
        super().__setattr__("stack_height", stack_height)
        self.stack_offset = stack_height * self.scale * -6.4
        self.stacked_position = self.position + self.stack_offset
        if self.end_position is not None:
            self.stacked_end_position = self.end_position + self.stack_offset

    def __setattr__(self, key, value):
        is_updating = hasattr(self, key)
        if key == "stack_height" and is_updating:
            self._set_stack_height(value)
        else:
            super().__setattr__(key, value)
        if key == "end_position" and hasattr(self, "stack_height"):
            self._set_stack_height(self.stack_height)


class HitCircle(HitObjectBase):
    type = HitObjectType.HITCIRCLE

    def __init__(self, params, parent, *args):
        super().__init__(parent, *args)


SliderObject = namedtuple("SliderObject", ["position", "stacked_position", "time", "type"])


class Slider(HitObjectBase):
    type = HitObjectType.SLIDER

    TICK_DISTANCE_MULTIPLIER = 1
    LEGACY_LAST_TICK_OFFSET = 36

    def __init__(self, params, parent, *args):
        super().__init__(parent, *args)
        self.nested_objects = []
        self.slides = int(params[1])
        self.length = float(params[2])
        # TODO: yeppers
        self.edge_sounds = params[3] if len(params) > 3 else None
        self.edge_sets = params[4] if len(params) > 4 else None
        self.path = SliderPath(params[0], self)

        self.velocity = None
        self.tick_distance = None
        self.end_time = None
        self.span_duration = None
        self.nested_objects = []
        self.end_position = None
        self.tail_circle = None

        # Lazy attributes are for osu difficulty calculation
        self.lazy_end_position = None
        self.lazy_travel_distance = 0
        self.lazy_travel_time = 0

    def on_difficulty_change(self):
        super().on_difficulty_change()
        self.create_nested_objects()

    def calculate_time_attributes(self):
        scoring_distance = self.BASE_SCORING_DISTANCE * self.parent.difficulty.slider_multiplier * \
                           (self.i_timing_point.slider_velocity if self.i_timing_point is not None else 1)
        self.velocity = scoring_distance / self.ui_timing_point.beat_duration
        self.tick_distance = scoring_distance / self.parent.difficulty.slider_tick_rate * \
            self.TICK_DISTANCE_MULTIPLIER
        self.end_time = self.time + self.slides * self.length / self.velocity
        self.span_duration = (self.end_time - self.time) / self.slides

    def calculate_path(self):
        self.path.calculate()
        self.end_position = self.position_at_path_progress(1)
        if self.stack_offset:
            self.stacked_end_position = self.end_position + self.stack_offset

    def create_nested_objects(self):
        """
        To be run after stacking has been applied when hit objects are being loaded.
        """
        self.nested_objects = []
        events = SliderEventGenerator.generate(self.time, self.span_duration, self.velocity, self.tick_distance,
                                               self.path.calculated_distance, self.slides, self.LEGACY_LAST_TICK_OFFSET)

        for event in events:
            if event.type == SliderEventType.TICK:
                position = self.position_at_path_progress(event.path_progress, stacked=False)
                self.nested_objects.append(SliderObject(position, position+self.stack_offset, event.time,
                                                        SliderEventType.TICK))
            elif event.type == SliderEventType.HEAD:
                self.nested_objects.append(SliderObject(self.position, self.stacked_position, event.time,
                                                        SliderEventType.HEAD))
            elif event.type == SliderEventType.LEGACY_LAST_TICK:
                pos = self.position_at_path_progress(event.path_progress)
                self.nested_objects.append(SliderObject(pos, pos+self.stack_offset, event.time,
                                                        SliderEventType.LEGACY_LAST_TICK))
            elif event.type == SliderEventType.REPEAT:
                position = self.position_at_path_progress(event.path_progress, stacked=False)
                self.nested_objects.append(SliderObject(position, position+self.stack_offset,
                                                        self.time + (event.span_index + 1) * self.span_duration,
                                                        SliderEventType.REPEAT))
            elif event.type == SliderEventType.TAIL:
                position = self.position_at_path_progress(event.path_progress, stacked=False)
                self.tail_circle = SliderObject(position, position+self.stack_offset, event.time,
                                                SliderEventType.TAIL)

    def curve_progress_at(self, progress):
        # slides = self.slides if progress != 1 else self.slides + 1
        curve_progress = progress * self.slides % 1
        if (progress * self.slides // 1) % 2 == 1:
            curve_progress = 1 - curve_progress
        return curve_progress

    def position_at_path_progress(self, progress, stacked=True, pri=False):
        point = self.path.position_at(progress, pri)
        if stacked:
            point += self.stack_offset
        return point

    def position_at_slider_progress(self, progress, stacked=True):
        return self.position_at_path_progress(self.curve_progress_at(progress), stacked)

    def position_at_offset(self, offset, stacked=True):
        if self.time == self.end_time:  # edge case
            return self.position_at_slider_progress(1, stacked)
        return self.position_at_slider_progress((offset - self.time) / (self.end_time - self.time), stacked)


class Spinner(HitObjectBase):
    type = HitObjectType.SPINNER

    def __init__(self, params, parent, *args):
        super().__init__(parent, *args)
        self.end_time = int(params[0])
        self.x = 256
        self.y = 192
        self.position = Vector2(self.x, self.y)


class ManiaHoldKey(HitObjectBase):
    type = HitObjectType.MANIA_HOLD_KEY

    def __init__(self, params, parent, *args):
        super().__init__(parent, *args)
        self.end_time = int(self.hit_sample.split(":")[0])
        self.hit_sample = self.hit_sample[len(str(self.end_time))+1:]

    def get_column(self, total_columns):
        return self.x * total_columns // 512


SliderEvent = namedtuple("SliderEvent", ("type", "span_index", "span_start_time",
                                         "time", "path_progress"))


class SliderEventGenerator:
    @staticmethod
    def generate(start_time, span_duration, velocity, tick_distance,
                 total_distance, span_count, legacy_last_tick_offset):
        events = []

        max_length = 100000

        length = min(max_length, total_distance)
        tick_distance = clamp(tick_distance, 0, length)

        min_distance_from_end = velocity * 10

        events.append(SliderEvent(SliderEventType.HEAD, 0, start_time, start_time, 0))

        if tick_distance != 0:
            for span in range(span_count):
                span_start_time = start_time + span * span_duration
                is_reversed = span % 2 == 1

                ticks = SliderEventGenerator.generate_ticks(span, span_start_time, span_duration, is_reversed,
                                                            length, tick_distance, min_distance_from_end)
                if is_reversed:
                    ticks = reversed(ticks)

                events += ticks

                if span < span_count - 1:
                    events.append(SliderEvent(SliderEventType.REPEAT, span, start_time + span * span_duration,
                                              span_start_time + span_duration, (span + 1) % 2))

        total_duration = span_count * span_duration

        final_span_index = span_count - 1
        final_span_start_time = start_time + final_span_index * span_duration
        final_span_end_time = max(start_time + total_duration / 2, (final_span_start_time + span_duration) -
                                  (legacy_last_tick_offset if legacy_last_tick_offset else 0))
        final_progress = (final_span_end_time - final_span_start_time) / span_duration if span_duration > 0 else 1

        if span_count % 2 == 0:
            final_progress = 1 - final_progress

        events += [
            SliderEvent(SliderEventType.LEGACY_LAST_TICK, final_span_index, final_span_start_time,
                        final_span_end_time, final_progress),
            SliderEvent(SliderEventType.TAIL, final_span_index, start_time + (span_count - 1) * span_duration,
                        start_time + total_duration, span_count % 2)
        ]

        return events

    @staticmethod
    def generate_ticks(span_index, span_start_time, span_duration, is_reversed, length,
                       tick_distance, min_distance_from_end):
        ticks = []
        d = 0
        while (d := d + tick_distance) <= length:
            if d >= length - min_distance_from_end:
                break

            path_progress = float(d / length)
            time_progress = 1 - path_progress if is_reversed else path_progress

            ticks.append(SliderEvent(SliderEventType.TICK, span_index, span_start_time,
                                     span_start_time + time_progress * span_duration, path_progress))
        return ticks
