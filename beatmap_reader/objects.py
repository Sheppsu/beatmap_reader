from .read import SongsReader, BeatmapsetReader, BeatmapReader
from .util import search_for_songs_folder
from typing import Sequence


class Beatmap:
    def __init__(self, reader: BeatmapReader):
        self.reader = reader
        self.data = None

    def load(self):
        self.data = self.reader.load_beatmap_data()
        self._format_data()

    def _format_data(self):
        pass


class Beatmapset:
    def __init__(self, reader: BeatmapsetReader):
        self.reader = reader
        self.reader.discover_beatmaps()
        self.reader.cast_beatmap_readers(Beatmap)

    @property
    def path(self):
        return self.reader.path

    @property
    def beatmaps(self) -> Sequence[Beatmap]:
        return self.reader.beatmaps


class SongsFolder:
    def __init__(self, reader: SongsReader):
        self.reader = reader
        self.reader.discover_all_beatmapsets()
        self.reader.cast_beatmapset_readers(Beatmapset)

    @classmethod
    def from_path(cls, path=None, confirmation_function=None):
        path = path
        if path is None:
            args = [confirmation_function] if confirmation_function is not None else []
            path = search_for_songs_folder(*args)
            if path is None:
                raise Exception("Bruh")  # TODO: b3uofqwfeniOGUWgbeu
        return cls(SongsReader(path))

    @property
    def beatmapsets(self) -> Sequence[Beatmapset]:
        return self.reader.beatmapsets

    @property
    def path(self):
        return self.reader.path


class HitObject:
    pass


class HitCircle(HitObject):
    pass


class Slider(HitObject):
    pass


class Spinner(HitObject):
    pass
