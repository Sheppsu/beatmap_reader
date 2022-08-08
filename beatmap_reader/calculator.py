from .performance_calculation import *
from .enums import GameMode


class BeatmapCalculator:
    def __init__(self, beatmap):
        if not beatmap.fully_loaded:
            raise ValueError("Beatmap must be fully loaded.")

        self.difficulty_attributes = {}
        self.beatmap = beatmap

        if beatmap.general.mode == GameMode.STANDARD:
            self.calculator = OsuDifficultyCalculator(beatmap.general.mode, beatmap)
        else:
            raise NotImplementedError("Game mode not implemented")

    def get_difficulty_attributes(self, mods=None):
        if mods is None:
            mods = 0
        if mods not in self.difficulty_attributes:
            self.calculate_difficulty_attributes(mods)
        return self.difficulty_attributes[mods]

    def calculate_difficulty_attributes(self, mods):
        self.difficulty_attributes[mods] = self.calculator.calculate(mods)
