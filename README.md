# LigerBots Membership Scripts

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

## Scripts

### merge_lists.py
* This combines two different team rosters.
* Uses email address as the key to match rows
* We want to preserve mods and extra columns from the master roster file (first file), so 
  the output is always defined by reading the file
* For historic reasons, not all members are signed up on the team's website, so we don't
  delete any rows. Slightly annoying.
* The script is a bit old, so uses some older syntax. Also, the "-G" mode has not been used
  in a long time.

### group_tool.py
* This takes a CSV list and syncs the emails and groups to our Google email groups
* The credential files are not included in the repo! They are cached in the same directory,
  so be careful about checking in.
* Uses "google_groups.py" to wrap some behavior. That file uses the modules provided by Google.
* You can preview what it will do if you do *not* give it the "--commit" command line option.

### present.py
* This is a generic CSV tool to find differences between 2 CSV files, based on set of key columns.
  <pre>present.py -c Column1 file1.csv file2.csv > output.csv</pre>
* This will look at "Column1" for both files and output the rows of *file2.csv* 
which are also found in file1.csv.
  <pre>present.py -m -c Column1,Column2 file1.csv file2.csv > output.csv</pre>
* This will look at "Column1" and "Column2" for both files and output the rows of *file2.csv* 
which are **not** found in file1.csv.
* So, the output file is always a set of rows from the 2nd file.
* Example: if you have fetch a CSV which lists all users (email) in some service, you can 
  find out if anyone is missing with:
   <pre>present.py -m -c email service_accounts.csv roster.csv > missed.csv</pre>
* You can use "-C" is the 2nd file column names are different.
* Use "-i" to ignore case when comparing key column values.
* Warning that column names are treated as case sensitive.

### joinCSV.py
* General tool to join rows of 2 CSV files.
* This is kind of a row-level "VLOOKUP" for CSVs (very loose comparison).
* The two CSV files are read and rows are merged if the specifed key columns match.
* The output is always the columns from file1 followed by the columns from file2.
* If a row has no match, the row is still output with blanks for the part that is missing.
* I use this to merge 2 roster or similar files and then pull it into a spreadsheet 
  for sorting, filtering etc. 