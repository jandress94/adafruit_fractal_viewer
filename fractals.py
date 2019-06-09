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


def match_cmp_bounds_with_aspect_ratio(raw_cmp_bounds, pix_sz):
    canvas_aspect_ratio = 1. * pix_sz[0] / pix_sz[1] # w / h
    real_range = raw_cmp_bounds[0][1] - raw_cmp_bounds[0][0]
    cmp_range = raw_cmp_bounds[1][1] - raw_cmp_bounds[1][0]
    cmp_bound_aspect_ratio = 1. * real_range / cmp_range

    if canvas_aspect_ratio < cmp_bound_aspect_ratio:
        cmp_range = real_range / canvas_aspect_ratio
        cmp_mid = (raw_cmp_bounds[1][0] + raw_cmp_bounds[1][1]) / 2.
        return (raw_cmp_bounds[0], (cmp_mid - cmp_range / 2, cmp_mid + cmp_range / 2))
    elif canvas_aspect_ratio > cmp_bound_aspect_ratio:
        real_range = cmp_range * canvas_aspect_ratio
        real_mid = (raw_cmp_bounds[0][0] + raw_cmp_bounds[0][1]) / 2.
        return ((real_mid - real_range / 2, real_mid + real_range / 2), raw_cmp_bounds[1])
    else:
        return raw_cmp_bounds


class FractalViewer:
    def __init__(self, color_mapper, max_iter, fractal=mandelbrot_fractal, pix_sz=(320, 240), cmp_bounds=None):
        self.color_mapper = color_mapper
        self.fractal_fn = fractal.fractal_fn

        if pix_sz[0] % 2 == 0:
            pix_sz = (pix_sz[0]-1, pix_sz[1])
        if pix_sz[1] % 2 == 0:
            pix_sz = (pix_sz[0], pix_sz[1]-1)
        self.pix_sz = pix_sz

        self.first_render = True
        raw_cmp_bounds = cmp_bounds if cmp_bounds is not None else fractal.starting_cmp_bounds
        self.cmp_bounds = match_cmp_bounds_with_aspect_ratio(raw_cmp_bounds, self.pix_sz)

        self.max_iter = max_iter
        self.current_col = 0
        self.bitmap = Bitmap(self.pix_sz[0], self.pix_sz[1], color_mapper.num_colors)

    def pix_to_cmp(self, pix, fencepost_offset=-1):
        return Complex(self.cmp_bounds[0][0] + 1.*pix[0]*(self.cmp_bounds[0][1] - self.cmp_bounds[0][0]) / (self.pix_sz[0] + fencepost_offset),
                       self.cmp_bounds[1][0] + 1.*pix[1]*(self.cmp_bounds[1][1] - self.cmp_bounds[1][0]) / (self.pix_sz[1] + fencepost_offset))

    def cmp_to_pix(self, comp):
        step_r = (self.cmp_bounds[0][1] - self.cmp_bounds[0][0]) / (self.pix_sz[0] - 1)
        step_c = (self.cmp_bounds[1][1] - self.cmp_bounds[1][0]) / (self.pix_sz[1] - 1)

        return (comp.r - self.cmp_bounds[0][0]) / step_r, (comp.c - self.cmp_bounds[1][0]) / step_c

    def has_computation_left(self):
        return self.current_col != self.pix_sz[0]

    def step(self):
        x = self.current_col
        has_skips_in_col = (not self.first_render) and (x%2 == 0)
        for y in range(self.pix_sz[1]):
            if has_skips_in_col and (y%2 == 0):
                continue

            fractal_iter_cnt = self.fractal_fn(self.pix_to_cmp((x, y)), self.max_iter-1)
            self.bitmap[x, y] = self.color_mapper.disp_pt_to_color_ind(fractal_iter_cnt)
        self.current_col = self.current_col + 1

    def register_click(self, click_pt):
        click_cmp = self.pix_to_cmp(click_pt)
        rng_r = (self.cmp_bounds[0][1] - self.cmp_bounds[0][0]) / 2
        rng_c = (self.cmp_bounds[1][1] - self.cmp_bounds[1][0]) / 2

        max_x = (self.pix_sz[0] - 1) // 2
        max_y = (self.pix_sz[1] - 1) // 2

        new_start_cmp = Complex(click_cmp.r - rng_r/2, click_cmp.c - rng_c/2)
        new_start_pix = self.cmp_to_pix(new_start_cmp)
        new_start_pix = (max(0, min(int(new_start_pix[0]), max_x)), max(0, min(int(new_start_pix[1]), max_y)))
        new_start_cmp = self.pix_to_cmp(new_start_pix)

        self.cmp_bounds = ((new_start_cmp.r, new_start_cmp.r + rng_r), (new_start_cmp.c, new_start_cmp.c + rng_c))
        self.current_col = 0

        new_bitmap = Bitmap(self.pix_sz[0], self.pix_sz[1], self.color_mapper.num_colors)

        for x in range(self.pix_sz[0]):
            for y in range(self.pix_sz[1]):
                new_bitmap[x, y] = self.bitmap[x // 2 + new_start_pix[0], y // 2 + new_start_pix[1]]
        self.bitmap = new_bitmap
        self.first_render = False


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
    