from displayio import Bitmap, Palette
from math import sqrt


class Fractal:
    def __init__(self, fractal_fn, starting_cmp_bounds):
        self.fractal_fn = fractal_fn
        self.starting_cmp_bounds = starting_cmp_bounds
    

def mandelbrot_fn(c, max_iter):
    z = c
    n = 0
    while z.modulus() <= 2 and n < max_iter:
        z = z*z + c
        n += 1
    return n


def burning_ship_fn(c, max_iter):
    z = c
    n = 0
    while z.modulus() <= 2 and n < max_iter:
        z_abs = Complex(abs(z.r), abs(z.c))
        z = z_abs * z_abs + c
        n += 1
    return n


mandelbrot_fractal = Fractal(mandelbrot_fn, ((-2.4, 1.2), (-1.2, 1.2)))
burning_ship_fractal = Fractal(burning_ship_fn, ((-2.2, 1.4), (-1.8, 0.6)))

class Complex:
    def __init__(self, r, c):
        self.r = r
        self.c = c

    def modulus(self):
        return sqrt(self.r**2 + self.c**2)

    def __mul__(self, other):
        if not isinstance(other, Complex):
            raise ValueError("Can only multiply two complex numbers")
        return Complex(self.r * other.r - self.c * other.c, self.r * other.c + self.c * other.r)

    def __add__(self, other):
        if not isinstance(other, Complex):
            raise ValueError("Can only add two complex numbers")
        return Complex(self.r + other.r, self.c + other.c)


class FractalViewer:
    def __init__(self, color_mapper, max_iter, fractal=mandelbrot_fractal, pix_sz=(320, 240), cmp_bounds=None):
        self.color_mapper = color_mapper
        self.fractal_fn = fractal.fractal_fn

        if pix_sz[0] % 2 == 0:
            pix_sz = (pix_sz[0]-1, pix_sz[1])
        if pix_sz[1] % 2 == 0:
            pix_sz = (pix_sz[0], pix_sz[1]-1)
        self.pix_sz = pix_sz

        self.cmp_bounds = cmp_bounds if cmp_bounds is not None else fractal.starting_cmp_bounds
        self.max_iter = max_iter
        self.current_col = 0
        self.bitmap = Bitmap(self.pix_sz[0], self.pix_sz[1], color_mapper.num_colors)

    def pix_to_cmp(self, pix, fencepost_offset=-1):
        return Complex(self.cmp_bounds[0][0] + 1.*pix[0]*(self.cmp_bounds[0][1] - self.cmp_bounds[0][0]) / (self.pix_sz[0] + fencepost_offset),
                       self.cmp_bounds[1][0] + 1.*pix[1]*(self.cmp_bounds[1][1] - self.cmp_bounds[1][0]) / (self.pix_sz[1] + fencepost_offset))

    def has_computation_left(self):
        return self.current_col != self.pix_sz[0]

    def step(self):
        x = self.current_col
        for y in range(self.pix_sz[1]):
            fractal_iter_cnt = self.fractal_fn(self.pix_to_cmp((x, y)), self.max_iter-1)
            self.bitmap[x, y] = self.color_mapper.disp_pt_to_color_ind(fractal_iter_cnt)
        self.current_col = self.current_col + 1

    def register_click(self, click_pt):
        half_screen_w = (self.pix_sz[0] + 1) // 2
        half_screen_h = (self.pix_sz[1] + 1) // 2

        click_base_x = click_pt[0] - half_screen_w // 2
        click_base_x = max(0, min(click_base_x, half_screen_w - 1))
        click_base_y = click_pt[1] - half_screen_h // 2
        click_base_y = max(0, min(click_base_y, half_screen_h - 1))

        click_pt = (click_base_x, click_base_y)
        end_pix_pt = (click_pt[0] + half_screen_w, click_pt[1] + half_screen_h)
        
        start_cmp = self.pix_to_cmp(click_pt)
        end_cmp = self.pix_to_cmp(end_pix_pt, fencepost_offset=0)

        self.cmp_bounds = ((start_cmp.r, end_cmp.r), (start_cmp.c, end_cmp.c))
        biggest_pt = (self.pix_sz[0] - 1, self.pix_sz[1] - 1)

        self.current_col = 0

        new_bitmap = Bitmap(self.pix_sz[0], self.pix_sz[1], self.color_mapper.num_colors)

        for x in range(self.pix_sz[0]):
            for y in range(self.pix_sz[1]):
                new_bitmap[x, y] = self.bitmap[x // 2 + click_pt[0], y // 2 + click_pt[1]]
        self.bitmap = new_bitmap


class LinearColorMapper:
    def __init__(self, color_list, iter_step_size=1):
        self.color_list = color_list
        self.palette = Palette(self.num_colors)
        for i in range(self.num_colors):
            self.palette[i] = color_list[i]
        self.iter_step_size = iter_step_size

    def disp_pt_to_color_ind(self, fractal_iter_cnt):
        return min(self.num_colors - 1, fractal_iter_cnt // self.iter_step_size)

    @property
    def num_colors(self):
        return len(self.color_list)
    