#!/usr/bin/env python
import calendar
from csv import DictReader, DictWriter
import datetime
from os import environ

from facepy import GraphAPI

# get posts until that date
CUTOFF = datetime.datetime(2013, 6, 21)
CUTOFF_UNIX = calendar.timegm(CUTOFF.timetuple())

# get secrets
OAUTH_TOKEN = environ.get('FB_OAUTH_TOKEN')
graph = GraphAPI(OAUTH_TOKEN)
data = ()

with open('faces.csv', 'rb') as read:
	data = list(DictReader(read))

# create a list of majority Twitter accounts strings
faces = {}
maj_faces = [obj['Majority_Face'] for obj in data if obj['Majority_Face']]
min_faces = [obj['Minority_Face'] for obj in data if obj['Minority_Face']]

#create dict of arrays of Twitter screen names
faces.update({
	'Majority_Face': maj_faces, 
	'Minority_Face': min_faces
})

timeline = { 'data': [] }
counter = 0
face_count = 0

# take possible k,v for likes, shares, comments, or shared posts
def condition(possible):
	data = timeline['data']
	place = len(timeline['data']) - 1
	try:
		data[place][possible] = "%s" % len(status[possible]["data"])
	except KeyError:
		data[place][possible] = "0"

def text_cond(possible):
	data = timeline['data']
	place = len(timeline['data']) - 1
	try:
		data[place][possible] = "%s" % status[possible]
	except KeyError:
		data[place][possible] = ""

for face in faces['Minority_Face']:
	print '%s, %s' % (face, face_count)
	face_count += 1
	search = '/posts'
	statuses = graph.get(face + search)
	if len(statuses['data']) > 1:
		for status in statuses['data']:
			timestamp_s = status['created_time']
			upstamp_s = status['updated_time']
			timestamp = datetime.strptime(timestamp_s, '%Y-%m-%dT%X+0000')
			upstamp = datetime.strptime(upstamp_s, '%Y-%m-%dT%X+0000')
			timeline['data'].append({
				"id": "%s" % status['from']['id'],
				"screen_name": "%s" % status['from']['name'],
				"type": "%s" % status['type'],
				"created_at": "%s" % timestamp.strftime("%x %X"),
				"updated_at": "%s" % upstamp.strftime("%x %X"),
				"week": "%s" % timestamp.strftime("%U"),
			})
			text_cond("message")
			text_cond("story")
			condition("likes")
			condition("comments")
			condition("shares")
			print '%s\t' % counter
			counter += 1

row0 = timeline['data'][0].keys()

with open('facebook.csv', 'wb') as writef:
	writef.write(u'\ufeff'.encode('utf8'))
	# Write the header row because of reasons.
	write_csv = DictWriter(writef, fieldnames=row0)
	write_csv.writeheader()
	for d in timeline['data']:
		write_csv.writerow({k:v.encode('utf8') for k,v in d.items()})