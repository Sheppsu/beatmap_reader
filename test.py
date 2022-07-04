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
colors = [
    (255, 0, 0),
    (0, 255, 0),
    (0, 0, 255),
    (255, 0, 255),
]


pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

draw_points = True
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                draw_points = not draw_points

    screen.fill((0, 0, 0))

    for i in range(len(sliders)):
        pygame.draw.lines(screen, colors[i % len(colors)], False, sliders[i].curve.curve_points[0], 1)
        pygame.draw.lines(screen, colors[i % len(colors)], False, sliders[i].curve.curve_points[1], 1)
        pygame.draw.circle(screen, colors[i], (sliders[i].x, sliders[i].y), sliders[i].curve.radius_offset)
        pygame.draw.circle(screen, colors[i], tuple(sliders[i].curve.points[-1]), sliders[i].curve.radius_offset)
        if draw_points:
            for point in sliders[i].curve.points:
                pygame.draw.circle(screen, [255, 255, 0], tuple(point), 1)
            for points in sliders[i].curve.curve_points:
                for point in points:
                    pygame.draw.circle(screen, [0, 255, 255], tuple(point), 1)

    pygame.display.update()
    clock.tick(60)
