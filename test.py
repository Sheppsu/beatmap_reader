from beatmap_reader import SongsFolder, HitObjectType, CurveType
import pygame


songs = "C:\\Users\\Sheep\\Desktop\\osu!\\Songs"


folder = SongsFolder.from_path(songs)
if not folder.beatmapsets:
    print("No beatmapsets in the songs folder. Is this an error with the program?")
    quit()


def get_sliders():
    sliders = []
    slider_check = {
        CurveType.PERFECT: False,
        CurveType.BEZIER: False,
        CurveType.CATMULL: False,
        CurveType.LINEAR: False,
    }

    for beatmapset in folder:
        if not beatmapset.beatmaps:
            print(f"Beatmapset {beatmapset.path} has no beatmaps. This is an error with the program.")
            break
        for beatmap in beatmapset:
            beatmap.load()
            for obj in beatmap.hit_objects:
                if obj.type == HitObjectType.SLIDER and not slider_check[obj.curve.type]:
                    sliders.append(obj)
                    slider_check[obj.curve.type] = True
                    print(f"Using {obj.curve.type} slider from {beatmap.path}")
                if all(slider_check.values()):
                    return sliders

    raise Exception("Could not find a slider of each type.")


def is_implemented(slider):
    try:
        slider.curve.create_curve_functions()
    except NotImplementedError:
        return False
    return True


sliders = get_sliders()
sliders = [slider for slider in sliders if is_implemented(slider)]
for slider in sliders:
    slider.render()


pygame.init()
screen = pygame.display.set_mode((640, 480))
clock = pygame.time.Clock()

draw_points = True
draw_sliders = {
    CurveType.PERFECT: True,
    CurveType.BEZIER: True,
    CurveType.CATMULL: True,
    CurveType.LINEAR: True,
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
                slider_type = list(draw_sliders.keys())[slider_keys.index(event.key)]
                draw_sliders[slider_type] = not draw_sliders[slider_type]

    screen.fill((0, 0, 0))

    for slider in sliders:
        if not draw_sliders[slider.curve.type]:
            continue
        screen.blit(slider.surf, (0, 0))
        if draw_points:
            for point in slider.curve.points:
                pygame.draw.circle(screen, (255, 255, 255), (point[0]+64, point[1]+48), 2)

    pygame.display.update()
    clock.tick(60)
