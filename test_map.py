from beatmap_reader import Beatmap


songs = "C:\\Users\\Sheep\\Desktop\\osu!\\Songs"


beatmap = Beatmap.from_path("C:\\Users\\Sheep\\Desktop\\osu!\\Songs\\829629 antiPLUR - Runengon\\antiPLUR - Runengon (Yusomi) [ar10].osu")
beatmap.load()
