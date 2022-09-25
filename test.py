from beatmap_reader import SongsFolder, HitObjectType, CurveType
import pygame
import random


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
    if catmullmap is None:
        raise Exception("catmullmap not found")

    for beatmapset in [catmullmap] + beatmapsets:
        if not beatmapset.beatmaps:
            print(f"Beatmapset {beatmapset.path} has no beatmaps. This is an error with the program.")
            break
        for beatmap in beatmapset:
            beatmap.load()
            if beatmap.hit_objects is None:
                continue
            for obj in beatmap.hit_objects:
                if obj.type == HitObjectType.SLIDER and len(sliders[obj.curve.type]) < 5:
                    sliders[obj.curve.type].append(obj)
                    print(obj.end_time)
                    print(f"Using {obj.curve.type.name} slider from {beatmap.path}")
                    if all(map(lambda l: len(l) == 5, sliders.values())):
                        return sliders

    raise Exception("Could not find a slider of each type.")


sliders = get_sliders()
tick = pygame.Surface((10, 10))
tick.fill((255, 255, 255))
for slider_list in sliders.values():
    for slider in slider_list:
        slider.render((640, 480), (64, 48), color=(0, 255, 0), border_color=(0, 0, 255), tick_surf=tick)


pygame.init()
screen = pygame.display.set_mode((640, 480))
clock = pygame.time.Clock()

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
        slider = sliders[slider_type][i]
        screen.blit(slider.surf, (0, 0))
        if draw_points:
            for point in slider.curve.points:
                pygame.draw.circle(screen, (255, 0, 0), (point[0]+64, point[1]+48), 2)

    pygame.display.update()
    clock.tick(60)
