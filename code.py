import time
import board
# from my_pyportal import PyPortal
import adafruit_touchscreen
import displayio
import gc
import board
from fractals import LinearColorMapper, FractalViewer, Complex, mandelbrot_fractal, burning_ship_fractal

touchscreen = adafruit_touchscreen.Touchscreen(board.TOUCH_XL, board.TOUCH_XR,
                                                            board.TOUCH_YD, board.TOUCH_YU,
                                                            calibration=((5200, 59000),
                                                                         (5800, 57000)),
                                                            size=(320, 240))
splash = displayio.Group(max_size=15)
_bg_group = displayio.Group(max_size=1)
_bg_file = None
_default_bg = 0x000000
splash.append(_bg_group)

board.DISPLAY.show(splash)

# the current working directory (where this file is)
cwd = ("/"+__file__).rsplit('/', 1)[0]
# pyportal = PyPortal(status_neopixel=board.NEOPIXEL,
#                     debug=True)


def set_background(bitmap, color_palette, position=None):
    """The background image to a bitmap file.
    :param file_or_color: The filename of the chosen background image, or a hex color.
    """
    global _bg_file
    print("Set background to ", bitmap)
    while _bg_group:
        _bg_group.pop()

    if not position:
        position = (0, 0)  # default in top corner

    if not bitmap:
        return  # we're done, no background desired
    if _bg_file:
        _bg_file.close()

    try:
        _bg_sprite = displayio.TileGrid(bitmap,
                                             pixel_shader=color_palette,
                                             position=(0, 0))
    except TypeError:
        _bg_sprite = displayio.TileGrid(bitmap,
                                             pixel_shader=color_palette,
                                             x=position[0], y=position[1])

    _bg_group.append(_bg_sprite)
    board.DISPLAY.refresh_soon()
    gc.collect()
    board.DISPLAY.wait_for_frame()


def get_next_color(r, g, b, step=5):
    def clip(v):
        return min(max(v, 0), 255)

    if r == 255 and g < 255 and b == 0:
        r, g, b = r, g + step, b
    elif g == 255 and r > 0:
        r, g, b = r - step, g, b
    elif g == 255 and b < 255:
        r, g, b = r, g, b + step
    elif b == 255 and g > 0:
        r, g, b = r, g - step, b
    elif b == 255 and r < 255:
        r, g, b = r + step, g, b
    elif r == 255 and b > 0:
        r, g, b = r, g, b - step

    return clip(r), clip(g), clip(b)


def wait_for_touch(touchscreen, min_pts=15):
    max_len = 10 * min_pts

    pts = []
    while True:
        touchpoint = touchscreen.touch_point

        if touchpoint:
            pts.append(touchpoint)
            if len(pts) > max_len:
                pts = pts[-max_len:]
        elif len(pts) >= min_pts:
            xs, ys, zs = zip(*pts)
            return sum(xs) // len(xs), sum(ys) // len(ys), sum(zs) // len(zs)
        else:
            pts = []


max_iter = 16
num_colors_to_use = 16

colors = [(255, 0, 0)]

while len(colors) < num_colors_to_use:
	colors.append(get_next_color(*colors[-1], step=75))

def rgb_to_int(r, g, b):
	return r * 256 ** 2 + g * 256 + b

colors = [rgb_to_int(*c) for c in colors]

# fractal = burning_ship_fractal
fractal = mandelbrot_fractal
color_mapper = LinearColorMapper(colors)
fractal_viewer = FractalViewer(color_mapper, max_iter, pix_sz=(120, 90), fractal=fractal)

while True:
    set_background(fractal_viewer.bitmap, color_mapper.palette)
    while fractal_viewer.has_computation_left():
        fractal_viewer.step()
        set_background(fractal_viewer.bitmap, color_mapper.palette)

    touch_x, touch_y, _ = wait_for_touch(touchscreen)

    # touch_cmp = fractal_viewer.pix_to_cmp((touch_x, touch_y))
    # cmp_bounds_x, cmp_bounds_y = fractal_viewer.cmp_bounds

    # cmp_bounds_x_rng = (cmp_bounds_x[1] - cmp_bounds_x[0]) / 4
    # cmp_bounds_y_rng = (cmp_bounds_y[1] - cmp_bounds_y[0]) / 4
    
    # fractal_viewer = FractalViewer(color_mapper, max_iter, pix_sz=fractal_viewer.pix_sz, 
    #     cmp_bounds=((touch_cmp.r - cmp_bounds_x_rng, touch_cmp.r + cmp_bounds_x_rng), 
    #                 (touch_cmp.c - cmp_bounds_y_rng, touch_cmp.c + cmp_bounds_y_rng)), 
    #     fractal=fractal)

    fractal_viewer.register_click((touch_x, touch_y))

