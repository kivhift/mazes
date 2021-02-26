#
# Copyright (c) 2021 Joshua Hughes <kivhift@gmail.com>
#
# SPDX-License-Identifier: MIT
#
from random import choice, randint

names = set()
def register_algo(fn):
    names.add(fn.__name__)
    return fn

@register_algo
def binary_tree(grid):
    for cell in grid.each_cell:
        if neighbors := list(filter(None, (cell.N, cell.E))):
            cell.link(choice(neighbors))

    return grid

@register_algo
def sidewinder(grid):
    run = []
    run_append = run.append

    for row in grid.each_row:
        run.clear()
        for cell in row:
            run_append(cell)
            at_E = cell.E is None
            not_at_N = cell.N is not None
            if at_E or (not_at_N and randint(0, 1)):
                member = choice(run)
                run.clear()
                if member.N:
                    member.link(member.N)
            else:
                cell.link(cell.E)

    return grid

@register_algo
def aldous_broder(grid):
    cell = grid.random_cell
    unvisited = grid.size - 1

    while unvisited:
        neighbor = cell.random_neighbor

        if not neighbor.links:
            cell.link(neighbor)
            unvisited -= 1

        cell = neighbor

    return grid

def remove_random(L):
    i = randint(0, len(L) - 1)
    ele = L[i]
    del L[i]

@register_algo
def wilsons(grid):
    unvisited = list(grid.each_cell)
    remove_random(unvisited)

    while unvisited:
        cell = choice(unvisited)
        path = [cell]

        while cell in unvisited:
            cell = cell.random_neighbor
            if cell in path:
                path = path[:path.index(cell) + 1]
            else:
                path.append(cell)

        for i in range(len(path) - 1):
            path[i].link(path[i + 1])
            unvisited.remove(path[i])

    return grid

@register_algo
def hunt_and_kill(grid):
    current = grid.random_cell
    while current:
        if unvisited_neighbors := current.neighbors_without_links:
            neighbor = choice(unvisited_neighbors)
            current.link(neighbor)
            current = neighbor
        else:
            current = None

            for cell in grid.each_cell:
                visited_neighbors = cell.neighbors_with_links
                if not cell.has_links and visited_neighbors:
                    current = cell
                    neighbor = choice(visited_neighbors)
                    current.link(neighbor)
                    break

    return grid

@register_algo
def recursive_backtracker(grid, start=None):
    stack = []
    push, pop, top = stack.append, stack.pop, lambda: stack[-1]
    push(start or grid.random_cell)

    while stack:
        current = top()
        if unvisited_neighbors := current.neighbors_without_links:
            neighbor = choice(unvisited_neighbors)
            current.link(neighbor)
            push(neighbor)
        else:
            pop()

    return grid

del register_algo
