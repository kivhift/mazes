#!/usr/bin/env python3
#
# Copyright (c) 2021 Joshua Hughes <kivhift@gmail.com>
#
# SPDX-License-Identifier: MIT
#
import argparse
import pathlib
import sys

import maze.algorithm
import maze.grid
import maze.output

class HelpFormatter(argparse.RawTextHelpFormatter
        , argparse.ArgumentDefaultsHelpFormatter):
    pass

def main(args_list=None):
    arg_parser = argparse.ArgumentParser(description='Make a maze'
        , formatter_class=HelpFormatter)
    _a = arg_parser.add_argument
    _a('-a', '--algorithm', default='binary_tree'
        , choices=sorted(maze.algorithm.names)
        , help='Maze-generation algorithm to use')
    _a('-c', '--color', action='store_true', help='Color output')
    _a('-f', '--format', choices=sorted(maze.output.formats)
        , help='Output format to use')
    _a('-m', '--mask', help='RLE (file) to use as mask')
    _a('-o', '--output', help='File to output to')
    _a('-p', '--print', action='store_true', help='Print maze to stdout')
    _a('-s', '--scale', type=float, default=1., help='Amount to scale drawing by')
    _a('-H', '--height', default=5, type=int, help='Maze height')
    _a('-W', '--width', default=5, type=int, help='Maze width')
    _a('--gui', choices='mask maze'.split()
        , help='Short circuit everything and open specified GUI')
    args = arg_parser.parse_args(args_list or sys.argv[1:])

    if args.gui is not None:
        if 'mask' == args.gui:
            from maze.widgets import mask_edit_main
            mask_edit_main()
        elif 'maze' == args.gui:
            from maze.widgets import maze_main
            maze_main()
        else:
            raise SystemExit(f'Invalid GUI: {args.gui}')

    if args.height < 1:
        raise SystemExit(f'Height should be positive: {args.height}')
    if args.width < 1:
        raise SystemExit(f'Width should be positive: {args.width}')

    gen_algo = getattr(maze.algorithm, args.algorithm)

    if args.mask is not None:
        mask_path = pathlib.Path(args.mask)
        if mask_path.exists():
            with mask_path.open() as mask_in:
                args.mask = mask_in.read()
        g = gen_algo(maze.grid.MaskedColoredGrid(maze.grid.Mask.from_RLE(args.mask)))
    else:
        g = gen_algo(maze.grid.ColoredGrid(args.height, args.width))

#    ###
#    g = gen_algo(maze.grid.ColoredGrid(args.height, args.width))
#    start, _ = g[0, 0].distances.max
#    distances = start.distances
#    goal, _ = distances.max
#    g.distances = distances.path_to(goal)

    if args.print:
        print(g)

    if args.output:
        if args.format is None:
            raise SystemError('Must specify an output format')

        if args.scale <= 0.0:
            raise SystemError('Scale must be greater than 0')

        if args.color:
            g.distances = g.random_cell.distances

        to_format = getattr(maze.output, f'to_{args.format}')
        with open(args.output, 'wb') as f:
            to_format(g, f, scale=args.scale)

if '__main__' == __name__:
    main()
