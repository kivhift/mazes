#
# Copyright (c) 2021 Joshua Hughes <kivhift@gmail.com>
#
# SPDX-License-Identifier: MIT
#
import sys

from PySide6.QtWidgets import (
    QApplication, QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout,
    QMainWindow, QMessageBox, QSpinBox, QVBoxLayout, QWidget,
    QComboBox, QLabel
)
from PySide6.QtCore import Slot, Qt
from PySide6.QtGui import QColor, QPainter, QShortcut, QKeySequence

from .grid import ColoredGrid, Cell, Mask
from . import algorithm

class RowColumnDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        vbox = QVBoxLayout(self)
        self.setLayout(vbox)

        self._rows = rows = QSpinBox(self)
        vbox.addWidget(rows)
        rows.setValue(10)
        rows.setMinimum(1)
        rows.setMaximum(200)
        rows.setSuffix(' rows')

        self._columns = cols = QSpinBox(self)
        vbox.addWidget(cols)
        cols.setValue(10)
        cols.setMinimum(1)
        cols.setMaximum(200)
        cols.setSuffix(' columns')

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self
        )
        vbox.addWidget(buttons)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

    @property
    def rows(self):
        return self._rows.value()

    @property
    def columns(self):
        return self._columns.value()

class RowColumnAlgorithmDialog(RowColumnDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._algo = None

        layout = self.layout()
        count = layout.count()
        if 0 == count:
            return

        buttons = layout.takeAt(count - 1)
        if buttons is None:
            return

        self._algo = combo = QComboBox(self)
        combo.addItems(sorted(algorithm.names))
        layout.addWidget(combo)
        layout.addItem(buttons)

    @property
    def algorithm(self):
        if self._algo is None:
            return None

        return self._algo.currentText()

class DrawingDimensions:
    def __init__(self, grid, interior=2, wall=1):
        self.cell_skip = cs = interior + wall
        self.wall = wall
        self.width = cs * grid.columns + wall
        self.height = cs * grid.rows + wall
        self.interior_rect = (interior, interior)
        self.east_neighbor_rect = (interior + wall, interior)
        self.south_neighbor_rect = (interior, interior + wall)

    def row_coord(self, row):
        return self.cell_skip * row + self.wall

    def column_coord(self, col):
        return self.cell_skip * col + self.wall

class MaskWidget(QWidget):
    def __init__(self, mask, parent=None):
        super().__init__(parent)

        self._mask = mask
        self._dim = DrawingDimensions(mask)
        self._lastpos = None
        self._wall_color = Qt.black
        self._unused_color = Qt.darkGreen
        self._used_color = QColor(30, 30, 30)
        self._has_changed = False

    @property
    def mask(self):
        return self._mask

    @property
    def has_changed(self):
        return self._has_changed

    @has_changed.setter
    def has_changed(self, value):
        self._has_changed = bool(value)

    def note_save(self):
        self._has_changed = False

    @Slot()
    def invert(self):
        mask = self._mask
        for r in range(mask.rows):
            for c in range(mask.columns):
                mask[r, c] = not mask[r, c]
        self._has_changed = True
        self.update()

    def paintEvent(self, event):
        mask = self._mask
        dim = self._dim
        wall = self._wall_color
        used = self._used_color
        unused = self._unused_color

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.scale(self.width() / dim.width, self.height() / dim.height)

        p.fillRect(0, 0, dim.width, dim.height, wall)
        for r in range(mask.rows):
            y = dim.row_coord(r)
            for c in range(mask.columns):
                x = dim.column_coord(c)
                p.fillRect(
                    x, y, *dim.interior_rect, used if mask[r, c] else unused
                )

    def _rowcol(self, pos):
        H = self.height() / self._mask.rows
        W = self.width() / self._mask.columns

        # int() truncates towards zero (and that's a good thing).
        return int(pos.y() / H), int(pos.x() / W)

    def _pos_out_of_range(self, pos):
        x, y = pos.x(), pos.y()
        return x < 0 or x >= self.width() or y < 0 or y >= self.height()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        r, c = self._rowcol(event.pos())
        if self._lastpos is None:
            self._mask[r, c] = not self._mask[r, c]
            self._has_changed = True
            self.update()

        self._lastpos = (r, c)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return

        if self._lastpos is None:
            return

        pos = event.pos()
        if self._pos_out_of_range(pos):
            return

        pos = self._rowcol(pos)
        lastpos = self._lastpos
        if lastpos == pos:
            return

        r, c = pos
        self._mask[r, c] = not self._mask[r, c]
        self._has_changed = True
        self.update()
        self._lastpos = pos

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return

        self._lastpos = None

class MaskMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.resize(500, 500)

        file_menu = self.menuBar().addMenu('&File')
        open_action = file_menu.addAction('&Open')
        open_action.triggered.connect(self.open_mask)
        save_action = file_menu.addAction('&Save')
        save_action.triggered.connect(self.save_mask)
        file_menu.addSeparator()
        new_action = file_menu.addAction('&New')
        new_action.triggered.connect(self.new_mask)
        file_menu.addSeparator()
        quit_action = file_menu.addAction('&Quit')
        quit_action.triggered.connect(self.quit)

        action_menu = self.menuBar().addMenu('&Action')
        invert_action = action_menu.addAction('&Invert')
        invert_action.triggered.connect(self.invert_mask)

        status_bar = self.statusBar()
        self._size_label = size_label = QLabel('0x0')
        status_bar.addPermanentWidget(size_label)

        shortcut = QShortcut(QKeySequence('Alt+L'), self)
        shortcut.activated.connect(self.increment_width)
        shortcut = QShortcut(QKeySequence('Alt+H'), self)
        shortcut.activated.connect(self.decrement_width)
        shortcut = QShortcut(QKeySequence('Alt+J'), self)
        shortcut.activated.connect(self.increment_height)
        shortcut = QShortcut(QKeySequence('Alt+K'), self)
        shortcut.activated.connect(self.decrement_height)

    def changed_mask_OK(self, what=None):
        mw = self.centralWidget()
        if mw is None:
            return True

        if not mw.has_changed:
            return True

        ans = QMessageBox.question(
            self, 'Mask changed', f'Mask has changed.  Continue {what}?'
        )

        return ans == QMessageBox.StandardButton.Yes

    @Slot()
    def quit(self):
        if not self.changed_mask_OK('Quit'):
            return

        qApp.quit()

    @Slot()
    def open_mask(self):
        if not self.changed_mask_OK('Open'):
            return

        title = 'Open mask'
        mask_file = QFileDialog.getOpenFileName(self, title)[0]
        if not mask_file:
            return

        # The dialog already checks for existence.
        try:
            with open(mask_file, 'r') as f:
                mask = Mask.from_RLE(f.read())
            self.setCentralWidget(MaskWidget(mask))
            self._size_label.setText(f'{mask.rows}x{mask.columns}')
        except Exception as e:
            QMessageBox.critical(self, title, f'Could not open mask: {e}')
            return

    @Slot()
    def save_mask(self):
        title = 'Save mask'
        mw = self.centralWidget()
        if mw is None:
            QMessageBox.information(self, title, 'No mask to save')
            return

        mask_file = QFileDialog.getSaveFileName(self, title)[0]
        if not mask_file:
            return

        # The dialog already confirms overwrites.
        try:
            with open(mask_file, 'w') as f:
                print(mw.mask.to_RLE(), file=f)
            mw.note_save()
        except Exception as e:
            QMessageBox.critical(self, title, f'Could not save mask: {e}')
            return

    @Slot()
    def new_mask(self):
        if not self.changed_mask_OK('New'):
            return

        rc = RowColumnDialog(self)
        rc.setWindowTitle('Mask dimensions')
        if QDialog.Rejected == rc.exec_():
            return

        self.setCentralWidget(MaskWidget(Mask(rc.rows, rc.columns)))
        self._size_label.setText(f'{rc.rows}x{rc.columns}')

    @Slot()
    def invert_mask(self):
        mw = self.centralWidget()
        if mw is None:
            QMessageBox.information(self, 'Invert mask', 'No mask to invert')
            return

        mw.invert()

    def _change_dimensions(self, delta_r, delta_c):
        mw = self.centralWidget()
        if mw is None:
            return

        mask = mw.mask
        new_rows = mask.rows + delta_r
        if new_rows < 1:
            return

        new_cols = mask.columns + delta_c
        if new_cols < 1:
            return

        new_mask = Mask(new_rows, new_cols)
        for r in range(min(mask.rows, new_mask.rows)):
            for c in range(min(mask.columns, new_mask.columns)):
                new_mask[r, c] = mask[r, c]

        nmw = MaskWidget(new_mask)
        nmw.has_changed = mw.has_changed
        self.setCentralWidget(nmw)
        self._size_label.setText(f'{new_mask.rows}x{new_mask.columns}')

    @Slot()
    def increment_width(self):
        self._change_dimensions(0, 1)

    @Slot()
    def decrement_width(self):
        self._change_dimensions(0, -1)

    @Slot()
    def increment_height(self):
        self._change_dimensions(1, 0)

    @Slot()
    def decrement_height(self):
        self._change_dimensions(-1, 0)

def cell_color(rgb):
    if rgb is None:
        return Qt.white

    r, g, b = rgb
    s = lambda x: round(255 * x)

    return QColor(s(r), s(g), s(b))

class MazeWidget(MaskWidget):
    def __init__(self, grid, parent=None):
        super().__init__(Mask(grid.rows, grid.columns), parent)

        self._grid = grid

    def paintEvent(self, event):
        grid = self._grid
        mask = self._mask
        dim = self._dim
        wall = self._wall_color
        used = self._used_color
        unused = self._unused_color
        dummy_cell = Cell(-1, -1)
        interior_rect = dim.interior_rect
        E_neighbor_rect = dim.east_neighbor_rect
        S_neighbor_rect = dim.south_neighbor_rect

        p = QPainter(self)
#        p.setRenderHint(QPainter.Antialiasing)
        p.scale(self.width() / dim.width, self.height() / dim.height)

        p.fillRect(0, 0, dim.width, dim.height, wall)
        for r, row in enumerate(grid.each_row):
            y = dim.row_coord(r)
            for c, cell in enumerate(row):
                x = dim.column_coord(c)
                cell = cell or dummy_cell
                color = used if mask[r, c] else unused
                p.fillRect(x, y, *interior_rect, color)
                if cell.linked_to(cell.E):
                    p.fillRect(x, y, *E_neighbor_rect, color)
                if cell.linked_to(cell.S):
                    p.fillRect(x, y, *S_neighbor_rect, color)

class MazeMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.resize(500, 500)

        maze_menu = self.menuBar().addMenu('&Maze')
        new_action = maze_menu.addAction('&New')
        new_action.triggered.connect(self.new_maze)
        maze_menu.addSeparator()
        quit_action = maze_menu.addAction('&Quit')
        quit_action.triggered.connect(qApp.quit)

    @Slot()
    def new_maze(self):
        rc = RowColumnAlgorithmDialog(self)
        rc.setWindowTitle('Maze dimensions')
        if QDialog.Rejected == rc.exec_():
            return

        self.setCentralWidget(MazeWidget(
            getattr(algorithm, rc.algorithm)(ColoredGrid(rc.rows, rc.columns))
        ))

def mask_edit_main():
    app = QApplication([])
    w = MaskMainWindow()
    w.setWindowTitle('Maze mask editor')
    w.show()
    sys.exit(app.exec_())

def maze_main():
    app = QApplication([])
    w = MazeMainWindow()
    w.setWindowTitle('Maze')
    w.show()
    sys.exit(app.exec_())
