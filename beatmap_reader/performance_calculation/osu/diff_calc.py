from ...enums import HitObjectType
from ..strain import Skill
from ..util import Util
from ..diff_calc import DifficultyCalculator, DifficultyAttributes
from .hit_object import OsuDifficultyHitObject
from .aim import Aim
from .speed import Speed
from .flashlight import Flashlight
from osu import Mods
from typing import Sequence
import math


class OsuDifficultyAttributes(DifficultyAttributes):
    def __init__(self, mods=None, skills=None, star_rating=None):
        super().__init__(mods, skills, star_rating)

        self.aim_strain = None
        self.speed_strain = None
        self.flashlight_rating = None
        self.slider_factor = None
        self.approach_rate = None
        self.overall_difficulty = None
        self.drain_rate = None
        self.hit_circle_count = None
        self.slider_count = None
        self.spinner_count = None

    @classmethod
    def from_attributes(cls, attributes):
        obj = cls()
        for attr, val in attributes.items():
            setattr(obj, attr, val)
        return obj


class OsuDifficultyCalculator(DifficultyCalculator):
    difficulty_multiplier = 0.0675

    def __init__(self, ruleset, beatmap):
        super().__init__(ruleset, beatmap)
        self.hit_window_great = 0

    def create_difficulty_attributes(self, beatmap, mods: Mods, skills: Sequence[Skill], clock_rate):
        if len(beatmap.hit_objects) == 0:
            return OsuDifficultyAttributes(mods, skills)

        aim_rating = math.sqrt(skills[0].difficulty_value()) * self.difficulty_multiplier
        aim_rating_no_sliders = math.sqrt(skills[1].difficulty_value()) * self.difficulty_multiplier
        speed_rating = math.sqrt(skills[2].difficulty_value()) * self.difficulty_multiplier
        flashlight_rating = math.sqrt(skills[3].difficulty_value()) * self.difficulty_multiplier

        slider_factor = aim_rating_no_sliders / aim_rating if aim_rating > 0 else 1

        if mods != 0 and Mods.Relax in mods:
            speed_rating = 0

        base_aim_performance = math.pow(5 * max(1, aim_rating / 0.0675) - 4, 3) / 100000
        base_speed_performance = math.pow(5 * max(1, speed_rating / 0.0675) - 4, 3) / 100000
        base_flashlight_performance = 0

        if mods != 0 and Mods.Flashlight in mods:
            base_flashlight_performance = math.pow(flashlight_rating, 2) * 25

        base_performance = math.pow(
            math.pow(base_aim_performance, 1.1) +
            math.pow(base_speed_performance, 1.1) +
            math.pow(base_flashlight_performance, 1.1), 1.0 / 1.1
        )

        star_rating = math.pow(1.12, 1/3) * 0.027 * (math.pow(100000 / math.pow(2, 1 / 1.1) * base_performance, 1/3) + 4) \
            if base_performance > 0.00001 else 0

        preempt = Util.difficulty_range(beatmap.difficulty.approach_rate, 1800, 1200, 450) / clock_rate
        drain_rate = beatmap.difficulty.hp_drain_rate

        max_combo = len(beatmap.hit_objects)
        # TODO: slider ticks and add to max_combo

        hit_circles_count = 0
        slider_count = 0
        spinner_count = 0
        for ho in beatmap.hit_objects:
            if ho.type == HitObjectType.HITCIRCLE:
                hit_circles_count += 1
            elif ho.type == HitObjectType.SLIDER:
                slider_count += 1
            elif ho.type == HitObjectType.SPINNER:
                spinner_count += 1

        return OsuDifficultyAttributes.from_attributes({
            "star_rating": star_rating,
            "aim_strain": aim_rating,
            "speed_strain": speed_rating,
            "flashlight_rating": flashlight_rating,
            "slider_factor": slider_factor,
            "approach_rate": (1800 - preempt) / 120 if preempt > 1200 else (1200 - preempt) / 150 + 5,
            "drain_rate": drain_rate,
            "max_combo": max_combo,
            "hit_circle_count": hit_circles_count,
            "slider_count": slider_count,
            "spinner_count": spinner_count,
            "overall_difficulty": (80 - self.hit_window_great) / 6,
            "mods": mods,
            "skills": skills
        })

    def create_difficulty_hit_objects(self, beatmap, clock_rate):
        for i in range(1, len(beatmap.hit_objects)):
            last_last = beatmap.hit_objects[i - 2] if i > 1 else None
            last = beatmap.hit_objects[i - 1]
            current = beatmap.hit_objects[i]

            yield OsuDifficultyHitObject(current, last_last, last, clock_rate)

    def create_skills(self, beatmap, mods, clock_rate):
        self.hit_window_great = Util.difficulty_range(beatmap.difficulty.overall_difficulty, 80, 50, 20)
        return [
            Aim(mods, True),
            Aim(mods, False),
            Speed(mods, self.hit_window_great),
            Flashlight(mods)
        ]

    @staticmethod
    def difficulty_adjustment_mods():
        return [
            Mods.DoubleTime,
            Mods.HalfTime,
            Mods.Easy,
            Mods.HardRock,
            Mods.Flashlight
        ]
