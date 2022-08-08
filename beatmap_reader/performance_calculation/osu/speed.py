from .strain import OsuStrainSkill
from ...enums import HitObjectType
from .hit_object import OsuDifficultyHitObject
from ..util import Util
import math


class Speed(OsuStrainSkill):
    single_spacing_threshold = 125
    rhythm_multiplier = 0.75
    history_time_max = 5000
    min_speed_bonus = 75
    speed_balancing_factor = 40

    skill_multiplier = 1375
    strain_decay_base = 0.3

    reduced_section_count = 5
    difficulty_multiplier = 1.04
    history_length = 32

    def __init__(self, mods, hit_window_great):
        super().__init__(mods)
        self.great_window = hit_window_great
        self.current_strain = 0
        self.current_rhythm = 0

    def calculate_rhythm_bonus(self, current: OsuDifficultyHitObject):
        if current.base_object.type == HitObjectType.SPINNER:
            return 0

        previous_island_size = 0

        rhythm_complexity_sum = 0
        island_size = 1
        start_ratio = 0

        first_delta_switch = False

        for i in reversed(range(1, len(self.previous)-1)):
            curr_obj = self.previous[i-1]
            prev_obj = self.previous[i]
            last_obj = self.previous[i+1]

            curr_historical_decay = max(0, (self.history_time_max - (current.start_time - curr_obj.start_time))) / self.history_time_max

            if curr_historical_decay != 0:
                curr_historical_decay = min((len(self.previous) - i) / len(self.previous), curr_historical_decay)

                curr_delta = curr_obj.strain_time
                prev_delta = prev_obj.strain_time
                last_delta = last_obj.strain_time
                curr_ratio = 1 + 6 * min(0.5, math.pow(math.sin(math.pi / (min(prev_delta, curr_delta) / max(prev_delta, curr_delta))), 2))

                window_penalty = min(1, max(0, abs(prev_delta - curr_delta) - self.great_window * 0.6) / (self.great_window * 0.6))
                window_penalty = min(1, window_penalty)  # idk if this does anything, but it was in the pp code, so I'll just keep it

                effective_ratio = window_penalty * curr_ratio

                if first_delta_switch:
                    if not (prev_delta > 1.25 * curr_delta or prev_delta * 1.25 < curr_delta):
                        if island_size < 7:
                            island_size += 1
                        else:
                            if self.previous[i - 1].base_object.type == HitObjectType.SLIDER:
                                effective_ratio *= 0.125
                            if self.previous[i].base_object .type == HitObjectType.SLIDER:
                                effective_ratio *= 0.25
                            if previous_island_size == island_size:
                                effective_ratio *= 0.25
                            if previous_island_size % 2 == island_size % 2:
                                effective_ratio *= 0.5
                            if last_delta > prev_delta + 10 and prev_delta > curr_delta + 10:
                                effective_ratio *= 0.125

                            rhythm_complexity_sum += math.sqrt(effective_ratio * start_ratio) * curr_historical_decay * \
                                math.sqrt(4 + island_size) / 2 * math.sqrt(4 + previous_island_size) / 2

                            start_ratio = effective_ratio

                            previous_island_size = island_size

                            if prev_delta * 1.25 < curr_delta:
                                first_delta_switch = False

                            island_size = 1
                elif prev_delta > 1.25 * curr_delta:
                    first_delta_switch = True
                    start_ratio = effective_ratio
                    island_size = 1

        return math.sqrt(4 + rhythm_complexity_sum * self.rhythm_multiplier) / 2

    def strain_value_of(self, current):
        if current.base_object.type == HitObjectType.SPINNER:
            return 0

        osu_curr_obj = current
        osu_prev_obj = self.previous[0] if len(self.previous) > 0 else None

        strain_time = osu_curr_obj.strain_time
        great_window_full = self.great_window * 2
        speed_window_ratio = strain_time / great_window_full

        if osu_prev_obj is not None and strain_time < great_window_full and osu_prev_obj.strain_time > strain_time:
            strain_time = Util.lerp(osu_prev_obj.strain_time, strain_time, speed_window_ratio)

        strain_time /= Util.clamp((strain_time / great_window_full) / 0.93, 0.92, 1)

        speed_bonus = 1

        if strain_time < self.min_speed_bonus:
            speed_bonus = 1 + 0.75 * math.pow((self.min_speed_bonus - strain_time) / self.speed_balancing_factor, 2)

        distance = min(self.single_spacing_threshold, osu_curr_obj.travel_distance + osu_curr_obj.jump_distance)

        return (speed_bonus + speed_bonus * math.pow(distance / self.single_spacing_threshold, 3.5)) / strain_time

    def strain_decay(self, ms):
        return math.pow(self.strain_decay_base, ms / 1000)

    def calculate_initial_strain(self, time):
        return (self.current_strain * self.current_rhythm) * self.strain_decay(time - self.previous[0].start_time)

    def strain_value_at(self, hit_object: OsuDifficultyHitObject):
        self.current_strain *= self.strain_decay(hit_object.delta_time)
        self.current_strain += self.strain_value_of(hit_object) * self.skill_multiplier

        self.current_rhythm = self.calculate_rhythm_bonus(hit_object)

        return self.current_strain * self.current_rhythm
