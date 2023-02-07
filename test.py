from beatmap_reader import SongsFolder, HitObjectType, CurveType, SliderEventType
import pygame
import random
import traceback


songs = "C:\\Users\\Sheep\\Desktop\\osu!\\Songs"


folder = SongsFolder.from_path(songs)
if not folder.beatmapsets:
    print("No beatmapsets in the songs folder. Is this an error with the program?")
    quit()


def get_sliders():
    sliders = {
        CurveType.PERFECT: [],
        CurveType.BEZIER: [],
        CurveType.CATMULL: [],
        CurveType.LINEAR: [],
    }

    beatmapsets = list(folder.beatmapsets)
    random.shuffle(beatmapsets)

    catmullmap = None
    for beatmapset in beatmapsets:
        if beatmapset.path.endswith("3 Ni-Ni - 1,2,3,4, 007 [Wipeout Series]"):
            catmullmap = beatmapset
            break
    if catmullmap is None:
        raise Exception("catmullmap not found")

    for beatmapset in [catmullmap] + beatmapsets:
        if not beatmapset.beatmaps:
            print(f"Beatmapset {beatmapset.path} has no beatmaps. This is an error with the program.")
            break
        for beatmap in beatmapset:
            beatmap.load()
            if beatmap.hit_objects is None or type(beatmap.hit_objects[0]) == str:
                continue
            for obj in beatmap.hit_objects:
                if obj.type == HitObjectType.SLIDER and len(sliders[obj.path.type]) < 5:
                    sliders[obj.path.type].append(obj)
                    print(f"Using {obj.path.type.name} slider ({obj.time}) from {beatmap.path}")
                    beatmap.load_sliders()
                    beatmap.apply_stacking()
                    if all(map(lambda l: len(l) == 5, sliders.values())):
                        return sliders

    raise Exception("Could not find a slider of each type.")


def render(slider, screen_size, placement_offset, osu_pixel_multiplier=1, color=(0, 0, 0),
           border_color=(255, 255, 255), border_thickness=1):
    format_point = lambda p1, p2: (p1 * osu_pixel_multiplier + placement_offset[0],
                                   p2 * osu_pixel_multiplier + placement_offset[1])
    surf = pygame.Surface(screen_size)
    surf.set_colorkey((0, 0, 0))
    try:
        size = slider.radius * osu_pixel_multiplier
        # Create base slider body and border
        for c, r in ((border_color, size), (color, size - border_thickness)):
            slider_length = slider.path.calculated_distance
            if slider_length == 0:
                path = [slider.stacked_position]
            else:
                path = [slider.position_at_path_progress(i/slider_length) for i in range(int(slider_length)+1)]
            for point in path:
                pygame.draw.circle(surf, c, format_point(*point),
                                   r)
    except:
        print(f"Error occurred while rendering slider at {slider.time} in {slider.parent.path}.")
        traceback.print_exc()
    return surf


sliders = get_sliders()
for curve, slider_list in sliders.items():
    sliders[curve] = list(map(
        lambda slider: (
            slider,
            render(slider, (640, 480), (64, 48), color=(0, 255, 0)),
        ),
        slider_list
    ))


pygame.init()
screen = pygame.display.set_mode((640, 480))
clock = pygame.time.Clock()

tick = pygame.Surface((10, 10))
tick.fill((255, 255, 255))

draw_points = True
slider_indexes = {
    CurveType.PERFECT: 0,
    CurveType.BEZIER: 0,
    CurveType.CATMULL: 0,
    CurveType.LINEAR: 0,
}


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
        if event.type == pygame.KEYDOWN:
            slider_keys = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]
            if event.key == pygame.K_p:
                draw_points = not draw_points
            if event.key in slider_keys:
                slider_type = list(slider_indexes.keys())[slider_keys.index(event.key)]
                slider_indexes[slider_type] = -1 if slider_indexes[slider_type] != -1 else 0
            if event.key in [pygame.K_LEFT, pygame.K_RIGHT]:
                slider_type = [type for type, i in slider_indexes.items() if i != -1]
                if not slider_type:
                    continue
                slider_type = slider_type[0]
                slider_indexes[slider_type] += 1 if event.key == pygame.K_RIGHT else -1
                if slider_indexes[slider_type] > 4:
                    slider_indexes[slider_type] = 0
                elif slider_indexes[slider_type] < 0:
                    slider_indexes[slider_type] = 4

    screen.fill((0, 0, 0))
    pygame.draw.rect(screen, (150, 150, 150), (64, 48, 512, 384), 3)

    for slider_type, i in slider_indexes.items():
        if i == -1:
            continue
        slider, surf = sliders[slider_type][i]
        screen.blit(surf, (0, 0))
        for slider_obj in filter(lambda obj: obj.type == SliderEventType.TICK, slider.nested_objects):
            pos = round(slider_obj.stacked_position)
            screen.blit(tick, (pos[0]+64-5, pos[1]+48-5))
        if draw_points:
            for point in slider.path.points:
                point = point.position
                pygame.draw.circle(screen, (255, 0, 0), (point[0]+64, point[1]+48), 2)

    pygame.display.update()
    clock.tick(60)
