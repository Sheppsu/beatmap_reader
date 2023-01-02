import struct
from enum import IntEnum
from .enums import GameMode, Mods
from typing import Union, IO, Sequence


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
    def __init__(self, buf: IO):
        self.buf = buf

    def _read(self, fmt, size):
        data = struct.unpack(fmt, self.buf.read(size))[0]
        return data

    def _read_raw(self, size):
        data = self.buf.read(size)
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


class Collections:
    __slots__ = ("version", "collections")

    def __init__(self, collection_buffer: Union[IO, Buffer]):
        if not isinstance(collection_buffer, Buffer):
            collection_buffer = Buffer(collection_buffer)

        self.version = collection_buffer.read_uint()
        self.collections = [Collection(collection_buffer)
                            for _ in range(collection_buffer.read_uint())]

    def replace_beatmap_hashes(self, osu_cache: Union['OsuCache', IO, Buffer]):
        for collection in self.collections:
            collection.replace_beatmap_hashes(osu_cache)

    @classmethod
    def from_path(cls, path: str):
        with open(path, "rb") as f:
            return cls(f)


class Collection:
    __slots__ = ("name", "beatmaps")

    def __init__(self, collection_buffer: Union[IO, Buffer]):
        self.name = collection_buffer.read_string()
        self.beatmaps: Sequence[Union[str, BeatmapCache]] = [
            collection_buffer.read_string() for _ in range(collection_buffer.read_uint())]

    def replace_beatmap_hashes(self, osu_cache: Union['OsuCache', IO, Buffer]):
        if not isinstance(osu_cache, OsuCache):
            if not isinstance(osu_cache, Buffer):
                osu_cache = Buffer(osu_cache)
            osu_cache = OsuCache(osu_cache)
        self.beatmaps = [osu_cache.get_beatmap_from_hash(bm_hash) for bm_hash in self.beatmaps]


class OsuCache:
    __slots__ = (
        "version", "folder_count", "account_unlocked", "account_unlocked_date",
        "username", "beatmaps"
    )

    def __init__(self, buffer: Union[IO, Buffer]):
        if not isinstance(buffer, Buffer):
            buffer = Buffer(buffer)

        self.version = buffer.read_uint()
        self.folder_count = buffer.read_uint()
        self.account_unlocked = buffer.read_bool()
        self.account_unlocked_date = buffer.read_date_time()
        self.username = buffer.read_string()
        self.beatmaps = [BeatmapCache(buffer, self.version) for _ in range(buffer.read_uint())]

    @classmethod
    def from_path(cls, path: str):
        with open(path, "rb") as f:
            return cls(f)

    def get_beatmap_from_hash(self, md5_hash):
        for beatmap in self.beatmaps:
            if beatmap.md5_hash == md5_hash:
                return beatmap


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

    def __init__(self, buffer: Union[IO, Buffer], version):
        if not isinstance(buffer, Buffer):
            buffer = Buffer(buffer)

        if VersionChanges.ENTRY_LENGTH_MIN <= version < VersionChanges.ENTRY_LENGTH_MAX:
            buffer.read_uint()
        self.artist = buffer.read_string()
        if version >= VersionChanges.FIRST_OSZ_2:
            self.artist_unicode = buffer.read_string()
        self.title = buffer.read_string()
        if version >= VersionChanges.FIRST_OSZ_2:
            self.title_unicode = buffer.read_string()
        self.mapper = buffer.read_string()
        self.difficulty = buffer.read_string()
        self.audio_file = buffer.read_string()
        self.md5_hash = buffer.read_string()
        self.map_file = buffer.read_string()
        self.ranked_status = buffer.read_ubyte()
        self.num_hitcircles = buffer.read_ushort()
        self.num_sliders = buffer.read_ushort()
        self.num_spinners = buffer.read_ushort()
        self.last_modified = buffer.read_date_time()
        if version >= VersionChanges.FLOAT_DIFFICULTY_VALUES:
            self.approach_rate = buffer.read_float()
            self.circle_size = buffer.read_float()
            self.hp_drain = buffer.read_float()
            self.overall_difficulty = buffer.read_float()
        else:
            self.approach_rate = buffer.read_ubyte()
            self.circle_size = buffer.read_ubyte()
            self.hp_drain = buffer.read_ubyte()
            self.overall_difficulty = buffer.read_ubyte()
        self.slider_velocity = buffer.read_double()
        if version >= VersionChanges.FLOAT_DIFFICULTY_VALUES:
            self.diff_star_rating_standard = buffer.read_dictionary(Mods)
            self.diff_star_rating_taiko = buffer.read_dictionary(Mods)
            self.diff_star_rating_ctb = buffer.read_dictionary(Mods)
            self.diff_star_rating_mania = buffer.read_dictionary(Mods)
        self.drain_time = buffer.read_uint()
        self.total_time = buffer.read_uint()
        self.preview_time = buffer.read_uint()
        self.timing_points = []
        for _ in range(buffer.read_uint()):
            self.timing_points.append(buffer.read_timing_point())
        self.beatmap_id = buffer.read_uint()
        self.beatmapset_id = buffer.read_uint()
        self.thread_id = buffer.read_uint()
        self.grade_standard = buffer.read_ubyte()
        self.grade_taiko = buffer.read_ubyte()
        self.grade_ctb = buffer.read_ubyte()
        self.grade_mania = buffer.read_ubyte()
        self.local_offset = buffer.read_short()
        self.stack_leniency = buffer.read_float()
        self.gameplay_mode = GameMode(buffer.read_ubyte())
        self.song_source = buffer.read_string()
        self.song_tags = buffer.read_string()
        self.online_offset = buffer.read_short()
        self.font = buffer.read_string()
        self.is_unplayed = buffer.read_bool()
        self.last_played = buffer.read_date_time()
        self.is_osz2 = buffer.read_bool()
        self.folder_name = buffer.read_string()
        self.last_check_against_osu_repo = buffer.read_date_time()
        self.ignore_beatmap_sounds = buffer.read_bool()
        self.ignore_beatmap_skin = buffer.read_bool()
        self.disable_storyboard = buffer.read_bool()
        self.disable_video = buffer.read_bool()
        self.visual_override = buffer.read_bool()
        if version < VersionChanges.FLOAT_DIFFICULTY_VALUES:
            self.old_unknown1 = buffer.read_short()
        self.last_edit_time = buffer.read_int()
        self.mania_scroll_speed = buffer.read_ubyte()
