from beatmap_reader.cache import OsuCache


osu_db_path = "C:\\Users\\Sheep\\Desktop\\osu!\\osu!.db"
cache = OsuCache.from_path(osu_db_path)
print(cache.version)
print(cache.folder_count)
print(cache.account_unlocked)
print(cache.account_unlocked_date)
print(cache.name)
beatmaps = cache.beatmaps[0]
for attr in dir(beatmaps):
    if attr.startswith("__"):
        continue
    print(f"{attr}: {getattr(beatmaps, attr)}")
