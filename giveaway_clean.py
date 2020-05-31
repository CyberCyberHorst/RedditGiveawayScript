import praw
import argparse
import re
import random

# These are defaults. Instead of using them, you can startup the script with the optional args (see "python giveaway.py -h")
default_client="Insert client ID here"
default_secret="insert API secret here"
default_username="Insert your Username here"
default_password="Insert your password here"

raffle_regex="^[1{1},2{1},3{1}]{1,3}" # Regex String to match for the raffle The default matches a priority list of 1-3 

prizes=[
    {    
        "name":"Game 1", # Only used in winner message
        "referenceInRegex":"1", # Single digit or character in raffle_regex
        "secret":"<Code>", # Insert Steam code or similar secret for the winner here
        "gone":False # Always initialize as False
    },
    {
        "name":"Game 2",
        "referenceInRegex":"2",
        "secret":"<Code>",
        "gone":False
    },
    {
        "name":"Game 3",
        "referenceInRegex":"3",
        "secret":"<Code>",
        "gone":False
    }
]

#parse args

parser = argparse.ArgumentParser()
parser.add_argument("threadID", help="A reddit base36 submission ID, e.g., 2gmzqe")
parser.add_argument("-u","--user",help="Enter user here if you don't want to edit the script")
parser.add_argument("-p","--passw",help="Enter passwort. Required if using -u")
parser.add_argument("-c","--client",help="Enter clientID. Required if using -u")
parser.add_argument("-s","--secret",help="Enter client secret. Required if using -u")
args = parser.parse_args()

# create reddit instance

if args.user is not None:
    if args.passw is not None and args.client is not None and args.secret is not None:
        reddit = praw.Reddit(client_id=args.client,
                     client_secret=args.secret,
                     password=args.passw,
                     user_agent="GiveawayScript by /u/CyberCyberHorst", # Please keep this
                     username=args.user)
    else:
        raise ValueError("If you use -u, also use -p -c and -s.")
else:
    reddit = praw.Reddit(client_id=default_client,
                     client_secret=default_secret,
                     password=default_password,
                     user_agent="GiveawayScript by /u/CyberCyberHorst",
                     username=default_username)

# Get post as object

submission = reddit.submission(id=args.threadID)
if submission is None:
    raise ValueError("The specified thread does not exist.")

# Get all regex Matching top-level comments

validComments = []

for top_level_comment in submission.comments:
    if re.search(raffle_regex,top_level_comment.body) is not None:
        validComments.append(top_level_comment)
    
#We have all top level comments matching the raffle RegEx. Now we purge double entries

doubleEntries = []
uniqueUsers= []

# get all users who entered two valid comments
for candidate in validComments:
    if candidate.author not in doubleEntries:
        if candidate.author not in uniqueUsers:
            uniqueUsers.append(candidate.author)
        else:
            uniqueUsers.remove(candidate.author)
            doubleEntries.append(candidate.author)

# save all valid comments from unique posters
cleanedComments = [] 
for candidate in validComments:
    if candidate.author in uniqueUsers:
        cleanedComments.append(candidate)

# Randomize comment List

random.shuffle(cleanedComments)


# extract Winner Priority lists and assign Prizes

numberOfWinners=len(prizes)
awarded = 0
offset=0
while(awarded<numberOfWinners):
    if awarded+offset >= len(cleanedComments):
        print("Prizes that not have been awarded, because nobody wanted them:")
        for prize in prizes:
            if prize["gone"] is False:
                print(prize["name"])
        sys.exit()
    prioList = re.search(raffle_regex,cleanedComments[awarded+offset].body)
    print(str(cleanedComments[awarded+offset].author)+" has prio list "+prioList.group())
    currentUserAwarded=False
    position = 0
    while currentUserAwarded is False:
        regExRep = str(prioList.group()[position])
        foundPrize = None
        for prize in prizes:
            if prize["referenceInRegex"] == regExRep and prize["gone"] == False:
                foundPrize=prize
                prize["gone"]=True
        if foundPrize is not None:
            print (cleanedComments[awarded+offset].author.name+" receives "+foundPrize["name"])
            # Winner message containing the secret
            winnerMessage="Congratulations, "+cleanedComments[awarded+offset].author.name+"\n\n you were winner number "+str((awarded+1))+" in my raffle. \n You won number "+str((position+1))+" in your priority list: "+foundPrize["name"]+". This is your code: \n\n "+foundPrize["secret"]+" \n\n This is a automated message by the giveaway script. GL&HF"
            # print(winnerMessage)
            # Send to winner
            reddit.redditor(cleanedComments[awarded+offset].author.name).message("You won!", winnerMessage)
            currentUserAwarded=True
            awarded=awarded+1
        else:
            position=position+1
            if position >= len(prioList.group()):
                loserMessage="Hello "+cleanedComments[awarded+offset].author.name+"\n You were selected as winner in "+str((awarded+1))+" place, but all your priorized prizes were already gone. Better luck next time."
                reddit.redditor(cleanedComments[awarded+offset].author.name).message("Better luck next time!", loserMessage)
                print(loserMessage)
                currentUserAwarded=True
                offset=offset+1
