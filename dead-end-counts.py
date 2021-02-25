#!/usr/bin/env python3
#
# Copyright (c) 2021 Joshua Hughes <kivhift@gmail.com>
#
# SPDX-License-Identifier: MIT
#
from time import monotonic_ns

import maze.grid
import maze.algorithm

tries = 100
size = 20

average = {}
for name in maze.algorithm.names:
    algo = getattr(maze.algorithm, name)
    dead_end_total = 0
    time_total = 0
    for _ in range(tries):
        start = monotonic_ns()
        grid = algo(maze.grid.Grid(size, size))
        end = monotonic_ns()

        dead_end_total += len(grid.dead_ends)
        time_total += end - start
    average[name] = (dead_end_total / tries, time_total / tries)

cell_count = size * size
W = max(len(x) for x in average)
print(f'Average dead-ends per {size}x{size} maze ({cell_count} cells):')
for name, (de_ave, ns_ave) in sorted(average.items(), key=lambda x: x[1][1]):
    print(f'{name.rjust(W)}: {100. * de_ave / cell_count:7.3f} %'
        f' ({ns_ave / 1e6:6.3f} ms)'
    )
