import os
from .enums import SampleSet


def confirm(path):
    m, options = "", ("y", "n", "yes", "no")
    while m not in options: m = input(f"Should I use {path} to load your maps?").lower()
    return not bool(options.index(m) % 2)


def is_beatmapset(path):
    for file in os.listdir(path):
        if file.endswith(".osu") and not os.path.isdir(os.path.join(path, file)):
            return True
    return False


def search_for_songs_folder(confirmation_function=confirm):
    # This function is pretty slow lol
    def recursion(path):
        try:
            files = os.listdir(path)
        except PermissionError:
            return
        if "osu!.exe" in files and "Songs" in files:
            return os.path.join(path, "Songs")
        for file in files:
            try:
                m = recursion(os.path.join(path, file))
                if m is not None:
                    return m
            except NotADirectoryError:
                pass

    while True:
        path = recursion("/")
        if path is None: return
        if confirmation_function(path): return path


def get_sample_set(sample_set):
    if sample_set.lower() == "none":
        return
    if sample_set.isdigit():
        sample_set = {
            "0": "Default", "1": "Normal",
            "2": "Soft", "3": "Drum"
        }[sample_set]
    return SampleSet(sample_set)
