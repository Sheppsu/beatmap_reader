import os
import numpy as np
from .enums import SampleSet


def confirm(path):
    m, options = "", ("y", "n", "yes", "no")
    while m not in options: m = input(f"Should I use {path} to load your maps? ").lower()
    return not bool(options.index(m) % 2)


def is_beatmapset(path):
    for file in os.listdir(path):
        if file.endswith(".osu") and not os.path.isdir(os.path.join(path, file)):
            return True
    return False


def search_for_songs_folder(confirmation_function=confirm):
    # This function is pretty slow lol
    for root, dirs, files in os.walk("/"):
        if "osu!.exe" in files and "Songs" in dirs:
            path = os.path.join(root, "Songs")
            if confirm(path):
                return path


def get_sample_set(sample_set):
    if sample_set.lower() == "none":
        return
    if sample_set.isdigit():
        sample_set = {
            "0": "Default", "1": "Normal",
            "2": "Soft", "3": "Drum"
        }[sample_set]
    return SampleSet(sample_set)


def difficulty_range(difficulty, min, mid, max):
    if difficulty > 5:
        return mid + (max - mid) * (difficulty - 5) / 5
    if difficulty < 5:
        return mid - (mid - min) * (5 - difficulty) / 5
    return mid


def linspace(start, stop, interval):
    if start > stop:
        raise ValueError("stop must be greater than start")
    elif start == stop:
        return np.zeros(1)
    array = np.zeros(int((stop - start) // interval) + 1)
    for i in range(len(array)):
        array[i] = interval * i
    return array
