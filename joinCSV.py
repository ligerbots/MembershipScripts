#!/usr/bin/python3

'''Join two CSV files using key columns'''

import sys
import argparse
import re
import string
import csv
import io
from copy import copy


def keyToken(token):
    key = str(token)

    if cleanWhitespace:
        key = re.sub(r'^\s+', '', key)
        key = re.sub(r'\s+$', '', key)
        key = re.sub(r'\s{2,}', ' ', key)

    if ignoreCase:
        key = key.lower()

    return key


def createKey(names, row, columns):
    try:
        key = map(lambda n: keyToken(row[columns.index(n)]), names)
    except Exception as e:
        print('names =', repr(names), file=sys.stderr)
        print('columns =', repr(columns), file=sys.stderr)
        raise e

    return tuple(key)


def loadFile(filename, keyList):
    with open(filename, 'r', encoding='utf_8_sig') as infile:
        incsv = csv.reader(infile)

        rowList = []
        entries = {}
        columns = next(incsv)

        # Check the key column names
        error = False
        for ke in keyList:
            for k in ke:
                if k not in columns:
                    print("ERROR: column '{}' does not exist in file '{}'".format(k, filename), file=sys.stderr)
                    error = True
        if error:
            return None, None, None

        line = -1
        for row in incsv:
            line += 1

            keyIndex = 0
            rowKeys = []
            for keyNames in keyList:
                key = createKey(keyNames, row, columns)
                entryKey = (keyIndex, key)
                if entryKey not in entries:
                    entries[entryKey] = []
                entries[entryKey].append(line)
                rowKeys.append(entryKey)
                keyIndex += 1

            rowList.append((row, tuple(rowKeys)))

    return rowList, entries, columns


parser = argparse.ArgumentParser(description='Join two CSV files')
parser.add_argument('--columns', '-C', required=True, action='append', help='Columns to use as keys (comma separated)')
parser.add_argument('--second-columns', '-D', action='append', help='Key columns for file 2 (if different)')
parser.add_argument('--ignore-case', '-i', action='store_true', help='Ignore case of keys')
parser.add_argument('--whitespace', '-w', action='store_true', help='Clean up whitespace before comparing keys')
parser.add_argument('--file-one-only', '-1', action='store_true', help='Lines from file 1 only')
parser.add_argument('--cumulative', '-P', action='store_true', help='Use the keys cumulatively')
parser.add_argument('file1', help='Input file 1')
parser.add_argument('file2', help='Input file 2')

args = parser.parse_args()

ignoreCase = args.ignore_case
cleanWhitespace = args.whitespace
allCombinations = False

keys1List = [keys.split(',') for keys in args.columns]

keys2List = []
if args.second_columns:
    keys2List = [keys.split(',') for keys in args.second_columns]
if not keys2List:
    keys2List = keys1List

# Validate the keys
if len(keys1List) != len(keys2List):
    print('Key lists not equal length', file=sys.stderr)
    parser.print_help()
    sys.exit(10)
for i in range(len(keys1List)):
    if len(keys1List[i]) != len(keys2List[i]):
        print('Key pair %d not equal length' % i, file=sys.stderr)
        parser.print_help()
        sys.exit(10)

# Read in file 1
file1Rows, file1Entries, file1Columns = loadFile(args.file1, keys1List)
if file1Rows is None:
    sys.exit(10)

# Read in file 2
file2Rows, file2Entries, file2Columns = loadFile(args.file2, keys2List)
if file2Rows is None:
    sys.exit(10)

# Figure out the column names
# First all the columns from file 1
output_columns = copy(file1Columns)

# Add the columns from file 2, checking for duplicate names
for n in file2Columns:
    index = 2
    name2 = n
    while name2 in output_columns and index < 100:
        name2 = '%s (%d)' % (n, index)
        index += 1
    if index >= 100:
        raise RuntimeError('Unable to create unique column name for %s' % n)
    output_columns.append(name2)

# Create the output iterator
out_csv = csv.writer(io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', newline=''))
out_csv.writerow(output_columns)

file2_used = len(file2Rows) * [False, ]
for row1, rowKeys in file1Rows:

    # Find the number of keys needed to specify a unique pair
    #  of lines in file1 and 2.
    lineSet1 = set()
    lineSet2 = set()
    for entryKey in rowKeys:
        myset = set(file1Entries.get(entryKey, []))
        if args.cumulative and lineSet1:
            lineSet1 = myset.intersection(lineSet1)
        else:
            lineSet1 = myset

        myset = file2Entries.get(entryKey, [])
        if args.cumulative and lineSet2:
            lineSet2 = myset.intersection(lineSet2)
        else:
            lineSet2 = myset

        if len(lineSet1) == 1 and len(lineSet2) == 1:
            break
        if args.cumulative and not lineSet2:
            break

    if not lineSet1:
        print('Something is wrong: lineset1 is empty', file=sys.stderr)
        sys.exit(1)

    if allCombinations or len(lineSet2) == 1:
        for l2 in lineSet2:
            try:
                row2 = file2Rows[l2][0]
            except Exception as e:
                print(lineSet2, file=sys.stderr)
                raise e

            output_row = copy(row1)
            output_row.extend(row2)
            out_csv.writerow(output_row)
            file2_used[l2] = True
    else:
        # need to extend the row so it has the correct number of columns
        output_row = []
        output_row.extend(row1)
        output_row.extend(len(file2Columns) * [None, ])
        out_csv.writerow(output_row)

if not args.file_one_only:
    # Output any rows from file two which have not already been done
    rowIndex = -1
    for row2, rowKeys in file2Rows:
        rowIndex += 1

        if file2_used[rowIndex]:
            continue
        output_row = len(file1Columns) * [None, ]
        output_row.extend(row2)
        out_csv.writerow(output_row)
