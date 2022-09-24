import os
from .util import is_beatmapset


class SongsReader:
    def __init__(self, path):
        self.path = path
        self.beatmapsets = []

    def cast_beatmapset_readers(self, cast_to):
        self.beatmapsets = list(map(cast_to, self.beatmapsets))

    def discover_all_beatmapsets(self):
        for beatmapset in os.listdir(self.path):
            beatmapset = os.path.join(self.path, beatmapset)
            if not os.path.isdir(beatmapset):
                continue
            if not is_beatmapset(beatmapset):
                continue
            self.beatmapsets.append(BeatmapsetReader(beatmapset))


class BeatmapsetReader:
    def __init__(self, path):
        self.path = path
        self.beatmaps = []

    def cast_beatmap_readers(self, cast_to):
        self.beatmaps = list(map(cast_to, self.beatmaps))

    def discover_beatmaps(self):
        for beatmap in os.listdir(self.path):
            full_beatmap = os.path.join(self.path, beatmap)
            if beatmap.endswith(".osu") and not os.path.isdir(full_beatmap):
                self.beatmaps.append(BeatmapReader(full_beatmap))


class BeatmapReader:
    key_value_sections = (
        "General", "Editor", "Metadata", "Difficulty", "Colours"
    )

    def __init__(self, path):
        self.path = path

    def load_beatmap_data(self):
        data = {}
        with open(self.path, "r", encoding="utf-8") as f:
            current_section = None
            for line in f.readlines():
                line = line[:-1]
                ascii_line = "".join(filter(lambda char: char.isascii(), line))
                if line.strip() == "" or line.startswith("//"):
                    continue
                if current_section is None and ascii_line.startswith("osu file format"):
                    data.update({"version": int(ascii_line[17:].strip())})
                    continue
                if line.startswith("[") and line.endswith("]"):
                    current_section = line[1:-1]
                    data.update({current_section: {} if current_section in self.key_value_sections else []})
                    continue
                if current_section is None:
                    continue
                if current_section in self.key_value_sections:
                    # Done this way for safety
                    split = line.split(":")
                    key = split[0].strip()
                    value = ":".join(split[1:]).strip()

                    data[current_section].update({key: value})
                else:
                    data[current_section].append(line.strip())
        return data
