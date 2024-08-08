#!/usr/bin/python3

# import sys
import csv
import logging
import argparse
import google_groups


HACK_EXTRA_EMAILS = {'dr.ljkraus@gmail.com': 'jordan_kraus@newton.k12.ma.us',
                     'diane.levy@ligerbots.org': 'dfldesign@levymeister.com',
                     'john_sangiolo@netropa.com': 'sangioloj@gmail.com',
                     # 'pamwright@rcn.com': '1pamwright@gmail.com',
                     }

# Head coaches want to be in a Parent group to monitor it
HEAD_COACH_GROUPS = ('Coaches', 'Parents - North', 'Execs')

# NOTES:
#  GMail does not care about "." in email names, but will return the "official" name.
#   So we may need to update the directory to make it match

SITE = 'nsf'


def load_google_groups(server, domain):
    '''Load the groups and members of all the Google groups'''

    groups = server.fetch_group_list(domain)

    res = {}
    for grp in groups:
        members = server.fetch_members(grp)
        assert 'members' not in grp
        grp['members'] = members
        res[grp['name']] = grp

    return res


def _add_member(grp_dict, grpname, email):
    g = grp_dict.get(grpname, None)
    if not g:
        g = set()
        grp_dict[grpname] = g
    g.add(email)
    return


def load_file(filename):
    '''Load the groups from the directory CSV file'''

    res = {}
    with open(filename, 'r') as f:
        csvin = csv.DictReader(f)
        for row in csvin:
            email = row['Email'].lower()
            if not email:
                logging.info('Empty email: %s', repr(row))
                continue

            school = row['School']
            groups = [g.lower().strip() for g in row['Groups'].split(',')]
            for grp in groups:
                gl = grp.lower()

                if gl == 'head_coach':
                    for g2 in HEAD_COACH_GROUPS:
                        _add_member(res, g2, email)
                    continue

                grpname = None
                if gl == 'coach':
                    grpname = 'Coaches'
                elif gl == 'mentor':
                    if 'parent' in groups:
                        grpname = 'Mentors - Parent'
                    else:
                        grpname = 'Mentors - Other'
                elif gl == 'parent':
                    grpname = 'Parents - ' + ('North' if school == 'North' else 'South')
                elif gl == 'student':
                    grpname = 'Students - ' + ('North' if school == 'North' else 'South')
                elif gl == 'community':
                    grpname = 'Community'
                elif gl == 'exec':
                    grpname = 'Execs'
                elif gl in ('alumni', 'alum'):
                    grpname = 'Alumni'
                else:
                    logging.error("Unknown group type '%s'", grp)

                if grpname:
                    if SITE == 'nsf':
                        grpname = 'LigerBots ' + grpname
                    _add_member(res, grpname, email)

    return res


def list_groups(google, groups=None):
    '''Print out the content of the Google groups'''

    for grpname, grp in sorted(google.items()):
        if groups and grpname not in groups:
            continue

        print('{}:'.format(grpname))
        for m in sorted(grp['members']):
            print('   {}'.format(m))
    return


def diff_ignore_period(list1, list2):
    list1a = [m.replace('.', '') for m in list1]
    diff = []
    for m in list2:
        m2 = m.replace('.', '')
        if m2 not in list1a:
            diff.append(m)
    return diff


def sync_groups(server, directory, google_grps, groups=None, commit=False):
    for grpname, members in sorted(directory.items()):
        if grpname in ('Execs', 'Alumni', 'LigerBots Execs', 'LigerBots Alumni'):
            continue
        if groups and grpname not in groups:
            continue

        for e1, e2 in HACK_EXTRA_EMAILS.items():
            if e1 in members:
                members.add(e2)

        g_grp = google_grps[grpname]
        g_members = g_grp['members']

        add_to_google = diff_ignore_period(g_members, members)
        del_from_google = diff_ignore_period(members, g_members)
        if add_to_google or del_from_google:
            print('{}:'.format(grpname))
        if del_from_google:
            print('  Del: {}'.format(', '.join(del_from_google)))
            if commit:
                server.delete_from_group(g_grp, del_from_google)
        if add_to_google:
            print('  Add: {}'.format(', '.join(add_to_google)))
            if commit:
                server.add_to_group(g_grp, add_to_google)

    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Work with Google groups')
    parser.add_argument('--cred', help='Credential secret file. Only if token is invalid/missing')
    if SITE == 'nsf':
        parser.add_argument('--token', default='token_nsf.json', help='Token file')
        parser.add_argument('--domain', default='ligerbots.org', help='Primary domain name')
    else:
        parser.add_argument('--token', default='token_liger.json', help='Token file')
        parser.add_argument('--domain', default='ligerbots.com', help='Primary domain name')

    parser.add_argument('--sync', help='Sync groups with CSV directory file')
    parser.add_argument('--list', action='store_true', help='List the Google groups')
    parser.add_argument('--group', action='append', help='Group name (multiple allowed)')
    parser.add_argument('--commit', action='store_true', help='Commit changes to groups')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose')
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)
    logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

    server = google_groups.GoogleGroups(args.token, cred_file=args.cred)

    logging.info('loading google groups')
    group_info = load_google_groups(server, args.domain)
    # pprint.pprint(google)

    if args.list:
        list_groups(group_info, groups=args.group)
    elif args.sync:
        logging.info('loading directory file')
        directory = load_file(args.sync)
        # pprint.pprint(directory)
        sync_groups(server, directory, group_info, groups=args.group, commit=args.commit)
