LigerBots Membership Scripts

These are a few scripts used to manage the LigerBots team membership.

The LigerBots maintain a set of email lists in our Google account.
There are lists for Parents, Students, Mentors and Coaches. Also, since we have
the 2 high schools, the Parent and Student lists are split by the school.
Within Google, there are additional email lists which merge various lists
(e.g. "parents" combines both high school parent lists), culminating in our
all-encompassing "team@ligerbots.org" email list.

All students and coaches are invited to the team's Slack. 
Parents are not, in fact, invited because of youth protection rules. If they wish, 
they can go through the background checks and become Mentors.

So the general procedure is as follows:
* New members sign up on the team's website. The signup form requires basic information
  like name, email, team role (student, parent, etc), parent contact info, etc.
* New website signups must be (manually) approved: students must be Newton Public School students,
  parents must have children on the team (or choose to be a Mentor).
* When there are new, approved signups, I download the roster from the website as a CSV.
* The master roster is download from Google Drive, again as a CSV.
* The script "merge_list.py" is run to merge any changes from the website into the master list:
    <pre>merge_lists.py master_roster.csv  website_roster.csv  > new_roster.csv</pre>
* The output "new_roster.csv" is uploaded back to Google Drive to become the new master roster
  (I generally overwrite the existing sheet).
* The script "group_tool.py" is used to update the Google email groups based on the new roster:
    <pre>group_tool.py --sync new_roster.csv --commit</pre>
  You can leave out "--commit" to see what it will do.
* New students are manually invited to the team Slack, using the email they provided.

Right now, removing people from the team is mostly manual. The one "automation" is that,
once a person is removed from the master roster (and the website!), running a sync with group_tool.py
will remove them from the Google email lists.