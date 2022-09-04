import struct
from enum import IntEnum
from .enums import GameMode, Mods
from typing import Union, ByteString


class VersionChanges:
    ENTRY_LENGTH_MIN = 20160408
    ENTRY_LENGTH_MAX = 20191107
    FLOAT_DIFFICULTY_VALUES = 20140609
    FIRST_OSZ_2 = 20121008
    REPLAY_SCORE_ID_64BIT = 20140721


class ByteType(IntEnum):
    NULL = 0
    BOOL = 1
    UBYTE = 2
    USHORT = 3
    UINT = 4
    ULONG = 5
    SBYTE = 6
    SHORT = 7
    INT = 8
    LONG = 9
    CHAR = 10
    STRING = 11
    FLOAT = 12
    DOUBLE = 13
    DECIMAL = 14
    DATE_TIME = 15
    BYTES = 16
    CHARS = 17
    UNKNOWN = 18
    SERIALIZABLE = 19


class Buffer:
    def __init__(self, data):
        self.data = data
        self.offset = 0

    def _read(self, fmt, size):
        data = struct.unpack(fmt, self.data[self.offset:self.offset+size])[0]
        self.offset += size
        return data

    def _read_raw(self, size):
        data = self.data[self.offset:self.offset+size]
        self.offset += size
        return data

    def read_raw_bytes(self, size):
        return self._read_raw(size)

    def read_sbyte(self):
        return self._read("<b", 1)

    def read_ubyte(self):
        return self._read("<B", 1)

    def read_bool(self):
        return bool(self.read_ubyte())

    def read_char(self):
        return self._read("<c", 1)

    def read_short(self):
        return self._read("<h", 2)

    def read_ushort(self):
        return self._read("<H", 2)

    def read_int(self):
        return self._read("<i", 4)

    def read_uint(self):
        return self._read("<I", 4)

    def read_long(self):
        return self._read("<q", 8)

    def read_ulong(self):
        return self._read("<Q", 8)

    def read_float(self):
        return self._read("<f", 4)

    def read_double(self):
        return self._read("<d", 8)

    def read_byte_array(self):
        length = self.read_int()
        return self.read_raw_bytes(length) if length > 0 else None

    def _read_chars(self, length):
        return self.read_raw_bytes(length).decode('utf-8')

    def read_chars(self):
        length = self.read_int()
        return self._read_chars(length) if length > 0 else None

    def read_ulb128(self):
        result = 0
        shift = 0
        while True:
            byte = self.read_ubyte()
            result |= (byte & 0b01111111) << shift
            if (byte & 0b10000000) == 0x00:
                break
            shift += 7
        return result

    def read_string(self):
        if self.read_ubyte() != 0x0B:
            return
        length = self.read_ulb128()
        return self.read_raw_bytes(length).decode('utf-8')

    def read_date_time(self):
        return self._read("<q", 8)

    def read_object(self):
        obj_type = ByteType(self.read_ubyte())
        if obj_type == ByteType.NULL:
            return
        if obj_type == ByteType.UNKNOWN or obj_type == ByteType.SERIALIZABLE:
            raise NotImplementedError()
        return getattr(self, "read_"+obj_type.name.lower(), lambda: None)()

    def read_dictionary(self, key_map=lambda x: x, value_map=lambda x: x):
        return {key_map(self.read_object()): value_map(self.read_object()) for _ in range(self.read_int())}

    def read_timing_point(self):
        bpm = self.read_double()
        offset = self.read_double()
        inherited = self.read_bool()
        return bpm, offset, inherited


class OsuCache:
    __slots__ = ("version", "folder_count", "account_unlocked", "account_unlocked_date", "name", "beatmaps")

    def __init__(self):
        self.version = None
        self.folder_count = None
        self.account_unlocked = None
        self.account_unlocked_date = None
        self.name = None
        self.beatmaps = []

    @classmethod
    def from_path(cls, path):
        with open(path, "rb") as f:
            return cls.from_buffer(f.read())

    @classmethod
    def from_buffer(cls, buffer: Union[ByteString, Buffer]):
        if not isinstance(buffer, Buffer):
            buffer = Buffer(buffer)
        cache = cls()

        cache.version = buffer.read_uint()
        cache.folder_count = buffer.read_uint()
        cache.account_unlocked = buffer.read_bool()
        cache.account_unlocked_date = buffer.read_date_time()
        cache.name = buffer.read_string()
        beatmap_count = buffer.read_uint()
        for _ in range(beatmap_count):
            cache.beatmaps.append(BeatmapCache.from_buffer(buffer, cache.version))
        return cache


class BeatmapCache:
    __slots__ = (
        "artist", "artist_unicode", "title", "title_unicode", "mapper", "difficulty", "audio_file",
        "md5_hash", "map_file", "ranked_status", "num_hitcircles", "num_sliders", "num_spinners",
        "last_modified", "approach_rate", "circle_size", "hp_drain", "overall_difficulty", "slider_velocity",
        "diff_star_rating_standard", "diff_star_rating_taiko", "diff_star_rating_ctb", "diff_star_rating_mania",
        "drain_time", "total_time", "preview_time", "timing_points", "beatmap_id", "beatmapset_id", "thread_id",
        "grade_standard", "grade_taiko", "grade_ctb", "grade_mania", "local_offset", "stack_leniency",
        "gameplay_mode", "song_source", "song_tags", "online_offset", "font", "is_unplayed", "last_played",
        "is_osz2", "folder_name", "last_check_against_osu_repo", "ignore_beatmap_sounds", "ignore_beatmap_skin",
        "disable_storyboard", "disable_video", "visual_override", "old_unknown1", "last_edit_time",
        "mania_scroll_speed"
    )

    def __init__(self):
        for slot in self.__slots__:
            setattr(self, slot, None)

    @classmethod
    def from_buffer(cls, buffer: Union[ByteString, Buffer], version):
        if not isinstance(buffer, Buffer):
            buffer = Buffer(buffer)
        cache = cls()

        if VersionChanges.ENTRY_LENGTH_MIN <= version < VersionChanges.ENTRY_LENGTH_MAX:
            buffer.read_uint()
        cache.artist = buffer.read_string()
        if version >= VersionChanges.FIRST_OSZ_2:
            cache.artist_unicode = buffer.read_string()
        cache.title = buffer.read_string()
        if version >= VersionChanges.FIRST_OSZ_2:
            cache.title_unicode = buffer.read_string()
        cache.mapper = buffer.read_string()
        cache.difficulty = buffer.read_string()
        cache.audio_file = buffer.read_string()
        cache.md5_hash = buffer.read_string()
        cache.map_file = buffer.read_string()
        cache.ranked_status = buffer.read_ubyte()
        cache.num_hitcircles = buffer.read_ushort()
        cache.num_sliders = buffer.read_ushort()
        cache.num_spinners = buffer.read_ushort()
        cache.last_modified = buffer.read_date_time()
        if version >= VersionChanges.FLOAT_DIFFICULTY_VALUES:
            cache.approach_rate = buffer.read_float()
            cache.circle_size = buffer.read_float()
            cache.hp_drain = buffer.read_float()
            cache.overall_difficulty = buffer.read_float()
        else:
            cache.approach_rate = buffer.read_ubyte()
            cache.circle_size = buffer.read_ubyte()
            cache.hp_drain = buffer.read_ubyte()
            cache.overall_difficulty = buffer.read_ubyte()
        cache.slider_velocity = buffer.read_double()
        if version >= VersionChanges.FLOAT_DIFFICULTY_VALUES:
            cache.diff_star_rating_standard = buffer.read_dictionary(Mods)
            cache.diff_star_rating_taiko = buffer.read_dictionary(Mods)
            cache.diff_star_rating_ctb = buffer.read_dictionary(Mods)
            cache.diff_star_rating_mania = buffer.read_dictionary(Mods)
        cache.drain_time = buffer.read_uint()
        cache.total_time = buffer.read_uint()
        cache.preview_time = buffer.read_uint()
        cache.timing_points = []
        for _ in range(buffer.read_uint()):
            cache.timing_points.append(buffer.read_timing_point())
        cache.beatmap_id = buffer.read_uint()
        cache.beatmapset_id = buffer.read_uint()
        cache.thread_id = buffer.read_uint()
        cache.grade_standard = buffer.read_ubyte()
        cache.grade_taiko = buffer.read_ubyte()
        cache.grade_ctb = buffer.read_ubyte()
        cache.grade_mania = buffer.read_ubyte()
        cache.local_offset = buffer.read_short()
        cache.stack_leniency = buffer.read_float()
        cache.gameplay_mode = GameMode(buffer.read_ubyte())
        cache.song_source = buffer.read_string()
        cache.song_tags = buffer.read_string()
        cache.online_offset = buffer.read_short()
        cache.font = buffer.read_string()
        cache.is_unplayed = buffer.read_bool()
        cache.last_played = buffer.read_date_time()
        cache.is_osz2 = buffer.read_bool()
        cache.folder_name = buffer.read_string()
        cache.last_check_against_osu_repo = buffer.read_date_time()
        cache.ignore_beatmap_sounds = buffer.read_bool()
        cache.ignore_beatmap_skin = buffer.read_bool()
        cache.disable_storyboard = buffer.read_bool()
        cache.disable_video = buffer.read_bool()
        cache.visual_override = buffer.read_bool()
        if version < VersionChanges.FLOAT_DIFFICULTY_VALUES:
            cache.old_unknown1 = buffer.read_short()
        cache.last_edit_time = buffer.read_int()
        cache.mania_scroll_speed = buffer.read_ubyte()
        return cache
