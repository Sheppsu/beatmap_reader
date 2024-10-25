from beatmap_reader import Beatmap


path_to_osu_file = "..."


beatmap = Beatmap.from_path(path_to_osu_file)
beatmap.load()  # load data from file
beatmap.load_objects()  # calculate slider paths, stacking, and max combo
