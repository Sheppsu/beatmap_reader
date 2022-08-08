from ..hit_object import DifficultyHitObject
from ...enums import HitObjectType
import math


class OsuDifficultyHitObject(DifficultyHitObject):
    normalized_radius = 50
    min_delta_time = 25
    maximum_slider_radius = normalized_radius * 2.4
    assumed_slider_radius = normalized_radius * 1.8

    def __init__(self, hit_object, last_last_object, last_object, clock_rate):
        self.jump_distance = 0
        self.movement_distance = 0
        self.travel_distance = 0
        self.angle = None
        self.movement_time = 0
        self.travel_time = 0

        super().__init__(hit_object, last_object, clock_rate)

        self.last_last_object = last_last_object
        self.last_object = last_object

        self.strain_time = max(self.delta_time, self.min_delta_time)

        self.set_distance(clock_rate)

    def set_distance(self, clock_rate):
        if self.base_object.type == HitObjectType.SPINNER or self.last_object.type == HitObjectType.SPINNER:
            return

        scaling_factor = self.normalized_radius / self.base_object.radius

        if self.base_object.radius < 30:
            small_circle_bonus = min(30 - self.base_object.radius, 5) / 50
            scaling_factor *= 1 + small_circle_bonus

        last_cursor_pos = self.get_end_cursor_position(self.last_object)
        self.jump_distance = (self.base_object.stacked_position * scaling_factor).distance_to(last_cursor_pos * scaling_factor)

        if self.last_object.type == HitObjectType.SLIDER:
            self.compute_slider_cursor_position(self.last_object)
            self.travel_distance = self.last_object.lazy_travel_distance
            self.travel_time = max(self.last_object.lazy_travel_time / clock_rate, self.min_delta_time)
            self.movement_time = max(self.strain_time - self.travel_time, self.min_delta_time)

            tail_jump_distance = self.last_object.stacked_end_position.distance_to(self.base_object.stacked_position) * scaling_factor
            self.movement_distance = max(0, min(self.jump_distance - (self.maximum_slider_radius - self.assumed_slider_radius),
                                                tail_jump_distance - self.maximum_slider_radius))
        else:
            self.movement_time = self.strain_time
            self.movement_distance = self.jump_distance

        if self.last_last_object is not None and self.last_last_object.type != HitObjectType.SPINNER:
            last_last_cursor_pos = self.get_end_cursor_position(self.last_last_object)

            v1 = (last_last_cursor_pos - self.last_object.stacked_position).v()
            v2 = (self.base_object.stacked_position - last_cursor_pos).v()

            dot = v1.dot(v2)
            det = v1.x * v2.y - v1.y * v2.x

            self.angle = abs(math.atan2(det, dot))

    def compute_slider_cursor_position(self, slider):
        if slider.lazy_end_position is not None:
            return

        slider.lazy_travel_time = slider.end_time - slider.time
        end_time_min = slider.lazy_travel_time / slider.span_duration
        if end_time_min % 2 >= 1:
            end_time_min = 1 - end_time_min % 1
        else:
            end_time_min %= 1

        slider.lazy_end_position = slider.stacked_position + slider.position_at(end_time_min)
        curr_cursor_position = slider.stacked_position
        scaling_factor = self.normalized_radius / slider.radius

        for i in range(1, len(slider.nested_objects)):
            curr_movement_obj = slider.nested_objects[i]

            curr_movement = (curr_movement_obj.stacked_position - curr_cursor_position).v()
            curr_movement_length = scaling_factor * curr_movement.magnitude()

            required_movement = self.assumed_slider_radius

            if i == len(slider.nested_objects) - 1:
                lazy_movement = (slider.lazy_end_position - curr_cursor_position).v()

                if lazy_movement.magnitude() < curr_movement.magnitude():
                    curr_movement = lazy_movement

                curr_movement_length = scaling_factor * curr_movement.magnitude()
            elif curr_movement_obj.is_reverse:
                required_movement = self.normalized_radius

            if curr_movement_length > required_movement:
                curr_cursor_position = curr_cursor_position + (curr_movement * ((curr_movement_length - required_movement) / curr_movement_length))
                curr_movement_length *= (curr_movement_length - required_movement) / curr_movement_length
                slider.lazy_travel_distance += curr_movement_length

            if i == len(slider.nested_objects) - 1:
                slider.lazy_end_position = curr_cursor_position

        slider.lazy_travel_distance *= math.pow(1 + (slider.slides - 1) / 2.5, 1.0 / 2.5)

    def get_end_cursor_position(self, hit_object):
        pos = hit_object.stacked_position

        if hit_object.type == HitObjectType.SLIDER:
            self.compute_slider_cursor_position(hit_object)
            if hit_object.lazy_end_position is not None:
                pos = hit_object.lazy_end_position

        return pos
