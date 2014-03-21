#!/usr/bin/python

# post-commit: Hook used for SVN post commits
#
# Scott Vitale
# svvitale@gmail.com

#
# Set config values in code, command line, or config file.
#

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
import ConfigParser
import threading

# Default room name
ROOM = "<room name>"

# Default token
TOKEN = "<token>"

# Default chat user name
NAME = "Subversion"

# Default config
CONFIG = "/etc/svn/hipchat.cfg"

# Default svnlook location
svnlook = "/usr/bin/svnlook"

#
#
# Edit below at your own risk #####################
#
#


def sendToHipChat(msg, token, room, name):
    # replace newlines with XHTML <br />
    msg = msg.replace("\r", "").replace("\n", "<br />")

    # replace bare URLs with real hyperlinks
    msg = re.sub(
        r'(?<!href=")((?:https?|ftp|mailto)\:\/\/[^ \n]*)', r'<a href="\1">\1</a>', msg)

    # create request dictionary
    request = {
        'auth_token': token,
        'room_id': room,
        'from': name,
        'message': msg,
        'notify': 1,
    }

    # urlencode and post
    urllib2.urlopen("https://api.hipchat.com/v1/rooms/message",
                    urllib.urlencode(request))


def runLook(*args):
        return subprocess.Popen([svnlook] + list(args), stdout=subprocess.PIPE).stdout.read()


def getCommitInfo(repo, revision):
    comment = runLook("log", repo, "-r", revision)
    author = runLook("author", repo, "-r", revision)
    files = runLook("changed", repo, "-r", revision)


    url_path = files.split()

    chatMsg = ("""
%s r%s : %s
%s : https://svn.onehippo.org/repos/closed/%s?p=%s
""" % (author.strip(), revision, comment.strip(), files, url_path[1], revision)).strip()


    return chatMsg


def main():
    revision = False
    repository = False
    cmd_config = False
    cmd_token = False
    cmd_name = False
    cmd_room = False

    try:
        opts, args = getopt.getopt(
            sys.argv[1:], "r:s:f:k:t:u:", ["revision=", "repository=", "config=", "room=", "token=", "user="])
    except getopt.GetoptError, err:
        print >>sys.stderr, str(err)
        print "Usage:"
        print "hipchat-svn-post-commit.py -r <revision> -s <repository> [-f config] [-k room] [-t token] [-n name]"
        sys.exit(1)
    for o, a in opts:
        if o in ("-r", "--revision"):
            revision = a
        elif o in ("-s", "--repository"):
            repository = a
        elif o in ("-k", "--room"):
            cmd_room = a
        elif o in ("-t", "--token"):
            cmd_token = a
        elif o in ("-n", "--name"):
            cmd_name = a
        elif o in ("-f", "--config"):
            cmd_config = a
            if not os.path.isfile(cmd_config):
                print "Config file does not exist:", cmd_config
                sys.exit(2)

    # set defaults
    token = TOKEN
    name = NAME
    room = ROOM

    # config overrides defaultsif cmd_room:
    if cmd_config:
        config_file = cmd_config
    else:
        config_file = CONFIG

    if os.path.isfile(config_file):
        config = ConfigParser.ConfigParser()
        config.read(config_file)
        if config.has_section('hipchat'):
            if config.has_option('hipchat', 'TOKEN'):
                token = config.get('hipchat', 'TOKEN')
            if config.has_option('hipchat', 'NAME'):
                name = config.get('hipchat', 'NAME')
            if config.has_option('hipchat', 'TOKEN'):
                room = config.get('hipchat', 'ROOM')

    # cmd line overrides defaults and config
    if cmd_token:
        token = cmd_token
    if cmd_name:
        name = cmd_name
    if cmd_room:
        room = cmd_room

    if not revision:
        print "Sepcify a revision with -r or --revision"
        sys.exit(2)
    if not repository:
        print "Specify a repository with -s or --repository"
        sys.exit(2)

    chatMsg = getCommitInfo(repository, revision)

    t = threading.Thread(target=sendToHipChat, args=(chatMsg, token, room, name))
    t.daemon = True
    t.start()


if __name__ == "__main__":
    main()
