from .strain import OsuStrainSkill
from .hit_object import OsuDifficultyHitObject
from ...enums import HitObjectType
import math


class Flashlight(OsuStrainSkill):
    skill_multiplier = 0.15
    strain_decay_base = 0.15
    decay_weight = 1.0
    history_length = 10

    def __init__(self, mods):
        super().__init__(mods)

        self.current_strain = 0

    def strain_value_of(self, current: OsuDifficultyHitObject):
        if current.base_object.type == HitObjectType.SPINNER:
            return 0

        osu_current = current
        osu_hit_object = osu_current.base_object

        scaling_factor = 52 / osu_hit_object.radius
        small_dist_nerf = 1
        cumulative_strain_time = 0

        result = 0

        for i in range(len(self.previous)):
            osu_previous = self.previous[i]
            osu_previous_hit_object = osu_previous.base_object

            if osu_previous_hit_object.type != HitObjectType.SPINNER:
                jump_distance = osu_hit_object.stacked_position.distance_to(osu_previous_hit_object.end_position)

                cumulative_strain_time += osu_previous.strain_time

                if i == 0:
                    small_dist_nerf = min(1, jump_distance / 75)

                stack_nerf = min(1, (osu_previous.jump_distance / scaling_factor) / 25)

                result += math.pow(0.8, i) * stack_nerf * scaling_factor * jump_distance / cumulative_strain_time

        return math.pow(small_dist_nerf * result, 2)

    def strain_decay(self, ms):
        return math.pow(self.strain_decay_base, ms / 1000)

    def calculate_initial_strain(self, time):
        return self.current_strain * self.strain_decay(time - self.previous[0].start_time)

    def strain_value_at(self, hit_object):
        self.current_strain *= self.strain_decay(hit_object.delta_time)
        self.current_strain += self.strain_value_of(hit_object) * self.skill_multiplier

        return self.current_strain
