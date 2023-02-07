from beatmap_reader import SongsFolder, Beatmap, HitObjectType, CurveType
from traceback import print_exc
from time import perf_counter


beatmap = Beatmap.from_path("C:\\Users\\Sheep\\Desktop\\osu!\\Songs\\889855 GALNERYUS - RAISE MY SWORD\\GALNERYUS - RAISE MY SWORD (Sotarks) [A THOUSAND FLAMES].osu")
print("Loading beatmap...")
t = perf_counter()
beatmap.load()
print(f"Beatmap load time: {perf_counter() - t}")
print("Loading sliders...")
t = perf_counter()
beatmap.load_sliders()
print(f"Slider load time: {perf_counter() - t}")
print("Applying stacking...")
t = perf_counter()
beatmap.apply_stacking()
print(f"Stacking apply time: {perf_counter() - t}")
print(f"All sliders have a calculated path: {all(map(lambda obj: len(obj.path.calculated_path) > 0, filter(lambda obj: obj.type == HitObjectType.SLIDER, beatmap)))}")


# print("Loading songs folder...")
# songs_folder = SongsFolder.from_path("C:\\Users\\Sheep\\Desktop\\osu!\\Songs")
# print("Iterating beatmapsets...")
# for beatmapset in songs_folder:
#     for beatmap in beatmapset:
#         print(f"Loading {beatmap.path}")
#         beatmap.load()
#         if not beatmap.fully_loaded:
#             quit()
#         for hit_object in filter(lambda obj: obj.type == HitObjectType.SLIDER, beatmap):
#             print(f"Calculating object {hit_object.time}")
#             try:
#                 hit_object.path.calculate()
#             except:
#                 print_exc()
#                 quit()
