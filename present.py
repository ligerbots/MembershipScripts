#!/usr/bin/python3

# output rows from a CSV file depending on presence/absense of a key in another CSV file

# $Id: present.py 34825 2020-06-17 21:29:50Z prensing $

import sys
import argparse
import csv
import io


def val2str(v):
    if v is None:
        return None
    if isinstance(v, str) and not v:
        return None
    return str(v)


def map_fields(csv_iter, colnames):
    fieldmap = {x.lower(): x for x in csv_iter.fieldnames}
    return [fieldmap[y.lower()] for y in colnames]


parser = argparse.ArgumentParser(description='Rows from CVS file2 if key columns are present/missing from file1')
parser.add_argument('--columns', '-c', required=True, action='append', help='Columns to use as keys (comma separated)')
parser.add_argument('--second-columns', '-C', action='append', help='Key columns for file 2 (if different)')
parser.add_argument('--ignore-case', '-i', action='store_true', help='Ignore case of keys')
parser.add_argument('--missing', '-m', action='store_true', help='Output missing rows, instead of present rows')
parser.add_argument('file1', help='Input file 1')
parser.add_argument('file2', help='Input file 2')

args = parser.parse_args()

keys1List = []
for c in args.columns:
    keys1List.extend(c.split(','))

if args.second_columns:
    keys2List = []
    for c in args.second_columns:
        keys2List.extend(c.split(','))

    if len(keys1List) != len(keys2List):
        print("Number of key fields must be equal for both files", file=sys.stderr)
        parser.print_help()
        sys.exit(10)
else:
    keys2List = keys1List

with open(args.file1, 'r', encoding='utf_8_sig') as infile:
    csv_iter = csv.DictReader(infile)
    try:
        keys1List = map_fields(csv_iter, keys1List)
    except KeyError as e:
        print("Unknown column '%s' in first file" % e.args[0])
        sys.exit(11)

    existing = set()
    for row in csv_iter:
        key = []
        for c in keys1List:
            k = val2str(row[c])
            if args.ignore_case and k:
                k = k.lower()
            key.append(k)
        key = tuple(key)
        existing.add(key)

with open(args.file2, 'r', encoding='utf_8_sig') as infile:
    csv_iter = csv.DictReader(infile)
    try:
        keys2List = map_fields(csv_iter, keys2List)
    except KeyError as e:
        print("Unknown column '%s' in second file" % e.args[0])
        sys.exit(11)

    outstrm = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', newline='')
    outIter = csv.DictWriter(outstrm, fieldnames=csv_iter.fieldnames)
    outIter.writeheader()

    for row in csv_iter:
        key = []
        for c in keys2List:
            k = val2str(row[c])
            if args.ignore_case and k:
                k = k.lower()
            key.append(k)
        key = tuple(key)

        if args.missing:
            keep = key not in existing
        else:
            keep = key in existing
        if keep:
            outIter.writerow(row)
