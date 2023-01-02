from beatmap_reader import OsuCache, Collections


osu_db_path = "C:\\Users\\Sheep\\Desktop\\osu!\\osu!.db"
osu_cache = OsuCache.from_path(osu_db_path)
collections = Collections.from_path("C:\\Users\\Sheep\\Desktop\\osu!\\collection.db")
collections.replace_beatmap_hashes(osu_cache)


def str_format(collection):
    if len(collection.beatmaps) == 0:
        return f"### {collection.name} ###\n\tNo beatmaps"
    return f"### {collection.name} ###\n\t{collection.beatmaps[0].artist} - {collection.beatmaps[0].title}\n\t..."


print("Collections:\n"+"\n".join([str_format(collection) for collection in collections.collections]))
