#!/usr/bin/python3

# Merge the two Ligerbots email lists

import sys
import csv
import getopt
import re
import datetime


addMembers = {}
delMembers = {}


def usage(msg=None):
    if msg:
        print(msg, file=sys.stderr)

    print("merge_lists.py <spreadsheet_csv> <db_dump_csv>", file=sys.stderr)
    print("Flags:", file=sys.stderr)
    print("  -G       Compare to Google email groups", file=sys.stderr)
    print("Output to stdout", file=sys.stderr)
    sys.exit(1)
    return


def formatPhone(instr):
    m = re.match(r'^(?P<ac>\d{3})(?P<ex>\d{3})(?P<n>\d{4})$', instr)
    if m:
        return '%s-%s-%s' % (m.group('ac'), m.group('ex'), m.group('n'))
    m = re.match(r'^\((?P<ac>\d{3})\)[ -]*(?P<ex>\d{3})[ -]*(?P<n>\d{4})$', instr)
    if m:
        return '%s-%s-%s' % (m.group('ac'), m.group('ex'), m.group('n'))
    return instr


def mergeGroups(entry, newE):
    oldEmail = entry.get('Email', None)
    newEmail = newE.get('Email', None)

    if not newEmail:
        return

    school = newE['School']
    if not school and entry.get('School', None):
        school = entry.get('School', None)

    if entry.get('Groups', None) and oldEmail:
        oldGroups = set([x.lower().strip() for x in entry['Groups'].split(',')])
    else:
        oldGroups = set()

    newGroups = set([x.lower().strip() for x in newE['Groups'].split(',')])

    if 'head_coach' in oldGroups:
        newGroups = set(('head_coach',))

    # Add to groups
    if oldEmail != newEmail:
        toadd = newGroups
    else:
        toadd = newGroups.difference(oldGroups)
    for g in toadd:
        g2 = g
        if g in ('student', 'parent'):
            g2 = '%s_%s' % (g, school)

        memlist = addMembers.setdefault(g2, [])
        memlist.append(newEmail)

    # Delete from groups
    if oldEmail != newEmail:
        todel = oldGroups
    else:
        todel = oldGroups.difference(newGroups)

    for g in todel:
        g2 = g
        if g in ('student', 'parent'):
            g2 = '%s_%s' % (g, school)

        memlist = delMembers.setdefault(g2, [])
        memlist.append(oldEmail)

    return


def mergeEntry(fields, entry, newE):

    if not entry.get('Email', None):
        newE['SignupDate'] = datetime.date.today().strftime('%Y-%m-%d')

    mergeGroups(entry, newE)
    # if n: print('groups:', entry)

    for f in fields:
        if newE.get(f, None):
            entry[f] = newE[f]
    # if n: print('merged:', entry)

    return


def compareSheetWeb(docFile, dbFile):

    # load the main dictionary from docFile
    f = open(docFile)
    csvIn = csv.reader(f)
    fields = next(csvIn)
    f.seek(0, 0)

    csvIn = csv.DictReader(f)
    refEntries = [r for r in csvIn]
    f.close()

    # create a few indices of the existing users
    usernames = {}
    emails = {}
    for e in refEntries:
        if e.get('Email', None):
            e['Email'] = e['Email'].lower()
        e['HasWebAccount'] = ''

        if e['Lastname'] and e['Firstname']:
            usernames[(e['Lastname'], e['Firstname'])] = e
        if e['Email']:
            emails[e['Email']] = e

    # Now, go through the other file and merge in any changes
    f = open(dbFile)
    csvIn = csv.DictReader(f)
    for newE in csvIn:
        for k, v in newE.items():
            newE[k] = v.strip()
            if newE[k] == 'NULL':
                newE[k] = None
            if k == 'Email':
                newE[k] = newE[k].lower()

        oldE = emails.get(newE['Email'], None)
        if oldE is None:
            key = (newE['Lastname'], newE['Firstname'])
            oldE = usernames.get(key, None)

        if oldE is None:
            oldE = {}
            refEntries.append(oldE)

        oldE['HasWebAccount'] = 1
        mergeEntry(fields, oldE, newE)

    # clean up some fields. Make sure to go through the whole list
    for entry in refEntries:
        if entry.get('Phone', None):
            entry['Phone'] = formatPhone(entry['Phone'])
        if entry.get('Emergency_Phone', None):
            entry['Emergency_Phone'] = formatPhone(entry['Emergency_Phone'])

        if re.match(r'^\d{4}$', entry['Zipcode']):
            entry['Zipcode'] = '0' + entry['Zipcode']
        if re.match(r'^\d', entry['Zipcode']):
            entry['Zipcode'] = "'" + entry['Zipcode']

    # Done. Output the list
    csvOut = csv.DictWriter(sys.stdout, fieldnames=fields, extrasaction='ignore')
    # need to output header
    csvOut.writeheader()

    for e in refEntries:
        csvOut.writerow(e)

    print('Add lists:', file=sys.stderr)
    for k, v in sorted(addMembers.items()):
        print(k, "\t", ', '.join(v), file=sys.stderr)

    print('', file=sys.stderr)
    print('Delete lists:', file=sys.stderr)
    for k, v in sorted(delMembers.items()):
        print(k, "\t", ', '.join(v), file=sys.stderr)

    return


def compareGoogleSheet(googleFile, docFile):
    # load the Group membership data
    groups = {}
    f = open(googleFile)
    csvIn = csv.DictReader(f)
    for row in csvIn:
        grp = row['Group'].strip().lower()
        grpList = groups.get(grp, None)
        if not grpList:
            grpList = []
            groups[grp] = grpList
        grpList.append(row['Email'].strip().lower())
    f.close()

    # Now, go through the other file and merge in any changes
    f = open(docFile)
    csvIn = csv.DictReader(f)
    for row in csvIn:
        email = row['Email'].strip().lower()
        if not email:
            continue

        school = row['School'].strip().lower()
        isParent = re.search(r'parent', row['Groups'], re.IGNORECASE)

        for grp in row['Groups'].split(','):
            grp = grp.strip()

            if grp in ('student', 'parent'):
                grpName = '%s_%s' % (grp, school)
                grpName = grpName.lower()
            elif grp == 'mentor':
                if isParent:
                    grpName = 'mentor_parent'
                else:
                    grpName = 'mentor_other'
            else:
                grpName = grp
            if grpName in ('exec', 'alumni', 'alum'):
                continue

            grpList = groups.get(grpName, None)
            if not grpList:
                print('Unknown group "%s" for "%s"' % (grpName, email), file=sys.stderr)
                continue

            if email in grpList:
                grpList.remove(email)
            else:
                x = addMembers.get(grpName, None)
                if not x:
                    x = []
                    addMembers[grpName] = x
                x.append(email)

    print('Add lists:')
    for k, v in sorted(addMembers.items()):
        print(k, "\t", ', '.join(v))

    print
    print('Delete lists:')
    for k, v in sorted(groups.items()):
        if v:
            print(k, "\t", ', '.join(v))


# ------------------------------------------------------------
if __name__ == '__main__':
    try:
        optlist, pargs = getopt.getopt(sys.argv[1:], 'G')
    except Exception:
        usage('Unknown option')

    if len(pargs) != 2:
        usage()

    # convert opts to something useful!!!
    opts = {}
    for x in optlist:
        opts[x[0]] = x[1]

    if '-G' in opts:
        compareGoogleSheet(pargs[0], pargs[1])
    else:
        compareSheetWeb(pargs[0], pargs[1])
