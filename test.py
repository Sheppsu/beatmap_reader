from beatmap_reader import SongsFolder
import random


songs = "C:\\Users\\Sheep\\Desktop\\osu!\\Songs"


folder = SongsFolder.from_path(songs)
assert folder.beatmapsets
beatmapset = random.choice(folder.beatmapsets)
assert beatmapset.beatmaps
beatmap = random.choice(beatmapset.beatmaps)
beatmap.load()
assert beatmap.data is not None
print(beatmap.data)
