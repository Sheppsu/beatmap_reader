from .read import SongsReader, BeatmapsetReader, BeatmapReader
from .util import search_for_songs_folder, get_sample_set
from .enums import *
from .curve import Curve
from typing import Sequence, Union
import os
import traceback
import pygame


class HitObject:
    def __new__(cls, parent, data):
        # TODO: hit sound and hit sample objects
        data = data.split(",")
        x, y = int(data[0]), int(data[1])
        time = int(data[2])
        type = int(data[3])
        new_combo = bool(type & (1 << 2))
        combo_colour_skip = 0 if not new_combo else type & 0b01110000
        hit_sound = int(data[4]) if data[4] else None  # Got an error where the hit sound was missing :shrug:
        params = data[5:]
        hit_sample = params.pop(-1) if params and ":" in params[-1] else None
        if type & (1 << 0):
            return HitCircle(params, parent, x, y, time, new_combo, combo_colour_skip,
                             hit_sound, hit_sample)
        elif type & (1 << 1):
            return Slider(params, parent, x, y, time, new_combo, combo_colour_skip,
                          hit_sound, hit_sample)
        elif type & (1 << 3):
            return Spinner(params, parent, x, y, time, new_combo, combo_colour_skip,
                           hit_sound, hit_sample)
        elif type & (1 << 7):
            return ManiaHoldKey(params, parent, x, y, time, new_combo, combo_colour_skip,
                                hit_sound, hit_sample)
        else:
            raise ValueError("Hit object does not have a valid type specified.")


class HitObjectBase:
    def __init__(self, parent, x, y, time, new_combo, combo_colour_skip,
                 hit_sound, hit_sample):
        self.parent = parent
        self.x = x
        self.y = y
        self.time = time
        self.new_combo = new_combo
        self.combo_colour_skip = combo_colour_skip
        self.hit_sound = hit_sound
        self.hit_sample = hit_sample


class HitCircle(HitObjectBase):
    type = HitObjectType.HITCIRCLE

    def __init__(self, params, parent, *args):
        super().__init__(parent, *args)


class Slider(HitObjectBase):
    type = HitObjectType.SLIDER

    def __init__(self, params, parent, *args):
        super().__init__(parent, *args)
        self.curve = Curve(params[0], self)
        self.slides = int(params[1])
        self.length = float(params[2])
        # TODO: yeppers
        self.edge_sounds = params[3] if len(params) > 3 else None
        self.edge_sets = params[4] if len(params) > 4 else None

        self.surf = None
        self.ui_timing_point = None
        self.i_timing_point = None
        for timing_point in self.parent.timing_points:
            if timing_point.time <= self.time:
                if timing_point.type == TimingPointType.UNINHERITED:
                    self.ui_timing_point = timing_point
                else:
                    self.i_timing_point = timing_point

        if self.ui_timing_point is None:
            self.ui_timing_point = self.parent.timing_points[0]

        s_vel = self.i_timing_point.slider_velocity if self.i_timing_point is not None else 1
        self.end_time = round(self.time + self.ui_timing_point.beat_duration * self.length * self.slides /
                              (self.parent.difficulty.slider_multiplier*s_vel*100))

    def render(self, screen_size, placement_offset, osu_pixel_multiplier=1, color=(0, 0, 0),
               border_color=(255, 255, 255)):
        # TODO: some kind of auto coloring based on skin and beatmap combo colors etc.
        surf = pygame.Surface(screen_size)
        surf.set_colorkey((0, 0, 0))
        try:
            size = self.curve.radius_offset*osu_pixel_multiplier
            for c, r in ((border_color, size), (color, size-1)):
                for point in self.curve.curve_points:
                    pygame.draw.circle(surf, c, (point[0] * osu_pixel_multiplier + placement_offset[0],
                                                 point[1] * osu_pixel_multiplier + placement_offset[1]),
                                       r)
        except:
            print(f"Error occurred while rendering slider at {self.time} in {self.parent.path}.")
            traceback.print_exc()
        self.surf = surf


class Spinner(HitObjectBase):
    type = HitObjectType.SPINNER

    def __init__(self, params, parent, *args):
        super().__init__(parent, *args)
        self.end_time = int(params[0])
        self.x = 256
        self.y = 192


class ManiaHoldKey(HitObjectBase):
    type = HitObjectType.MANIA_HOLD_KEY

    def __init__(self, params, parent, *args):
        super().__init__(parent, *args)
        self.end_time = int(self.hit_sample.split(":")[0])
        self.hit_sample = self.hit_sample[len(str(self.end_time))+1:]

    def get_column(self, total_columns):
        return self.x * total_columns // 512


class General:
    __slots__ = (
        "audio_file", "audio_lead_in", "audio_hash", "preview_time",
        "countdown", "sample_set", "stack_leniency", "mode",
        "letterbox_in_breaks", "story_fire_in_front", "use_skin_sprites",
        "always_show_playfield", "overlay_position", "skin_preference",
        "epilepsy_warning", "special_style", "widescreen_storyboard",
        "samples_match_playback_rate"
    )

    def __init__(self, path: str, data: dict):
        self.audio_file = data.get("AudioFilename")
        if self.audio_file is not None:
            self.audio_file = os.path.join(os.path.split(path)[0], self.audio_file)
        self.audio_lead_in = int(data.get("AudioLeadIn", 0))
        self.audio_hash = data.get("AudioHash")
        self.preview_time = int(data.get("PreviewTime", -1))
        self.countdown = Countdown(int(data.get("Countdown", 1)))
        self.sample_set = get_sample_set(data.get("SampleSet", "Normal"))
        self.stack_leniency = float(data.get("StackLeniency", 0.7))
        self.mode = GameMode(int(data.get("Mode", 0)))
        self.letterbox_in_breaks = bool(data.get("LetterboxInBreaks", 0))
        self.story_fire_in_front = bool(data.get("StoryFireInFront", 1))
        self.use_skin_sprites = bool(data.get("UseSkinSprites", 0))
        self.always_show_playfield = bool(data.get("AlwaysShowPlayfield", 0))
        self.overlay_position = OverlayPosition(data.get("OverlayPosition", "NoChange"))
        self.skin_preference = data.get("SkinPreference")
        self.epilepsy_warning = bool(data.get("EpilepsyWarning", 0))
        self.special_style = bool(data.get("SpecialStyle", 0))
        self.widescreen_storyboard = bool(data.get("WidescreenStoryboard", 0))
        self.samples_match_playback_rate = bool(data.get("SamplesMatchPlaybackRate", 0))


class Editor:
    __slots__ = (
        "bookmarks", "distance_spacing", "beat_divisor",
        "grid_size", "timeline_zoom"
    )

    def __init__(self, data: dict):
        self.bookmarks = list(map(int, data["Bookmarks"].split(","))) if "Bookmarks" in data and data["Bookmarks"] else []
        self.distance_spacing = float(data["DistanceSpacing"])
        self.beat_divisor = float(data["BeatDivisor"])
        self.grid_size = int(data["GridSize"])
        self.timeline_zoom = float(data["TimelineZoom"]) if "TimelineZoom" in data else None


class Metadata:
    __slots__ = (
        "title", "title_unicode", "artist", "artist_unicode",
        "creator", "version", "source", "tags", "beatmap_id",
        "beatmapset_id"
    )

    def __init__(self, data):
        self.title = data["Title"]
        self.title_unicode = data.get("TitleUnicode", self.title)
        self.artist = data["Artist"]
        self.artist_unicode = data.get("ArtistUnicode", self.artist)
        self.creator = data["Creator"]
        self.version = data["Version"]
        self.source = data.get("Source")
        self.tags = data.get("Tags")
        self.beatmap_id = data.get("BeatmapID")
        self.beatmapset_id = data.get("BeatmapSetID")


class Difficulty:
    __slots__ = (
        "hp_drain_rate", "circle_size", "overall_difficulty",
        "approach_rate", "slider_multiplier", "slider_tick_rate"
    )

    def __init__(self, data):
        self.hp_drain_rate = float(data["HPDrainRate"])
        self.circle_size = float(data["CircleSize"])
        self.overall_difficulty = float(data["OverallDifficulty"])
        self.approach_rate = float(data.get("ApproachRate", self.overall_difficulty))
        self.slider_multiplier = float(data["SliderMultiplier"])
        self.slider_tick_rate = float(data["SliderTickRate"])


class Events:
    pass


class Effects:
    def __init__(self, effects):
        self.is_kiai_enabled = bool(effects & (1 << 0))
        self.is_first_barline_omitted = bool(effects & (1 << 3))


class UninheritedTimingPoint:
    type = TimingPointType.UNINHERITED

    def __init__(self, time, beat_duration, meter, sample_set,
                 sample_index, volume, effects):
        self.time = time
        self.beat_duration = beat_duration
        self.meter = meter
        self.sample_set = sample_set
        self.sample_index = sample_index
        self.volume = volume
        self.effects = Effects(effects) if effects is not None else None


class InheritedTimingPoint:
    type = TimingPointType.INHERITED

    def __init__(self, time, slider_velocity, sample_set,
                 sample_index, volume, effects):
        self.time = time
        self.slider_velocity = 1/(-slider_velocity/100)
        self.sample_set = sample_set
        self.sample_index = sample_index
        self.volume = volume
        self.effects = Effects(effects) if effects is not None else None


class TimingPoint:
    def __new__(cls, string):
        data = string.split(",")
        time = float(data[0])
        beat_length = float(data[1])
        # TODO: find some default values for these I guess
        meter = int(data[2]) if len(data) > 2 else None
        sample_set = get_sample_set(data[3]) if len(data) > 3 else None
        sample_index = int(data[4]) if len(data) > 4 else None
        volume = int(data[5]) if len(data) > 5 else None
        uninherited = bool(int(data[6])) if len(data) > 6 else None
        effects = int(data[7]) if len(data) > 7 else None
        if uninherited or uninherited is None:
            return UninheritedTimingPoint(time, beat_length, meter, sample_set,
                                          sample_index, volume, effects)
        return InheritedTimingPoint(time, beat_length, sample_set, sample_index,
                                    volume, effects)


class Colour:
    def __init__(self, colour):
        self.int_colour = colour

    @classmethod
    def from_hex(cls, hex_colour):
        if hex_colour is None:
            return
        hex_colour = hex_colour.replace("#", "")  # Just in case
        return cls(int("0x"+hex_colour, 16))

    @classmethod
    def from_rgb(cls, red, green, blue):
        if None in (red, green, blue):
            return
        return cls(int(hex(red)+hex(green)[2:]+hex(blue)[2:], 16))

    @classmethod
    def from_rgb_string(cls, string):
        if string is None:
            return
        return cls.from_rgb(*list(map(
            lambda val: int(val.strip()),
            string.split(",")
        )))

    @property
    def hex_colour(self):
        return hex(self.int_colour)[2:]

    @property
    def rgb_colour(self):
        hex_colour = self.hex_colour
        return int(hex_colour[:2], 16), int(hex_colour[2:4], 16), int(hex_colour[4:6], 16)


class Colours:
    def __init__(self, data):
        self.combo_colours = {}
        for combo, colour in data.items():
            if combo.startswith("Combo"):
                self.combo_colours.update({
                    int(combo.replace("Combo", "")): Colour.from_rgb_string(colour)
                })
        self.slider_track_override = Colour.from_rgb_string(data.get("SliderTrackOverride"))
        self.slider_border = Colour.from_rgb_string(data.get("SliderBorder"))


class Beatmap:
    def __init__(self, reader: BeatmapReader):
        self.reader = reader
        self.general: Union[General, dict, None] = None
        self.editor: Union[Editor, dict, None] = None
        self.metadata: Union[Metadata, dict, None] = None
        self.difficulty: Union[Difficulty, dict, None] = None
        self.events: Union[Events, dict, None] = None
        self.timing_points: Union[Sequence[TimingPoint], dict, None] = None
        self.colours: Union[Colours, dict, None] = None
        self.hit_objects: Union[Sequence[HitObject], dict, None] = None

        self.fully_loaded = False

    def load(self):
        try:
            data = self.reader.load_beatmap_data()
        except:
            print(f"There was a problem while loading the data in {self.reader.path}\n{traceback.format_exc()}")
            return False
        self.general = data.get("General")
        self.editor = data.get("Editor")
        self.metadata = data.get("Metadata")
        self.difficulty = data.get("Difficulty")
        self.events = data.get("Events")
        self.timing_points = data.get("TimingPoints")
        self.colours = data.get("Colours")
        self.hit_objects = data.get("HitObjects")
        try:
            self._format_data()
            self.fully_loaded = True
            return True
        except:
            print(f"There was a problem while formatting the data in {self.reader.path}\n{traceback.format_exc()}")
            return False

    def _format_data(self):
        self.general = General(self.reader.path, self.general) if self.general is not None else None
        self.editor = Editor(self.editor) if self.editor is not None else None
        self.metadata = Metadata(self.metadata) if self.metadata is not None else None
        self.difficulty = Difficulty(self.difficulty) if self.difficulty is not None else None
        self.timing_points = list(map(TimingPoint, self.timing_points)) if self.timing_points is not None else None
        self.colours = Colours(self.colours) if self.colours is not None else None
        self.hit_objects = list(map(lambda data: HitObject(self, data), self.hit_objects)) if self.hit_objects is not None else None

    @property
    def path(self):
        return self.reader.path

    def __iter__(self):
        return iter(self.hit_objects)


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

    def __iter__(self):
        return iter(self.beatmaps)


class SongsFolder:
    def __init__(self, reader: SongsReader):
        self.reader = reader
        self.reader.discover_all_beatmapsets()
        self.reader.cast_beatmapset_readers(Beatmapset)

    @classmethod
    def from_path(cls, path=None, confirmation_function=None):
        path = path
        if path is None:
            print("Searching for osu! songs folder...")
            args = [confirmation_function] if confirmation_function is not None else []
            path = search_for_songs_folder(*args)
            if path is None:
                raise Exception("Bruh")  # TODO: b3uofqwfeniOGUWgbeuW
        return cls(SongsReader(path))

    @property
    def beatmapsets(self) -> Sequence[Beatmapset]:
        return self.reader.beatmapsets

    @property
    def path(self):
        return self.reader.path

    def __iter__(self):
        return iter(self.beatmapsets)
