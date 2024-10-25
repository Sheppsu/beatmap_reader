from beatmap_reader import Beatmap, HitObjectType, SliderEventType
import sys


beatmap = Beatmap.from_path(sys.argv[1])
beatmap.load()  # load data from file
beatmap.load_objects()  # calculate slider paths, stacking, and max combo

print(
    f"{beatmap.metadata.artist_unicode} - "
    f"{beatmap.metadata.title_unicode} "
    f"[{beatmap.metadata.version}] "
    f"mapped by {beatmap.metadata.creator}"
)

print(f"Has {len(beatmap.hit_objects)} objects")
print(f" - {beatmap.hit_circle_count} hit circles")
print(f" - {beatmap.slider_count} sliders")
print(f" - {beatmap.spinner_count} spinners")

slider_ticks = 0
for hit_object in beatmap.hit_objects:
    if hit_object.type == HitObjectType.SLIDER:
        for obj in hit_object.nested_objects:
            if obj.type == SliderEventType.TICK:
                slider_ticks += 1

print(f"Has {slider_ticks} slider ticks")
print(f"Max combo {beatmap.max_combo}")
