import requests
import pickle
from datetime import datetime, date, timedelta
from worker import conn
import os

def getFolloweeData(user_id, client_id, access_token):

	# Try the cache first
	cache_try = conn.get('ig_cache:'+user_id)
	if cache_try is not None:
		return pickle.loads(cache_try)

	results = {}

	# Call the IG servers
	payload = { 
		'client_id': client_id,
		'access_token': access_token,
	}
	r = requests.get('https://api.instagram.com/v1/users/'+user_id+'/media/recent/', params=payload)

	# Extract recent media from the response
	recent_media = []

	if r.status_code == 200: # If not, this user is probably visible to followers only
		for item in r.json()['data']:
			recent_media.append({'time':float(item['created_time']), 'user': item['user']['username'], 'likes': int(item['likes']['count'])})

	results['last_photo_time'] = recent_media[0]['time']

	# Calculate photos per day

	days = {}
	most_days_back = datetime.now().date()-datetime.fromtimestamp(recent_media[-1]['time']).date()
	most_days_back = most_days_back.days

	for day in xrange(0,most_days_back):
		days[day] = 0

	for photo in recent_media:
		photo_day = datetime.now().date()-datetime.fromtimestamp(photo['time']).date()
		photo_day = photo_day.days
		if photo_day < most_days_back:
			days[photo_day] += 1

	num_of_photos = 0
	for day in xrange(0,most_days_back):
		num_of_photos += days[day]

	results['photos_per_day'] = format(num_of_photos / float(most_days_back), '.2f')

	# Calculate likes per photo

	likes = 0
	for photo in recent_media:
		likes += photo['likes']

	results['likes_per_photo'] = format(likes / float(len(recent_media)), '.2f')

	# Additional metadata

	results['username'] = recent_media[0]['user']

	results['user_id'] = user_id

	conn.set('ig_cache:'+user_id ,pickle.dumps(results))
	conn.expire('ig_cache:'+user_id, os.environ['CACHE_LIFE'])

	return results
