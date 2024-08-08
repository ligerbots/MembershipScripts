#!/usr/bin/python3

import httplib2
import logging

# from googleapiclient.discovery import build
# import googleapiclient.errors

from apiclient import discovery, errors
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage


class GoogleGroups:

    # If modifying these scopes, delete the file token.json.
    SCOPES = 'https://www.googleapis.com/auth/admin.directory.group'
    APPLICATION_NAME = 'LigerBotsGroups'

    def __init__(self, token_file, cred_file=None):
        self.credentials = self.get_credentials(token_file, cred_file=cred_file)
        self.http = self.credentials.authorize(httplib2.Http())
        self.service = discovery.build('admin', 'directory_v1', http=self.http)
        return

    def get_credentials(self, token_file, cred_file):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """

        store = Storage(token_file)
        credentials = store.get()
        if not credentials or credentials.invalid:
            if not cred_file:
                raise Exception("Need to specify credential file to reauthorize the token")
            flow = client.flow_from_clientsecrets(cred_file, self.SCOPES)
            flow.user_agent = self.APPLICATION_NAME
            # need blank command line arg structure
            flags = tools.argparser.parse_args(args=[])
            credentials = tools.run_flow(flow, store, flags)
            logging.info('Credentials were cached in %s', cred_file)

        return credentials

    def fetch_group_list(self, domain):
        """Fetch list of groups"""

        # Call the Admin SDK Directory API
        results = self.service.groups().list(domain=domain).execute()
        groups = results.get('groups', [])
        return groups

    def fetch_members(self, grp):
        """Fetch the members of a group"""

        req = self.service.members().list(groupKey=grp['id']).execute()
        members = req.get('members', [])
        res = set()
        for m in members:
            e = m.get('email', None)
            if e:
                res.add(e.lower())

        return res

    def delete_from_group(self, grp, members):
        for m in members:
            logging.info("Attempting to delete '%s' from '%s'", m, grp['name'])
            try:
                self.service.members().delete(groupKey=grp['id'], memberKey=m).execute()
            except errors.HttpError as e:
                logging.error('Error while deleting %s: %s', m, str(e))
        return

    def add_to_group(self, grp, members):
        for m in members:
            logging.info("Attempting to add '%s' to '%s'", m, grp['name'])
            try:
                self.service.members().insert(groupKey=grp['id'], body={'email': m}).execute()
            except errors.HttpError as e:
                logging.error('Error while adding %s: %s', m, str(e))
        return
