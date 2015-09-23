import requests
import sys
import humanize
import os
from datetime import datetime, timedelta, date
from bottle import route, run, request, template, redirect, post

session = requests.Session()

class Followee:
	def __init__(self, id, username):
		self.recent_media = []
		self.user_id = id
		self.username = username		

	def getRecentMedia(self,payload):
		r = session.get('https://api.instagram.com/v1/users/'+self.user_id+'/media/recent/', params=payload)
		if r.status_code == 200: # If not, this user is probably visible to followers only
			for item in r.json()['data']:
				self.recent_media.append({'time':float(item['created_time']), 'user': item['user']['username'], 'likes': int(item['likes']['count'])})

	def photosPerDay(self):
		days = {}
		most_days_back = datetime.now().date()-datetime.fromtimestamp(self.recent_media[-1]['time']).date()
		most_days_back = most_days_back.days

		for day in xrange(0,most_days_back):
			days[day] = 0

		for photo in self.recent_media:
			photo_day = datetime.now().date()-datetime.fromtimestamp(photo['time']).date()
			photo_day = photo_day.days
			if photo_day < most_days_back:
				days[photo_day] += 1

		num_of_photos = 0
		for day in xrange(0,most_days_back):
			num_of_photos += days[day]

		return format(num_of_photos / float(most_days_back), '.2f')

	def likesPerPhoto(self):
		likes = 0
		for photo in self.recent_media:
			likes += photo['likes']

		return format(likes / float(len(self.recent_media)), '.2f')


	def __repr__(self):
		return "<Followee %s, %s, %s>"%(str(self.username), str(self.user_id), str(len(self.recent_media)))

	def printData(self):
		if len(self.recent_media) != 0:
			photos_per_day = self.photosPerDay()
			likes_per_photo = self.likesPerPhoto()
			time_ago = humanize.naturaltime(datetime.now()-datetime.fromtimestamp(self.recent_media[0]['time']))
			print self.username,
			print '\t',
			print time_ago,
			print '\t',
			print photos_per_day,
			print '\t',
			print likes_per_photo
			return {'username': self.username, 'photos_per_day': photos_per_day, 'likes_per_photo': likes_per_photo, 'last_photo_time': time_ago}
		else:
			print self.username
			return {'username': self.username}



def main(access_token):

	CLIENT_ID=os.environ['CLIENT_ID']

	followees = []

	response = {}

	payload = {'client_id':CLIENT_ID, 'access_token': access_token}

	def getUser():
		r = session.get('https://api.instagram.com/v1/users/self/', params=payload)
		return r.json()

	user_info = getUser()
	
	print "User name is", user_info['data']['username']

	response['self_user'] = user_info['data']['username']

	print "User has", user_info['data']['counts']['follows'], "followings"

	response['followings'] = user_info['data']['counts']['follows']

	self_user = Followee(user_info['data']['id'], user_info['data']['username'])
	self_user.getRecentMedia(payload)
	self_user.printData()

	def populateFollowings(user_id):
		paginated = True
		current_url = 'https://api.instagram.com/v1/users/'+str(user_id)+'/follows'
		while paginated:
			r = session.get(current_url, params=payload)
			for item in r.json()['data']:
				followees.append(Followee(item['id'], item['username']))
			if 'next_url' in r.json()['pagination']:
				current_url = r.json()['pagination']['next_url']
			else: 
				paginated = False
		print len(followees), "Followings found"
		return True

	print "Getting followings info..."
	populateFollowings(user_info['data']['id'])

	response['users'] = []
	print "Getting followings media..."
	for user in followees[:10]:
		user.getRecentMedia(payload)
		response['users'].append(user.printData())

	return response


@route('/')
def hello():	
	return template('before.html', redirect_url = os.environ['BASE_URL']+'/results', client_id = os.environ['CLIENT_ID'])

@route('/results')
def results():
	payload = { 
		'client_id': os.environ['CLIENT_ID'],
		'client_secret': os.environ['CLIENT_SECRET'],
		'grant_type': 'authorization_code',
		'redirect_uri': os.environ['BASE_URL']+'/results',
		'code': request.query.get('code')
	}

	r = session.post('https://api.instagram.com/oauth/access_token', data=payload)
	response = r.json()
	
	return template('answer.html', access_token=response['access_token'])


@route('/get_data')
def get_data():
	if request.query.get('access_token') is not None:
		return main(request.query.get('access_token'))
	else:
		return 'Missing access_token'

run(host='localhost', port=8000, debug=True)

