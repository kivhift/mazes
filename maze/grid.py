#
# Copyright (c) 2021 Joshua Hughes <kivhift@gmail.com>
#
# SPDX-License-Identifier: MIT
#
import string

from random import choice

class Distances(dict):
    def __init__(self, root):
        self.root = root
        self[root] = 0

    def cells(self):
        return self.keys()

    def path_to(self, goal):
        current = goal

        breadcrumbs = Distances(self.root)
        breadcrumbs[current] = self[current]
        root = self.root
        while current != root:
            for neighbor in current.links:
                if self[neighbor] < self[current]:
                    breadcrumbs[neighbor] = self[neighbor]
                    current = neighbor
                    break

        return breadcrumbs

    @property
    def max(self):
        max_distance = 0
        max_cell = self.root

        for cell in self:
            if self[cell] > max_distance:
                max_cell = cell
                max_distance = self[cell]

        return max_cell, max_distance

class Cell:
    def __init__(self, row, column):
        self._row = row
        self._column = column
        self._links = set()
        self._neighbors = [None] * 4

    @property
    def row(self):
        return self._row

    @property
    def column(self):
        return self._column

    @property
    def N(self):
        return self._neighbors[0]

    @N.setter
    def N(self, cell):
        if self._neighbors[0] is None:
            self._neighbors[0] = cell

    @property
    def E(self):
        return self._neighbors[1]

    @E.setter
    def E(self, cell):
        if self._neighbors[1] is None:
            self._neighbors[1] = cell

    @property
    def S(self):
        return self._neighbors[2]

    @S.setter
    def S(self, cell):
        if self._neighbors[2] is None:
            self._neighbors[2] = cell

    @property
    def W(self):
        return self._neighbors[3]

    @W.setter
    def W(self, cell):
        if self._neighbors[3] is None:
            self._neighbors[3] = cell

    @property
    def neighbors(self):
        return list(filter(None, self._neighbors))

    @property
    def neighbors_with_links(self):
        return list(filter(lambda x: x.has_links, self.neighbors))

    @property
    def neighbors_without_links(self):
        return list(filter(lambda x: not x.has_links, self.neighbors))

    @property
    def random_neighbor(self):
        return choice(self.neighbors)

    def link(self, cell, bidirectional=True):
        self._links.add(cell)
        if bidirectional:
            cell.link(self, False)
        return self

    def unlink(self, cell, bidirectional=True):
        self._links.remove(cell)
        if bidirectional:
            cell.unlink(self, False)
        return self

    def linked_to(self, cell):
        return cell in self._links

    @property
    def links(self):
        return self._links

    @property
    def has_links(self):
        return bool(len(self._links))

    @property
    def distances(self):
        distances = Distances(self)
        frontier = [self]

        while frontier:
            next_frontier = []
            for cell in frontier:
                for linked in cell.links:
                    if linked in distances:
                        continue
                    distances[linked] = distances[cell] + 1
                    next_frontier.append(linked)
            frontier = next_frontier

        return distances

class Grid:
    def __init__(self, rows, columns):
        super().__init__()
        self._prepare_grid(rows, columns)
        self._configure_cells()

    def __getitem__(self, index):
        r, c = index
        if r < 0 or r >= self.rows:
            return None
        if c < 0 or c >= self.columns:
            return None
        return self._grid[r][c]

    def __str__(self):
        lines = [ '+' + '---+' * self.columns ]
        lines_append = lines.append
        dummy_cell = Cell(-1, -1)

        mid, bot = [], []
        mid_append, bot_append = mid.append, bot.append
        for row in self._grid:
            mid_append('|')
            bot_append('+')

            for cell in row:
                cell = cell or dummy_cell
                mid_append(f' {self.cell_interior(cell)} ')
                mid_append(' ' if cell.linked_to(cell.E) else '|')
                bot_append(' ' * 3 if cell.linked_to(cell.S) else '-' * 3)
                bot_append('+')

            lines_append(''.join(mid))
            lines_append(''.join(bot))

            mid.clear()
            bot.clear()

        return '\n'.join(lines)

    def _prepare_grid(self, rows, columns):
        self._grid = [
            [ Cell(r, c) for c in range(columns) ] for r in range(rows)
        ]

    def _configure_cells(self):
        for cell in self.each_cell:
            r, c = cell.row, cell.column
            cell.N = self[r - 1, c]
            cell.E = self[r, c + 1]
            cell.S = self[r + 1, c]
            cell.W = self[r, c - 1]

    @property
    def rows(self):
        return len(self._grid)

    @property
    def columns(self):
        return len(self._grid[0])

    @property
    def size(self):
        return self.rows * self.columns

    @property
    def random_cell(self):
        return choice(choice(self._grid))

    @property
    def each_row(self):
        for row in self._grid:
            yield row

    @property
    def each_cell(self):
        for row in self._grid:
            for col in row:
                if col is not None:
                    yield col

    def cell_interior(self, cell):
        return ' '

    def cell_background_color(self, cell):
        return None

    @property
    def dead_ends(self):
        dead_ends = []
        for cell in self.each_cell:
            if 1 == len(cell.links):
                dead_ends.append(cell)

        return dead_ends

_b62 = string.digits + string.ascii_lowercase + string.ascii_uppercase
class DistanceGrid(Grid):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)

        self.distances = None

    def cell_interior(self, cell):
        if self.distances is None or self.distances.get(cell) is None:
            return super().cell_interior(cell)

        distance = self.distances[cell]
        if 0 == distance:
            return '0'

        rep = []
        base = len(_b62)
        while distance:
            distance, i = divmod(distance, base)
            rep.append(_b62[i])

        return ''.join(reversed(rep))

class ColoredGrid(Grid):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)

        self._distances = None

    @property
    def distances(self):
        return self._distances

    @distances.setter
    def distances(self, distances):
        _, maximum = distances.max
        self._distances = distances
        self._maximum = maximum

    def cell_background_color(self, cell):
        if self._distances is None or self._distances.get(cell) is None:
            return super().cell_background_color(cell)

        distance = self._distances[cell]
        norm = (self._maximum - distance) / self._maximum
        R = 0
        G = 0.5 * (norm + 1.0) - 0.25
        B = 0

        return (R, G, B)

class Mask:
    def __init__(self, rows, columns):
        self._mask = [ [ True for c in range(columns) ] for r in range(rows) ]

    def __getitem__(self, index):
        r, c = index
        if r < 0 or r >= self.rows:
            return False
        if c < 0 or c >= self.columns:
            return False
        return self._mask[r][c]

    def __setitem__(self, index, is_on):
        r, c = index
        if r < 0 or r >= self.rows:
            raise IndexError(f'Row index is out of range: {r}')
        if c < 0 or c >= self.columns:
            raise IndexError(f'Column index is out of range: {c}')
        self._mask[r][c] = is_on

    def __str__(self):
        lines = []
        for row in self._mask:
            ch = []
            for x in row:
                ch.append('.' if x else 'o')
            lines.append(''.join(ch))
        return '\n'.join(lines)

    @classmethod
    def from_RLE(cls, rle):
        digits, whitespace = string.digits, string.whitespace
        _0 = ord('0')

        class _state:
            def __init__(self):
                self.mask = None
                self.width = None
                self.height = None
                self.count = 0
                self.index = 0

            @property
            def rowcol(self):
                return divmod(self.index, self.width)

        s = _state()
        def get_and_reset_count():
            cnt = s.count if s.count > 0 else 1
            s.count = 0
            return cnt

        for ch in rle:
            if ch in whitespace:
                continue
            elif ch in digits:
                s.count *= 10
                s.count += ord(ch) - _0
            elif 'w' == ch:
                if s.width is None:
                    s.width = get_and_reset_count()
                    if s.height is not None and s.mask is None:
                        s.mask = cls(s.height, s.width)
                else:
                    raise ValueError(f'Width already specified as {width}')
            elif 'h' == ch:
                if s.height is None:
                    s.height = get_and_reset_count()
                    if s.width is not None and s.mask is None:
                        s.mask = cls(s.height, s.width)
                else:
                    raise ValueError(f'Height already specified as {height}')
            elif 'o' == ch:
                if s.mask is None:
                    raise ValueError('Must specify dimensions before occupancy')
                for _ in range(get_and_reset_count()):
                    r, c = s.rowcol
                    s.mask[r, c] = False
                    s.index += 1
            elif '.' == ch:
                s.index += get_and_reset_count()
            elif '$' == ch:
                if s.width is None:
                    raise ValueError('Must specify width before ending row')
                r, c = s.rowcol
                s.index += s.width - c
            elif '!' == ch:
                break
            else:
                raise ValueError(f'Bad character: {repr(ch)}')

        return s.mask

    def to_RLE(self):
        rle = [f'{self.rows}h{self.columns}w']

        ch = { True: '.', False: 'o' }
        current = None
        count = 0
        def output_count():
            if 1 == count:
                rle.append(ch[current])
            else:
                rle.append(f'{count}{ch[current]}')

        for row in self._mask:
            for val in row:
                if val != current:
                    if current is not None:
                        output_count()
                    current = val
                    count = 1
                else:
                    count += 1

        if current is not None:
            output_count()

        return ''.join(rle)

    @property
    def rows(self):
        return len(self._mask)

    @property
    def columns(self):
        return len(self._mask[0])

    @property
    def count(self):
        count = 0
        for row in self._mask:
            for x in row:
                if x:
                    count += 1
        return count

    @property
    def random_location(self):
        if 0 == self.count:
            raise ValueError('No locations on')

        rows = list(range(self.rows))
        cols = list(range(self.columns))
        mask = self._mask
        while True:
            row = choice(rows)
            col = choice(cols)
            if mask[row][col]:
                return row, col

class MaskedGrid(Grid):
    def __init__(self, mask):
        self._mask = mask
        super().__init__(mask.rows, mask.columns)

    def _prepare_grid(self, rows, columns):
        mask = self._mask
        self._grid = [
            [ Cell(r, c) if mask[r, c] else None for c in range(columns) ]
                for r in range(rows)
        ]

    @property
    def random_cell(self):
        r, c = self._mask.random_location
        return self[r, c]

    @property
    def size(self):
        return self._mask.count

class MaskedColoredGrid(MaskedGrid, ColoredGrid):
    def cell_background_color(self, cell):
        if not self._mask[cell.row, cell.column]:
            return (0, 0, 0)

        return super().cell_background_color(cell)
