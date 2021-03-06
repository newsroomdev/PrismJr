#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from csv import DictReader, DictWriter
from datetime import datetime
from os import environ
from sys import argv
from time import sleep

import requests
from requests_oauthlib import OAuth1
from urlparse import parse_qs

# (command, argument, input, output) = argv[1:]

# Twitter specific auth urls
REQUEST_TOKEN_URL = "https://api.twitter.com/oauth/request_token"
AUTHORIZE_URL = "https://api.twitter.com/oauth/authorize?oauth_token="
ACCESS_TOKEN_URL = "https://api.twitter.com/oauth/access_token"

# secretz
CONSUMER_KEY = environ.get('TW_CONSUMER_KEY')
CONSUMER_SECRET = environ.get('TW_CONSUMER_SECRET')

# written at runtime
OAUTH_TOKEN = ""
OAUTH_TOKEN_SECRET = ""

# API urls & params 
BASE_URL = "https://api.twitter.com/1.1/statuses/user_timeline.json?screen_name="
COUNT = "&count=200"
CUTOFF = datetime(2013, 6, 21)

# get variables from the command line
# (argument, input, output) = argv[1:]

def setup_oauth():
    """Authorize your app via identifier."""
    # Request token
    oauth = OAuth1(CONSUMER_KEY, client_secret=CONSUMER_SECRET)
    r = requests.post(url=REQUEST_TOKEN_URL, auth=oauth)
    credentials = parse_qs(r.content)

    resource_owner_key = credentials.get('oauth_token')[0]
    resource_owner_secret = credentials.get('oauth_token_secret')[0]

    # Authorize
    authorize_url = AUTHORIZE_URL + resource_owner_key
    print 'Please go here and authorize: ' + authorize_url

    verifier = raw_input('Please input the verifier: ')
    oauth = OAuth1(CONSUMER_KEY,
       client_secret=CONSUMER_SECRET,
       resource_owner_key=resource_owner_key,
       resource_owner_secret=resource_owner_secret,
       verifier=verifier)

    # Finally, Obtain the Access Token
    r = requests.post(url=ACCESS_TOKEN_URL, auth=oauth)
    credentials = parse_qs(r.content)
    token = credentials.get('oauth_token')[0]
    secret = credentials.get('oauth_token_secret')[0]

    return token, secret

# get the oauth
def get_oauth():
    oauth = OAuth1(CONSUMER_KEY,
        client_secret=CONSUMER_SECRET,
        resource_owner_key=OAUTH_TOKEN,
        resource_owner_secret=OAUTH_TOKEN_SECRET)
    return oauth

def input_users(filename):
    """Reads a CSV and returns a list of majority and minority users"""
    with open(filename, 'rU') as readf:
        # create a list of dicts of Twitter URLs nested objects
        data = list(DictReader(readf))

    # create a list of majority Twitter accounts strings
    tweeps = {}
    missing = [obj['handle'] for obj in data if obj['handle']]

    #create dict of arrays of Twitter screen names
    tweeps.update({
        'missing': missing
    })
    return tweeps

def parse_tweets(lists):
    """
    Takes a list of dictionaries, get the good bits
    Returns a dictionary
    """
    timeline = []
    for statuses in lists:
        for status in statuses:
            format = "%a %b %d %H:%M:%S +0000 %Y"
            output_format = "%m/%d/%Y %H:%M:%S"
            stamp = datetime.strptime(status['created_at'], format)
            if stamp >= CUTOFF:
                # write the data to a new dictionary
                timeline.append({
                    # "id": "%s" % status['id_str'],
                    "screen_name": "%s" % status['user']['screen_name'],
                    "text": "%s" % status['text'],
                    "retweet_count": "%s" % status['retweet_count'],
                    "favorite_count": "%s" % status['favorite_count'],
                    "created_at": "%s" % stamp.strftime(output_format),
                    "week": "%s" % stamp.strftime("%U"),
                    "id": "%s" % status['id_str']
                })
    return timeline

def next_timeline(statuses, tweep, oauth):
    """
    Parse out the max_id and since_id, then keep on rolling. 
    Takes a nested objects
    """
    max_id = statuses[-1]['id'] - 1
    max_param = "&max_id=%s" % max_id
    url = BASE_URL + tweep + COUNT + max_param
    next_r = requests.get(url=url, auth=oauth)
    return next_r.json()

def make_requests(users, oauth):
    """
    Construct a request from a list of users
    Return a request object
    """
    storage = []
    for user in users:
        print user
        r = requests.get(url=BASE_URL+user+COUNT, auth=oauth)
        statuses = r.json()
        next = next_timeline(statuses, user, oauth)
        print 'initial %s' %len(statuses)
        while len(next) > 0:
            statuses.extend(next)
            print 'added %s' % len(next)
            sleep(10)
            next = next_timeline(statuses, user, oauth)
        storage.append(statuses)
        print 'appended %s total to storage' % len(statuses)
    return storage

def output_csv(timeline, user=None):
    """
    Takes a dictionary and writes it to a CSV
    """
    row0 = timeline[0].keys()
    if user != None:
        write_name = user + '.csv'
    else:
        write_name = 'missing_tweeps.csv'
    with open(write_name, 'wb') as writef:
        # Write the header row because of reasons.
        write_csv = DictWriter(writef, fieldnames=row0)
        write_csv.writeheader()
        # write the dictionary to a CSV, and encode strings at UTF8
        for d in timeline:
            write_csv.writerow({k:v.encode('utf8') for k,v in d.items()})
    print 'PRISM Jr. is done. Please see %s' % write_name

if __name__ == "__main__":
    if not OAUTH_TOKEN:
        token, secret = setup_oauth()
        print "OAUTH_TOKEN: " + token
        OAUTH_TOKEN = token
        print "OAUTH_TOKEN_SECRET: " + secret
        OAUTH_TOKEN_SECRET = secret
        print
    else:
        oauth = get_oauth()
        tweeps = input_users('missing.csv')
        storage = make_requests(tweeps['missing'], oauth)
        timeline = parse_tweets(storage)
        output_csv(timeline)
