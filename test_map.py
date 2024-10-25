from beatmap_reader import Beatmap


# beatmap = Beatmap.from_path("C:\\Users\\Sheeppsu\\Desktop\\osu!\\Songs\\829629 antiPLUR - Runengon\\antiPLUR - Runengon (Yusomi) [ar10].osu")
beatmap = Beatmap.from_path("C:\\Users\\Sheeppsu\\Desktop\\osu!\\Songs\\3 Ni-Ni - 1,2,3,4, 007 [Wipeout Series]\\Ni-Ni - 1,2,3,4, 007 [Wipeout Series] (MCXD) [-Breezin-].osu")
beatmap.load()  # load data from file
beatmap.load_objects()  # calculate slider paths, stacking, and max combo
