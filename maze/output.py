#
# Copyright (c) 2021 Joshua Hughes <kivhift@gmail.com>
#
# SPDX-License-Identifier: MIT
#
import cairo

from .grid import Cell

class DrawingDimensions:
    def __init__(self, grid, interior_size=2, wall_thickness=1, scale=1):
        s = lambda x: round(scale * x)
        interior_size = s(interior_size)
        wall_thickness = s(wall_thickness)
        self.interior_size = interior_size
        self.wall_thickness = wall_thickness
        self.cell_skip = interior_size + wall_thickness
        self.W = self.cell_skip * grid.columns + wall_thickness
        self.H = self.cell_skip * grid.rows + wall_thickness
        self.E_neighbor_rect = (interior_size + wall_thickness, interior_size)
        self.S_neighbor_rect = (interior_size, interior_size + wall_thickness)
        self.interior_rect = (interior_size, interior_size)

def _draw_to_surface(grid, surface, dimension):
    dummy_cell = Cell(-1, -1)

    ctx = cairo.Context(surface)
    ctx.set_source_rgb(0, 0, 0)
    ctx.paint()

    for r, row in enumerate(grid.each_row):
        r *= dimension.cell_skip
        r += dimension.wall_thickness
        for c, cell in enumerate(row):
            c *= dimension.cell_skip
            c += dimension.wall_thickness
            cell = cell or dummy_cell
            ctx.set_source_rgb(*(grid.cell_background_color(cell) or (1, 1, 1)))
            ctx.rectangle(c, r, *dimension.interior_rect)
            ctx.fill()
            if cell.linked_to(cell.E):
                ctx.rectangle(c, r, *dimension.E_neighbor_rect)
                ctx.fill()
            if cell.linked_to(cell.S):
                ctx.rectangle(c, r, *dimension.S_neighbor_rect)
                ctx.fill()

formats = set()
def to_PNG(grid, out, scale=1):
    d = DrawingDimensions(grid, scale=scale)
    with cairo.ImageSurface(cairo.FORMAT_ARGB32, d.W, d.H) as surface:
        _draw_to_surface(grid, surface, d)
        surface.write_to_png(out)
formats.add('PNG')

def to_SVG(grid, out, scale=1):
    d = DrawingDimensions(grid, scale=scale)
    with cairo.SVGSurface(out, d.W, d.H) as surface:
        _draw_to_surface(grid, surface, d)
formats.add('SVG')

def to_PDF(grid, out, scale=1):
    d = DrawingDimensions(grid, scale=scale)
    with cairo.PDFSurface(out, d.W, d.H) as surface:
        _draw_to_surface(grid, surface, d)
formats.add('PDF')

class UTF8Output:
    def __init__(self, out):
        self._out = out
        self._opened = False
        self._binary = False
        if hasattr(out, 'mode'):
            if getattr(out, 'mode').endswith('b'):
                self._binary = True
        else:
            self._out = open(out, 'w', encoding='utf-8')
            self._opened = True

    def write(self, strbuf):
        if self._binary:
            return self._out.write(strbuf.encode('utf-8'))
        return self._out.write(strbuf)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        if self._opened:
            self._out.close()
        return False

def to_HTML(grid, out, scale=1):
    d = DrawingDimensions(grid, scale=scale)
    dummy_cell = Cell(-1, -1)
    ir = ', '.join(str(x) for x in d.interior_rect)
    E_nr = ', '.join(str(x) for x in d.E_neighbor_rect)
    S_nr = ', '.join(str(x) for x in d.S_neighbor_rect)
    with UTF8Output(out) as o:
        p = lambda s: print(s, file=o)
        p('''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"></head>
<body><div><canvas id="maze"></canvas></div><script>
"use strict";
window.addEventListener('load', (e) => {
var canv = document.querySelector('#maze'), ctx = canv.getContext('2d');
//    var html = document.documentElement;
//    canv.width = Math.floor(0.97 * html.clientWidth);
//    canv.height = Math.floor(0.97 * html.clientHeight);
''')
        p(f'canv.width = {d.W}\ncanv.height = {d.H}')
        p('''
ctx.fillStyle = 'rgb(0, 0, 0)';
ctx.fillRect(0, 0, canv.width, canv.height);
''')
        for r, row in enumerate(grid.each_row):
            r *= d.cell_skip
            r += d.wall_thickness
            for c, cell in enumerate(row):
                c *= d.cell_skip
                c += d.wall_thickness
                cell = cell or dummy_cell
                rgb = ', '.join(map(lambda x: str(round(255 * x))
                    , grid.cell_background_color(cell) or (1, 1, 1)))
                p(f"ctx.fillStyle = 'rgb({rgb}';\nctx.fillRect({c}, {r}, {ir});")
                if cell.linked_to(cell.E):
                    p(f'ctx.fillRect({c}, {r}, {E_nr});')
                if cell.linked_to(cell.S):
                    p(f'ctx.fillRect({c}, {r}, {S_nr});')
        p('''
});
</script></body></html>''')
formats.add('HTML')
