# Syncs to server, for use as cronjob
from gen import ROOT_DIR, REV_DIR, BASE_YAML, get_sync_data, get_base, get_rev_dir, write_sync_data
import os
import yaml
import urllib2, urllib

SLINK = os.path.join(ROOT_DIR, 'slink')

def slink(revision):
    os.system('rm %s' % SLINK)
    os.system('\nln -s %s %s' % (get_rev_dir(revision), SLINK))

# How to get a new access token
# 1) Go to https://www.facebook.com/dialog/oauth?client_id=CLIENT_ID&redirect_uri=http://tortbunnies.com/test/&scope=publish_stream,offline_access,manage_pages
#    Replace CLIENT_ID with current app_id and redirect_uri as appropriate
# 2) https://graph.facebook.com/oauth/access_token?client_id=CLIENT_ID&redirect_uri=http://tortbunnies.com/test/&client_secret=THE_SECRET&code=THE_CODE_FROM_ABOVE
#    Again, replace as appropriate
# 3) Get fan page access token - https://graph.facebook.com/me/accounts?access_token=SOME_ACCESS_TOKEN
ACCESS_TOKEN = 'NOPE'
POST_URL = "https://graph.facebook.com/me/links"

def post_to_facebook(url, message):
    print urllib2.urlopen(POST_URL, data=urllib.urlencode(
        {'access_token' : ACCESS_TOKEN, 'link' : url, 'message' : message})).read()

if __name__ == '__main__':
    import time, sys, traceback, datetime
    now = datetime.datetime.utcnow()
    base = get_base()
    revisions = base['revisions'].items()
    revisions.sort()
    latest = None
    for r, dt in revisions: # Get latest revision that has or will deploy soon
        if dt <= now + datetime.timedelta(minutes=70): # Time to deploy!
            latest = r
    if latest:
        slink(latest)
        data = get_sync_data(latest) or {}
        fb = data.get("post_to_facebook", [])
        if fb:
            for f in fb:
                post_to_facebook(f['link'], f['message'])
            data["post_to_facebook"] = []
            write_sync_data(latest, data)

