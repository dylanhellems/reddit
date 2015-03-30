#/u/GoldenSights
import traceback
import praw  # simple interface to the reddit API, also handles rate limiting of requests
import time
import datetime
import sqlite3
import re
from populate_db import populate_db, fetch_word

'''USER CONFIGURATION'''

# This is the bot's Username. In order to send mail, he must have some amount of Karma.
USERNAME = ""

# This is the bot's Password.
PASSWORD = ""

# This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
USERAGENT = ""

# This is the sub or list of subs to scan for new posts. For a single sub, use "sub1".
# For multiple subreddits, use "sub1+sub2+sub3+..."
SUBREDDIT = "whatisthewordconky+GoldTesting+FreeKarma"

# Current date
DATE = datetime.datetime.now().date()

# Populate database with words
populate_db()

# These are the words you are looking for
KEYWORDS = []

# These are the names of the authors you are looking for
# Any authors not on this list will not be replied to.
# Make empty to allow anybody
KEYAUTHORS = []

#This is the word you want to put in reply
REPLYSTRING = "AHHHHHHHHHHHHHHHHHHHHHHHHH!\n\n You said today's Secret Word: \"%s\"" \
              + ". Remember to scream real loud whenever you hear someone say the Secret Word!\n\n" \
                "Check /r/whatisthewordconky each day to find out what it is.\n\n Oh, and /u/%s, how do" \
                " you like today's Secret Word?"

#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
MAXPOSTS = 100

#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.
WAIT = 20

#HH:MM Format
#TWENTY-FOUR HOUR STYLE
#EST Timezone
PTIME = "00:00"

#The Following Post title and Post text can be customized using the strftime things
#    https://docs.python.org/2/library/time.html#time.strftime
#    Ex: "Daily thread for %A %B %d %Y" = "Daily thread for Tuesday November 04 2014"
#Don't forget that the text will be wrung through reddit Markdown
PTITLE = "%s: Today's Secret Word is \"%s\""
PTEXT = "Remember to scream real loud whenever you hear someone say the Secret Word!"

'''All done!'''

try:
    # This is a file in my python library which contains my
    # Bot's username and password.
    # I can push code to Git without showing credentials
    import bot
    USERNAME = bot.username
    PASSWORD = bot.password
    USERAGENT = bot.useragent
except ImportError:
    pass

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

# cur.execute('DROP TABLE IF EXISTS oldposts')
cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
print('Loaded Completed table: oldposts')

cur.execute('DROP TABLE IF EXISTS posts')
cur.execute('CREATE TABLE IF NOT EXISTS posts(ID TEXT, STAMP TEXT, CREATED INT, Word TEXT)')
print('Loaded Completed table: posts')

sql.commit()
print('Commited\n')

print('Logging in...\n')
r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD)

ptime = PTIME.split(':')
ptime = (60*int(ptime[0])) + int(ptime[1])


def conkybot():
    print('Searching %s.' % SUBREDDIT)
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = subreddit.get_comments(limit=MAXPOSTS)
    for post in posts:
        # Anything that needs to happen every loop goes here.
        pid = post.id

        try:
            pauthor = post.author.name
        except AttributeError:
            #Author is deleted. We don't care about this post.
            continue

        if KEYAUTHORS and all(auth.lower() != pauthor.lower() for auth in KEYAUTHORS):
            # This post was not made by a keyauthor
            continue

        cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
        if cur.fetchone():
            # Post is already in the database
            continue

        cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
        sql.commit()
        pbody = post.body.lower()
        if any(re.search(r'\b' + key + r'\b', pbody) is not None for key in KEYWORDS):
            if pauthor.lower() != USERNAME.lower():
                print('Replying to ' + pid + ' by ' + pauthor)
                try:
                    post.reply(REPLYSTRING % (KEYWORDS[0], pauthor))
                except Exception:
                    print('I\'ll try again in a bit')
                    cur.execute('DELETE FROM oldposts WHERE ID=?', [pid])
            else:
                print('Will not reply to myself')


def dailypost():
    global KEYWORDS
    #I want to ping reddit on every cycle. I've had bots lose their session before
    subreddit = r.get_subreddit("whatisthewordconky", fetch=True)
    now = datetime.datetime.now()
    daystamp = datetime.datetime.strftime(now, "%d%b%Y")
    cur.execute('SELECT * FROM posts WHERE STAMP=?', [daystamp])
    nowtime = (60*now.hour) + now.minute
    print('Now: ' + str(nowtime) + ' ' + datetime.datetime.strftime(now, "%H:%M"))
    print('Pst: ' + str(ptime) + ' ' + PTIME)
    last = cur.fetchone()
    if not last:
        diff = nowtime-ptime
        if diff > 0:
            print('t+ ' + str(abs(diff)) + ' minutes')
            makepost(now, daystamp)
        else:
            print('t- ' + str(diff) + ' minutes')
    else:
        print("Already made today's post")
        if not KEYWORDS:
            print(DATE)
            KEYWORDS = [last[3]]
            print("Secret Word is " + KEYWORDS[0] + "\n")


def makepost(now, daystamp):
    global DATE, KEYWORDS
    DATE == datetime.datetime.now().date()
    print(DATE)
    KEYWORDS = [fetch_word()]
    print("Secret Word is " + KEYWORDS[0] + "\n")

    print('Making post...')
    ptitle = datetime.datetime.strftime(now, PTITLE % (DATE, KEYWORDS[0]))
    ptext = datetime.datetime.strftime(now, PTEXT)
    try:
        newpost = r.submit("whatisthewordconky", ptitle, text=ptext, captcha=None)
        print('Success: ' + newpost.short_link)
        cur.execute('INSERT INTO posts VALUES(?, ?, ?, ?)', [newpost.id, daystamp, newpost.created_utc, KEYWORDS[0]])
        sql.commit()
    except praw.requests.exceptions.HTTPError as e:
        print('ERROR: PRAW HTTP Error.', e)


while True:
    try:
        dailypost()
    except Exception as e:
        traceback.print_exc()
    print()
    try:
        conkybot()
    except Exception as e:
        traceback.print_exc()
    print('Running again in %d seconds \n' % WAIT)
    time.sleep(WAIT)
