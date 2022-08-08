from .strain import OsuStrainSkill
from ...enums import HitObjectType
from ..util import Util
from .hit_object import OsuDifficultyHitObject
import math


class Aim(OsuStrainSkill):
    history_length = 2

    wide_angle_multiplier = 1.5
    acute_angle_multiplier = 2
    slider_multiplier = 1.5
    velocity_change_multiplier = 0.75

    skill_multiplier = 23.25
    strain_decay_base = 0.15

    def __init__(self, mods, with_sliders):
        super().__init__(mods)
        self.with_sliders = with_sliders
        self.current_strain = 0

    def strain_value_of(self, curr_obj: OsuDifficultyHitObject):
        if curr_obj.base_object.type == HitObjectType.SPINNER or len(self.previous) <= 1 \
                or self.previous[0].base_object.type == HitObjectType.SPINNER:
            return 0

        last_obj = self.previous[0]
        last_last_obj = self.previous[1]

        curr_velocity = curr_obj.jump_distance / curr_obj.strain_time

        if last_obj.base_object.type == HitObjectType.SLIDER and self.with_sliders:
            movement_velocity = curr_obj.movement_distance / curr_obj.movement_time
            travel_velocity = curr_obj.travel_distance / curr_obj.travel_time
            curr_velocity = max(curr_velocity, movement_velocity + travel_velocity)

        prev_velocity = last_obj.jump_distance / last_obj.strain_time

        if last_last_obj.base_object.type == HitObjectType.SLIDER and self.with_sliders:
            movement_velocity = last_obj.movement_distance / last_obj.movement_time
            travel_velocity = last_obj.travel_distance / last_obj.travel_time
            prev_velocity = max(prev_velocity, movement_velocity + travel_velocity)

        wide_angle_bonus = 0
        acute_angle_bonus = 0
        slider_bonus = 0
        velocity_change_bonus = 0

        aim_strain = curr_velocity

        if max(curr_obj.strain_time, last_obj.strain_time) < 1.25 * min(curr_obj.strain_time, last_obj.strain_time):
            if curr_obj.angle is not None and last_obj.angle is not None and last_last_obj.angle is not None:
                curr_angle = curr_obj.angle
                last_angle = last_obj.angle
                last_last_angle = last_last_obj.angle

                angle_bonus = min(curr_velocity, prev_velocity)

                wide_angle_bonus = self.calc_wide_angle_bonus(curr_angle)
                acute_angle_bonus = self.calc_acute_angle_bonus(curr_angle)

                if curr_obj.strain_time > 100:
                    acute_angle_bonus = 0
                else:
                    acute_angle_bonus *= self.calc_acute_angle_bonus(last_angle) * \
                                         min(angle_bonus, 125 / curr_obj.strain_time) * \
                                         math.pow(math.sin(math.pi / 2 * min(1, (100 - curr_obj.strain_time) / 25)), 2) * \
                                         math.pow(math.sin(math.pi / 2 * (Util.clamp(curr_obj.jump_distance, 50, 100) - 50) / 50), 2)

                wide_angle_bonus *= angle_bonus * (1 - min(wide_angle_bonus, math.pow(self.calc_wide_angle_bonus(last_angle), 3)))
                acute_angle_bonus *= 0.5 + 0.5 * (1 - min(acute_angle_bonus, math.pow(self.calc_acute_angle_bonus(last_last_angle), 3)))

        if max(prev_velocity, curr_velocity) != 0:
            prev_velocity = (last_obj.jump_distance + last_obj.travel_distance) / last_obj.strain_time
            curr_velocity = (curr_obj.jump_distance + curr_obj.travel_distance) / curr_obj.strain_time

            dist_ratio = math.pow(math.sin(math.pi / 2 * abs(prev_velocity - curr_velocity) / max(prev_velocity, curr_velocity)), 2)
            overlap_velocity_buff = min(125 / min(curr_obj.strain_time, last_obj.strain_time), abs(prev_velocity - curr_velocity))
            non_overlap_velocity_buff = abs(prev_velocity - curr_velocity) * \
                                        math.pow(math.sin(math.pi / 2 * min(1, min(curr_obj.jump_distance, last_obj.jump_distance) / 100)), 2)

            velocity_change_bonus = max(overlap_velocity_buff, non_overlap_velocity_buff) * dist_ratio
            velocity_change_bonus *= math.pow(min(curr_obj.strain_time, last_obj.strain_time) / max(curr_obj.strain_time, last_obj.strain_time), 2)

        if curr_obj.travel_time != 0:
            slider_bonus = curr_obj.travel_distance / curr_obj.travel_time

        aim_strain += max(acute_angle_bonus * self.acute_angle_multiplier,
                          wide_angle_bonus * self.wide_angle_multiplier +
                          velocity_change_bonus * self.velocity_change_multiplier)

        if self.with_sliders:
            aim_strain += slider_bonus * self.slider_multiplier

        return aim_strain

    @staticmethod
    def calc_wide_angle_bonus(angle):
        return math.pow(math.sin(3 / 4 * (min(5 / 6 * math.pi, max(math.pi / 6, angle)) - math.pi / 6)), 2)

    @staticmethod
    def calc_acute_angle_bonus(angle):
        return 1 - Aim.calc_wide_angle_bonus(angle)

    @staticmethod
    def apply_diminish_exp(val):
        return math.pow(val, 0.99)

    def strain_decay(self, ms):
        return math.pow(self.strain_decay_base, ms / 1000)

    def calculate_initial_strain(self, time):
        return self.current_strain * self.strain_decay(time - self.previous[0].start_time)

    def strain_value_at(self, hit_object: OsuDifficultyHitObject):
        self.current_strain *= self.strain_decay(hit_object.delta_time)
        self.current_strain += self.strain_value_of(hit_object) * self.skill_multiplier

        return self.current_strain
