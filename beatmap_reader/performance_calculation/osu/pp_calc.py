from ..pp_calc import PerformanceCalculator
from .diff_calc import OsuDifficultyAttributes
from ..util import Util
from osu import Mods, Score
import math


class OsuScoreAttributes:
    __slots__ = (
        'mods', 'accuracy', 'score_max_combo', 'count_great',
        'count_ok', 'count_meh', 'count_miss'
    )

    def __init__(self):
        self.mods = None
        self.accuracy = None
        self.score_max_combo = None
        self.count_great = None
        self.count_ok = None
        self.count_meh = None
        self.count_miss = None

    @classmethod
    def from_osupy_score(cls, score: Score):
        score_attributes = cls()
        score_attributes.set_attributes({
            "mods": score.mods,
            "accuracy": score.accuracy,
            "score_max_combo": score.max_combo,
            "count_great": score.statistics.count_300,
            "count_ok": score.statistics.count_100,
            "count_meh": score.statistics.count_50,
            "count_miss": score.statistics.count_miss
        })
        return score_attributes

    def set_attributes(self, attributes: dict):
        for k, v in attributes.items():
            setattr(self, k, v)


class OsuPerformanceCalculator(PerformanceCalculator):
    def __init__(self, ruleset, attributes: OsuDifficultyAttributes, score: OsuScoreAttributes):
        super().__init__(ruleset, attributes, score)

        self.mods = score.mods if score.mods else []
        self.accuracy = score.accuracy
        self.score_max_combo = score.score_max_combo
        self.count_great = score.count_great
        self.count_ok = score.count_ok
        self.count_meh = score.count_meh
        self.count_miss = score.count_miss
        self.total_hits = self.count_great + self.count_ok + self.count_meh + self.count_miss
        self.effective_miss_count = self.calculate_effective_miss_count()

    def calculate(self, category_ratings=None):
        multiplier = 1.12

        if Mods.NoFail in self.mods:
            multiplier *= max(0.9, 1 - 0.02 * self.effective_miss_count)

        if Mods.SpunOut in self.mods:
            multiplier *= 1 - math.pow(self.attributes.spinner_count / self.total_hits, 0.85)

        if Mods.Relax in self.mods:
            self.effective_miss_count = min(self.effective_miss_count + self.count_ok + self.count_meh, self.total_hits)
            multiplier *= 0.6

        aim_value = self.compute_aim_value()
        speed_value = self.compute_speed_value()
        accuracy_value = self.compute_accuracy_value()
        flashlight_value = self.compute_flashlight_value()
        total_value = math.pow(
            math.pow(aim_value, 1.1) +
            math.pow(speed_value, 1.1) +
            math.pow(accuracy_value, 1.1) +
            math.pow(flashlight_value, 1.1), 1 / 1.1
        ) * multiplier

        if category_ratings is not None:
            category_ratings.update({
                "aim": aim_value,
                "speed": speed_value,
                "accuracy": accuracy_value,
                "flashlight": flashlight_value,
                "od": self.attributes.overall_difficulty,
                "ar": self.attributes.approach_rate,
                "max_combo": self.attributes.max_combo,
            })

        return total_value

    def compute_aim_value(self):
        raw_aim = self.attributes.aim_strain

        if Mods.TouchDevice in self.mods:
            raw_aim = math.pow(raw_aim, 0.8)

        aim_value = math.pow(5 * max(1, raw_aim / 0.0675) - 4, 3) / 100000

        length_bonus = 0.95 + 0.4 * min(1, self.total_hits / 2000) + \
            (math.log10(self.total_hits / 2000) * 0.5 if self.total_hits > 2000 else 0)

        aim_value *= length_bonus

        if self.effective_miss_count > 0:
            aim_value *= 0.97 * math.pow(1 - math.pow(self.effective_miss_count / self.total_hits, 0.775), self.effective_miss_count)

        if self.attributes.max_combo > 0:
            aim_value *= min(math.pow(self.score_max_combo, 0.8) / math.pow(self.attributes.max_combo, 0.8), 1)

        approach_rate_factor = 0
        if self.attributes.approach_rate > 10.33:
            approach_rate_factor = 0.3 * (self.attributes.approach_rate - 10.33)
        elif self.attributes.approach_rate < 8:
            approach_rate_factor = 0.1 * (8 - self.attributes.approach_rate)

        aim_value *= 1 + approach_rate_factor * length_bonus

        if Mods.Hidden in self.mods:
            aim_value *= 1 + 0.04 * (12 - self.attributes.approach_rate)

        estimate_difficulty_sliders = self.attributes.slider_count + 0.15

        if self.attributes.slider_count > 0:
            estimate_slider_ends_dropped = Util.clamp(min(self.count_ok + self.count_meh + self.count_miss,
                                                          self.attributes.max_combo - self.score_max_combo),
                                                      0, estimate_difficulty_sliders)
            slider_nerf_factor = (1 - self.attributes.slider_factor) * math.pow(1 - estimate_slider_ends_dropped /
                                                                                estimate_difficulty_sliders, 3) + \
                self.attributes.slider_factor
            aim_value *= slider_nerf_factor

        aim_value *= self.accuracy
        aim_value *= 0.98 + math.pow(self.attributes.overall_difficulty, 2) / 2500

        return aim_value

    def compute_speed_value(self):
        speed_value = math.pow(5 * max(1, self.attributes.speed_strain / 0.0675) - 4, 3) / 100000

        length_bonus = 0.95 + 0.4 * min(1, self.total_hits / 2000) + \
            (math.log10(self.total_hits / 2000) * 0.5 if self.total_hits > 2000 else 0)

        speed_value *= length_bonus

        if self.effective_miss_count > 0:
            speed_value *= 0.97 * math.pow(1 - math.pow(self.effective_miss_count / self.total_hits, 0.775),
                                           math.pow(self.effective_miss_count, 0.875))

        if self.attributes.max_combo > 0:
            speed_value *= min(math.pow(self.score_max_combo, 0.8) / math.pow(self.attributes.max_combo, 0.8), 1)

        approach_rate_factor = 0
        if self.attributes.approach_rate > 10.33:
            approach_rate_factor = 0.3 * (self.attributes.approach_rate - 10.33)

        speed_value *= 1 + approach_rate_factor * length_bonus

        if Mods.Hidden in self.mods:
            speed_value *= 1 + 0.04 * (12 - self.attributes.approach_rate)

        speed_value *= (0.95 + math.pow(self.attributes.overall_difficulty, 2) / 750) * \
            math.pow(self.accuracy, (14.5 - max(self.attributes.overall_difficulty, 8)) / 2)

        speed_value *= math.pow(0.98, 0 if self.count_meh < self.total_hits / 500 else self.count_meh - self.total_hits / 500)

        return speed_value

    def compute_accuracy_value(self):
        if Mods.Relax in self.mods:
            return 0

        better_accuracy_percentage = 0
        amount_hit_objects_with_accuracy = self.attributes.hit_circle_count

        if amount_hit_objects_with_accuracy > 0:
            better_accuracy_percentage = ((self.count_great - (self.total_hits - amount_hit_objects_with_accuracy)) *
                                          6 + self.count_ok * 2 + self.count_meh) / \
                                         (amount_hit_objects_with_accuracy * 6)
        else:
            better_accuracy_percentage = 0

        if better_accuracy_percentage < 0:
            better_accuracy_percentage = 0

        accuracy_value = math.pow(1.52163, self.attributes.overall_difficulty) * \
            math.pow(better_accuracy_percentage, 24) * 2.83

        accuracy_value *= min(1.15, math.pow(amount_hit_objects_with_accuracy / 1000, 0.3))

        if Mods.Hidden in self.mods:
            accuracy_value *= 1.08

        if Mods.Flashlight in self.mods:
            self.accuracy *= 1.02

        return accuracy_value

    def compute_flashlight_value(self):
        if Mods.Flashlight not in self.mods:
            return 0

        raw_flashlight = self.attributes.flashlight_rating

        if Mods.TouchDevice in self.mods:
            raw_flashlight = math.pow(raw_flashlight, 0.8)

        flashlight_value = math.pow(raw_flashlight, 2) * 25

        if Mods.Hidden in self.mods:
            flashlight_value *= 1.3

        if self.effective_miss_count > 0:
            flashlight_value *= 0.97 * math.pow(1 - math.pow(self.effective_miss_count / self.total_hits, 0.775),
                                                math.pow(self.effective_miss_count, 0.875))

        if self.attributes.max_combo > 0:
            flashlight_value *= min(math.pow(self.score_max_combo, 0.8) / math.pow(self.attributes.max_combo, 0.8), 1)

        flashlight_value *= 0.7 + 0.1 * min(1, self.total_hits / 200) + \
            (0.2 * min(1, (self.total_hits - 200) / 200) if self.total_hits > 200 else 0)
        flashlight_value *= 0.5 + self.accuracy / 2
        flashlight_value *= 0.98 + math.pow(self.attributes.overall_difficulty, 2) / 2500

        return flashlight_value

    def calculate_effective_miss_count(self):
        combo_based_miss_count = 0

        if self.attributes.slider_count > 0:
            full_combo_threshold = self.attributes.max_combo - 0.1 * self.attributes.slider_count
            if self.score_max_combo < full_combo_threshold:
                combo_based_miss_count = full_combo_threshold / max(1, self.score_max_combo)

        combo_based_miss_count = min(combo_based_miss_count, self.total_hits)

        return max(self.count_miss, math.floor(combo_based_miss_count))
