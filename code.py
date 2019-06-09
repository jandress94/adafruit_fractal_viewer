
import adafruit_touchscreen
import displayio
import gc
import board
from adafruit_button import Button
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text.label import Label
from fractals import LinearColorMapper, FractalViewer, mandelbrot_fractal, burning_ship_fractal

cwd = ("/"+__file__).rsplit('/', 1)[0]

screen_size = (320, 240)
button_area_size = (100, screen_size[1])
fractal_area_size = (screen_size[0] - button_area_size[0], screen_size[1])
fractal_position = (button_area_size[0], 0)

touchscreen = adafruit_touchscreen.Touchscreen(board.TOUCH_XL, board.TOUCH_XR,
                                                            board.TOUCH_YD, board.TOUCH_YU,
                                                            calibration=((5200, 59000),
                                                                         (5800, 57000)),
                                                            size=screen_size)
splash = displayio.Group(max_size=15)
_bg_group = displayio.Group(max_size=1)
_default_bg = 0x000000
splash.append(_bg_group)
board.DISPLAY.show(splash)

font = bitmap_font.load_font(cwd+"/fonts/Arial-ItalicMT-17.bdf")

# setup the UI Elements
mandelbrot_button = Button(x=10, y=10, width=80, height=80, 
    style=Button.SHADOWROUNDRECT, fill_color=(255, 255, 255), 
    outline_color=0x222222, name="mandelbrot", label="Mandel...", label_font=font, selected_fill=(100, 100, 100))

ship_button = Button(x=10, y=100, width=80, height=80, 
    style=Button.SHADOWROUNDRECT, fill_color=(255, 255, 255), 
    outline_color=0x222222, name="ship", label="Ship", label_font=font, selected_fill=(100, 100, 100))

zoom_label = Label(font, text="Touch To\nZoom ->", line_spacing=1.1)
zoom_label.y = 210
zoom_label.x = 10
zoom_label.color = 0x000000


def flip_buttons(enabled):
    if enabled:
        mandelbrot_button.selected = False
        ship_button.selected = False
        zoom_label.color = 0xffffff
    else:
        mandelbrot_button.selected = True
        ship_button.selected = True
        zoom_label.color = 0x000000


def get_fractal_from_touch(touch_x, touch_y):
    if mandelbrot_button.contains((touch_x, touch_y)):
        return mandelbrot_fractal
    elif ship_button.contains((touch_x, touch_y)):
        return burning_ship_fractal
    else:
        return None


def set_background(bitmap, color_palette, position=None):
    while _bg_group:
        _bg_group.pop()

    if not position:
        position = (0, 0)  # default in top corner

    if not bitmap:
        return  # we're done, no background desired

    try:
        _bg_sprite = displayio.TileGrid(bitmap,
                                             pixel_shader=color_palette,
                                             position=position)
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


def rgb_to_int(r, g, b):
    return r * 256 ** 2 + g * 256 + b


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


if __name__ == '__main__':
    splash.append(mandelbrot_button.group)
    splash.append(ship_button.group)
    splash.append(zoom_label)

    # get the original fractal selection
    fractal = None
    while fractal is None:
        touch_x, touch_y, _ = wait_for_touch(touchscreen)
        fractal = get_fractal_from_touch(touch_x, touch_y)

    # disable the buttons
    flip_buttons(enabled=False)

    # create the colors that will be used to display the fractal
    num_colors_to_use = 16
    colors = [(255, 0, 0)]
    while len(colors) < num_colors_to_use:
        colors.append(get_next_color(*colors[-1], step=75))
    colors = [rgb_to_int(*c) for c in colors]
    color_mapper = LinearColorMapper(colors)

    # create the fractal viewer
    max_iter = 16
    fractal_viewer = FractalViewer(color_mapper, max_iter, pix_sz=fractal_area_size, fractal=fractal)

    while True:
        set_background(fractal_viewer.bitmap, color_mapper.palette, position=fractal_position)
        
        # keep rendering the fractal until it is done
        while fractal_viewer.has_computation_left():
            fractal_viewer.step()
            set_background(fractal_viewer.bitmap, color_mapper.palette, position=fractal_position)

        # enable the buttons
        flip_buttons(enabled=True)

        # get the touch point
        touch_x, touch_y, _ = wait_for_touch(touchscreen)

        new_fractal = get_fractal_from_touch(touch_x, touch_y)
        if new_fractal is not None:
            # if they selected one of the fractal buttons, restart with that fractal
            flip_buttons(enabled=False)
            fractal_viewer = FractalViewer(color_mapper, max_iter, pix_sz=fractal_area_size, fractal=new_fractal)
        elif touch_x >= fractal_position[0]:
            # if they clicked within the fractal, zoom
            flip_buttons(enabled=False)
            fractal_viewer.register_click((touch_x - fractal_position[0], touch_y))
