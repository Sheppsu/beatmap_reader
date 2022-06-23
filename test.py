from beatmap_reader import SongsFolder
import random


songs = "C:\\Users\\Sheep\\Desktop\\osu!\\Songs"


folder = SongsFolder.from_path(songs)
if not folder.beatmapsets:
    print("No beatmapsets in the songs folder. Is this an error with the program?")
    quit()
for beatmapset in folder:
    if not beatmapset.beatmaps:
        print(f"Beatmapset {beatmapset.path} has no beatmaps. This is an error with the program.")
        break
    for beatmap in beatmapset:
        beatmap.load()
