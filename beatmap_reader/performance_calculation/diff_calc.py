from ..enums import Mods
from .util import Util
from typing import List, Union


class DifficultyAttributes:
    def __init__(self, mods=None, skills=None, star_rating=None):
        self.mods = mods
        self.skills = skills
        self.star_rating = star_rating
        self.max_combo = 0


class TimedDifficultyAttributes:
    def __init__(self, time, attributes):
        self.time = time
        self.attributes = attributes

    def compare_to(self, other):
        return self.time - other.time


class ProgressiveCalculationBeatmap:
    def __init__(self, beatmap):
        self.beatmap = beatmap
        self.hit_objects = []

    def __getattr__(self, item):
        return getattr(self.beatmap, item)


class DifficultyCalculator:
    def __init__(self, ruleset, beatmap):
        self.ruleset = ruleset
        self.beatmap = beatmap

        self.clock_rate = 0
        self.playable_mods: Union[Mods, None] = None

    def calculate(self, mods: Mods):
        self.pre_process(mods)

        skills = self.create_skills(self.beatmap, self.playable_mods, self.clock_rate)

        if len(self.beatmap.hit_objects) == 0:
            return self.create_difficulty_attributes(self.beatmap, self.playable_mods, skills, self.clock_rate)

        for hit_obj in self.get_difficulty_hit_objects():
            for skill in skills:
                skill.process_internal(hit_obj)

        return self.create_difficulty_attributes(self.beatmap, self.playable_mods, skills, self.clock_rate)

    def calculate_timed(self, mods: Mods):
        self.pre_process(mods)

        attribs = []

        if len(self.beatmap.hit_objects) == 0:
            return attribs

        skills = self.create_skills(self.beatmap, self.playable_mods, self.clock_rate)
        progressive_beatmap = ProgressiveCalculationBeatmap(self.beatmap)

        for hit_obj in self.get_difficulty_hit_objects():
            progressive_beatmap.hit_objects.append(hit_obj.base_object)

            for skill in skills:
                skill.process_internal(hit_obj)

            attribs.append(TimedDifficultyAttributes(
                hit_obj.end_time * self.clock_rate, self.create_difficulty_attributes(
                    progressive_beatmap, self.playable_mods, skills, self.clock_rate)))

        return attribs
    
    def calculate_all(self):
        for combination in self.create_difficulty_adjustment_mod_combinations():
            yield self.calculate(combination)
        
    def get_difficulty_hit_objects(self):
        return self.sort_objects(self.create_difficulty_hit_objects(self.beatmap, self.clock_rate))
    
    def pre_process(self, mods: Mods):
        self.playable_mods = mods
        self.clock_rate = Util.get_time_rate(mods)

    @staticmethod
    def sort_objects(hit_objects):
        return sorted(hit_objects, key=lambda h: h.base_object.time)

    def _create_difficulty_adjustment_mod_combinations(self, remaining_mods: List[Mods], current_set: List[Mods], current_set_cnt=0):
        if current_set_cnt == 0:
            yield []
        elif current_set_cnt == 1:
            yield current_set[0]
        else:
            yield Mods.parse_any_list(current_set)

        def check_mod_sets(conditional):
            return any(list(map(
                    lambda m1: any(list(map(
                        lambda m2: conditional(m1, m2),
                        next_set))),
                    current_set)))

        for i in range(len(remaining_mods)):
            next_set = remaining_mods[i:]

            if check_mod_sets(lambda m1, m2: not m1.is_compatible_with(m2)):
                continue

            if check_mod_sets(lambda m1, m2: m1 == m2):
                continue

            for combo in self._create_difficulty_adjustment_mod_combinations(remaining_mods[i+1:], current_set + next_set, len(next_set)+current_set_cnt):
                yield combo

    def create_difficulty_adjustment_mod_combinations(self):
        return self._create_difficulty_adjustment_mod_combinations(self.difficulty_adjustment_mods(), [])

    @staticmethod
    def difficulty_adjustment_mods():
        return []

    def create_difficulty_attributes(self, beatmap, mods, skills, clock_rate):
        raise NotImplementedError()

    def create_difficulty_hit_objects(self, beatmap, clock_rate):
        raise NotImplementedError()

    def create_skills(self, beatmap, mods, clock_rate):
        raise NotImplementedError()
