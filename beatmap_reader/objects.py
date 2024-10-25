from .read import SongsReader, BeatmapsetReader, BeatmapReader
from .util import search_for_songs_folder, get_sample_set
from .enums import *
from .hit_objects import (
    get_hit_object,
    HitObjectBase,
    HitCircle,
    Slider,
    Spinner,
    ManiaHoldKey
)
from typing import Sequence, Union
import os
import traceback


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
        "approach_rate", "slider_multiplier", "slider_tick_rate",
        "_hp_drain_rate", "_circle_size", "_overall_difficulty",
        "_approach_rate"
    )

    def __init__(self, data):
        self._hp_drain_rate = float(data["HPDrainRate"])
        self.hp_drain_rate = self._hp_drain_rate
        self._circle_size = float(data["CircleSize"])
        self.circle_size = self._circle_size
        self._overall_difficulty = float(data["OverallDifficulty"])
        self.overall_difficulty = self._overall_difficulty
        self._approach_rate = float(data.get("ApproachRate", self.overall_difficulty))
        self.approach_rate = self._approach_rate
        self.slider_multiplier = float(data["SliderMultiplier"])
        self.slider_tick_rate = float(data["SliderTickRate"])

    def reset_mods(self):
        self.hp_drain_rate = self._hp_drain_rate
        self.circle_size = self._circle_size
        self.overall_difficulty = self._overall_difficulty
        self.approach_rate = self._approach_rate

    def apply_mods(self, mods: Mods):
        if Mods.HardRock in mods:
            self.hp_drain_rate = min(self._hp_drain_rate * 1.4, 10)
            self.circle_size = min(self._circle_size * 1.3, 10)
            self.overall_difficulty = min(self._overall_difficulty * 1.4, 10)
            self.approach_rate = min(self._approach_rate * 1.4, 10)
        if Mods.Easy in mods:
            self.hp_drain_rate = max(self._hp_drain_rate * 0.5, 0)
            self.circle_size = max(self._circle_size * 0.5, 0)
            self.overall_difficulty = max(self._overall_difficulty * 0.5, 0)
            self.approach_rate = max(self._approach_rate * 0.5, 0)
        # TODO: DT and HT


class Events:
    pass


class Effects:
    __slots__ = ("is_kiai_enabled", "is_first_barline_omitted")

    def __init__(self, effects):
        self.is_kiai_enabled = bool(effects & (1 << 0))
        self.is_first_barline_omitted = bool(effects & (1 << 3))


class UninheritedTimingPoint:
    __slots__ = ("time", "beat_duration", "meter", "sample_set", "sample_index", "volume", "effects")
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
    __slots__ = ("time", "parent_timing_point", "slider_velocity", "sample_set", "sample_index", "volume", "effects")
    type = TimingPointType.INHERITED

    def __init__(self, time, slider_velocity, sample_set,
                 sample_index, volume, effects):
        self.time = time
        self.parent_timing_point = None
        self.slider_velocity = 1/(-slider_velocity/100)
        self.sample_set = sample_set
        self.sample_index = sample_index
        self.volume = volume
        self.effects = Effects(effects) if effects is not None else None


class TimingPoint:
    def __new__(cls, string) -> Union[InheritedTimingPoint, UninheritedTimingPoint]:
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
    __slots__ = ("int_colour",)

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
    __slots__ = ("combo_colours", "slider_track_override", "slider_border")

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
    __slots__ = (
        "reader", "version", "general", "editor", "metadata", "difficulty",
        "events", "timing_points", "colours", "hit_objects", "fully_loaded",
        "max_combo", "hit_circle_count", "slider_count", "spinner_count"
    )
    STACK_DISTANCE = 3

    def __init__(self, reader: BeatmapReader):
        self.reader = reader
        self.version: Union[int, None] = None
        self.general: Union[General, dict, None] = None
        self.editor: Union[Editor, dict, None] = None
        self.metadata: Union[Metadata, dict, None] = None
        self.difficulty: Union[Difficulty, dict, None] = None
        self.events: Union[Events, dict, None] = None
        self.timing_points: Union[Sequence[Union[InheritedTimingPoint, UninheritedTimingPoint]], dict, None] = None
        self.colours: Union[Colours, dict, None] = None
        self.hit_objects: Union[Sequence[Union[HitCircle, Slider, Spinner, ManiaHoldKey]], dict, None] = None

        self.max_combo = None
        self.hit_circle_count = None
        self.slider_count = None
        self.spinner_count = None

        self.fully_loaded = False

    @classmethod
    def from_path(cls, path):
        return cls(BeatmapReader(path))

    def load(self):
        try:
            data = self.reader.load_beatmap_data()
        except:
            print(f"There was a problem while loading the data in {self.reader.path}\n{traceback.format_exc()}")
            return False
        if 'version' not in data:
            print(f"There was a problem while trying to identify the version of {self.reader.path}")
            return False
        self.version = data["version"]
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
            return True
        except:
            print(f"There was a problem while formatting the data in {self.reader.path}\n{traceback.format_exc()}")
            return False

    def _format_data(self):
        self.general = General(self.reader.path, self.general) if self.general is not None else None
        self.editor = Editor(self.editor) if self.editor is not None else None
        self.metadata = Metadata(self.metadata) if self.metadata is not None else None
        self.difficulty = Difficulty(self.difficulty) if self.difficulty is not None else None
        self.timing_points = sorted(
            list(map(TimingPoint, self.timing_points)),
            key=lambda timing: timing.time) \
            if self.timing_points is not None else None
        self._set_parent_timing_points()
        self.colours = Colours(self.colours) if self.colours is not None else None
        self.hit_objects = sorted(
            list(map(
                lambda data: get_hit_object(self, data[1], data[0]),
                enumerate(self.hit_objects))),
            key=lambda obj: obj.time) \
            if self.hit_objects is not None else None

        self._set_timing_points()
        for hit_object in filter(lambda obj: obj.type == HitObjectType.SLIDER, self.hit_objects):
            hit_object.calculate_time_attributes()
        self.hit_circle_count, self.slider_count, self.spinner_count = self._calculate_object_amounts()
        self.fully_loaded = True

    def load_slider_paths(self):
        for hit_object in filter(lambda obj: obj.type == HitObjectType.SLIDER, self.hit_objects):
            hit_object.calculate_path()

    def load_slider_nested_objects(self):
        for hit_object in filter(lambda obj: obj.type == HitObjectType.SLIDER, self.hit_objects):
            hit_object.create_nested_objects()

    def load_objects(self):
        self.load_slider_paths()
        self.apply_stacking()
        self.load_slider_nested_objects()
        self.max_combo = self._calculate_max_combo()

    def apply_stacking(self):
        if self.version >= 6:
            self._apply_stacking(0, len(self.hit_objects) - 1)
        else:
            self._apply_stacking_old()

    def _apply_stacking(self, start_index, end_index):
        extended_end_index = end_index

        if end_index < len(self.hit_objects) - 1:
            for i in reversed(range(start_index, end_index+1)):
                stack_base_index = i

                for n in range(stack_base_index+1, len(self.hit_objects)):
                    stack_base_obj = self.hit_objects[stack_base_index]
                    if stack_base_obj.type == HitObjectType.SPINNER:
                        break

                    object_n = self.hit_objects[n]
                    if object_n.type == HitObjectType.SPINNER:
                        continue

                    end_time = stack_base_obj.end_time
                    stack_threshold = object_n.time_preempt * self.general.stack_leniency

                    if object_n.time - end_time > stack_threshold:
                        break

                    if stack_base_obj.position.distance_to(object_n.position) < self.STACK_DISTANCE or \
                            (stack_base_obj.type == HitObjectType.SLIDER and
                             stack_base_obj.end_position.distance_to(object_n.position) < self.STACK_DISTANCE):
                        stack_base_index = n
                        object_n.stack_height = 0

                if stack_base_index > extended_end_index:
                    extended_end_index = stack_base_index
                    if extended_end_index == len(self.hit_objects) - 1:
                        break

        extended_start_index = start_index

        for i in reversed(range(start_index+1, extended_end_index+1)):
            n = i

            object_i = self.hit_objects[i]
            if object_i.stack_height != 0 or object_i.type == HitObjectType.SPINNER:
                continue

            stack_threshold = object_i.time_preempt * self.general.stack_leniency

            if object_i.type == HitObjectType.HITCIRCLE:
                while n-1 >= 0:
                    n -= 1
                    object_n = self.hit_objects[n]
                    if object_n.type == HitObjectType.SPINNER:
                        continue

                    end_time = object_n.end_time

                    if object_i.time - end_time > stack_threshold:
                        break

                    if n < extended_start_index:
                        object_n.stack_height = 0
                        extended_start_index = n

                    if object_n.type == HitObjectType.SLIDER and object_n.end_position.distance_to(object_i.position) < self.STACK_DISTANCE:
                        offset = object_i.stack_height - object_n.stack_height + 1

                        for j in range(n+1, i+1):
                            object_j = self.hit_objects[j]
                            if object_n.end_position.distance_to(object_j.position) < self.STACK_DISTANCE:
                                object_j.stack_height -= offset

                        break

                    if object_n.position.distance_to(object_i.position) < self.STACK_DISTANCE:
                        object_n.stack_height = object_i.stack_height + 1
                        object_i = object_n
            elif object_i.type == HitObjectType.SLIDER:
                while n-1 >= start_index:
                    n -= 1
                    object_n = self.hit_objects[n]
                    if object_n.type == HitObjectType.SPINNER:
                        continue

                    if object_i.time - object_n.time > stack_threshold:
                        break

                    if object_n.end_position.distance_to(object_i.position) < self.STACK_DISTANCE:
                        object_n.stack_height = object_i.stack_height + 1
                        object_i = object_n

    def _apply_stacking_old(self):
        for i in range(len(self.hit_objects)):
            curr_hit_object = self.hit_objects[i]

            if curr_hit_object.stack_height != 0 and curr_hit_object.type != HitObjectType.SLIDER:
                continue

            start_time = curr_hit_object.end_time
            slider_stack = 0

            for j in range(i+1, len(self.hit_objects)):
                stack_threshold = self.hit_objects[i].time_preempt * self.general.stack_leniency

                if self.hit_objects[j].time - stack_threshold > start_time:
                    break

                position2 = curr_hit_object.position + curr_hit_object.position_at_path_progress(1) \
                    if curr_hit_object.type == HitObjectType.SLIDER else curr_hit_object.position

                if self.hit_objects[j].position.distance_to(curr_hit_object.position) < self.STACK_DISTANCE:
                    curr_hit_object.stack_height += 1
                    start_time = self.hit_objects[j].end_time
                elif self.hit_objects[j].position.distance_to(position2) < self.STACK_DISTANCE:
                    slider_stack += 1
                    self.hit_objects[j].stack_height -= slider_stack
                    start_time = self.hit_objects[j].end_time

    def _calculate_max_combo(self):
        combo = 0
        for hit_object in self.hit_objects:
            combo += len(hit_object.nested_objects) if hit_object.type == HitObjectType.SLIDER else 1
        return combo

    def _calculate_object_amounts(self):
        hit_circles_count = 0
        slider_count = 0
        spinner_count = 0
        for ho in self.hit_objects:
            if ho.type == HitObjectType.HITCIRCLE:
                hit_circles_count += 1
            elif ho.type == HitObjectType.SLIDER:
                slider_count += 1
            elif ho.type == HitObjectType.SPINNER:
                spinner_count += 1
        return hit_circles_count, slider_count, spinner_count

    def _set_parent_timing_points(self):
        if self.timing_points is not None:
            parent = None
            for timing_point in self.timing_points:
                if timing_point.type == TimingPointType.UNINHERITED:
                    parent = timing_point
                else:
                    timing_point.parent_timing_point = parent

    def _set_timing_points(self):
        timing_i = 0
        obj_i = 0
        while obj_i < len(self.hit_objects):
            offset = 0
            while timing_i + offset < len(self.timing_points) and \
                    self.hit_objects[obj_i].time >= self.timing_points[timing_i + offset].time:
                offset += 1
            timing_i = max(timing_i + offset - 1, 0)
            if self.timing_points[timing_i].type == TimingPointType.UNINHERITED:
                self.hit_objects[obj_i].ui_timing_point = self.timing_points[timing_i]
            else:
                self.hit_objects[obj_i].ui_timing_point = self.timing_points[timing_i].parent_timing_point
                self.hit_objects[obj_i].i_timing_point = self.timing_points[timing_i]
            obj_i += 1

    def apply_mods(self, mods: Mods):
        if type(self.difficulty) != Difficulty:
            raise TypeError("difficulty attribute is not formatted properly and so mods cannot be applied to it.")
        if len(self.hit_objects) > 0 and not all(map(lambda ho: isinstance(ho, HitObjectBase), self.hit_objects)):
            raise TypeError("hit_objects is not formatted properly and so mods cannot be applied to it.")
        self.difficulty.reset_mods()
        if mods is not None:
            self.difficulty.apply_mods(mods)
        for hit_object in self.hit_objects:
            hit_object.on_difficulty_change()

    @property
    def path(self):
        return self.reader.path

    def __iter__(self):
        return iter(self.hit_objects)


class Beatmapset:
    __slots__ = ("reader",)

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

    def __getitem__(self, index):
        return self.beatmaps[index]

    def __iter__(self):
        return iter(self.beatmaps)


class SongsFolder:
    __slots__ = ("reader",)

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

    def __getitem__(self, index):
        return self.beatmapsets[index]

    def __iter__(self):
        return iter(self.beatmapsets)
