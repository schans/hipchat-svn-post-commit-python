#!/usr/bin/python

# post-commit: Hook used for SVN post commits
#
# Scott Vitale
# svvitale@gmail.com

# This script is set to publish information after SVN commits to HipChat. 
#
# Required files/Application/services:
#     * Subversion: http://subversion.tigris.org/
#     * Working repository
#     * HipChat account and room setup: https://www.hipchat.com/
#     * HipChat token created: https://www.hipchat.com/groups/api
#
import os
import sys
import subprocess
import getopt
import urllib
import urllib2
import re

# Set hipchat info
#
TOKEN="<token>"
ROOM="<room name>"
NAME="Subversion"

# svnlook location
LOOK="/usr/bin/svnlook"

##############################################################
##############################################################
############ Edit below at your own risk #####################
##############################################################
##############################################################

def sendToHipChat( msg, token, room, name ):
	# replace newlines with XHTML <br />
	msg = msg.replace("\r", "").replace("\n", "<br />")

	# replace bare URLs with real hyperlinks
	msg = re.sub( r'(?<!href=")((?:https?|ftp|mailto)\:\/\/[^ \n]*)', r'<a href="\1">\1</a>', msg)

	# create request dictionary
	request = {
		'auth_token': token,
		'room_id': room,
		'from': name,
		'message': msg,
		'notify': 1,
	}

	# urlencode and post
	urllib2.urlopen( "https://api.hipchat.com/v1/rooms/message", urllib.urlencode( request ) )
  
def runLook( *args ):
        return subprocess.Popen([LOOK] + list(args), stdout=subprocess.PIPE).stdout.read()

def getCommitInfo( repo, revision ):
	comment = runLook("log", repo, "-r", revision)
	author = runLook("author", repo, "-r", revision)
	files = runLook("changed", repo, "-r", revision)

	chatMsg = ("""
%s r%s : %s
%s
""" % (author.strip(), revision, comment.strip(), files)).strip()
  
	return chatMsg

def main():
        repository = False
        revision = False
        try:
                opts, args = getopt.getopt(sys.argv[1:], "r:s:", ["revision=", "repository="])
        except getopt.GetoptError, err:
                print >>sys.stderr, str(err)
                print "Usage:"
                print "hipchat-svn-post-commit.py -r <revision> -s <repository>"
                sys.exit(2)
        for o, a in opts:
                if o in ("-r", "--revision"):
                       revision = a
                elif o in ("-s", "--repository"):
                       repository = a

        if not revision:
                print "Sepcify a revision with -r or --revision"
                sys.exit(2)
        if not repository:
                print "Specify a repository with -s or --repository"
                sys.exit(2)

	chatMsg = getCommitInfo( repository, revision )
	sendToHipChat( chatMsg, TOKEN, ROOM, NAME )

if __name__ == "__main__":
	main()
