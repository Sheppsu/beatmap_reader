from osu import Mods
from beatmap_reader import SongsFolder


songs = SongsFolder.from_path("C:\\Users\\Sheep\\Desktop\\osu!\\Songs")

print(len(songs.beatmapsets))
beatmapset = songs.beatmapsets[2029]
beatmap = beatmapset.beatmaps[0]
print(beatmap.path)
if not beatmap.load():
    quit()


nomod = beatmap.get_difficulty_attributes()
print(f"No mod: {nomod.star_rating} {nomod.aim_strain} {nomod.speed_strain} "
      f"{nomod.flashlight_rating} {nomod.slider_factor}")

difficulty = []
for mod in (Mods.HardRock, Mods.DoubleTime, Mods.Easy, Mods.HalfTime, Mods.Flashlight):
    difficulty.append(beatmap.get_difficulty_attributes(mod))

for diff in difficulty:
    print(diff.mods, diff.star_rating, diff.aim_strain, diff.speed_strain,
          diff.flashlight_rating, diff.slider_factor)
