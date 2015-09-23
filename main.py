import requests
import sys
import humanize
from datetime import datetime, timedelta, date
from bottle import route, run, request, template


CLIENT_ID="7250583f495e42f1b7828a6c7eacc004"
user_access_token="1546684.7250583.6b2deff4e7da4bb2b60bfc8778095649"

def refreshPayload():
	payload = {'client_id':CLIENT_ID, 'access_token': user_access_token}

refreshPayload()

session = requests.Session()

followees = []

class Followee:
	def __init__(self, id, username):
		self.recent_media = []
		self.user_id = id
		self.username = username		

	def getRecentMedia(self):
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
		# print "Username: %s"%self.username
		if len(self.recent_media) != 0:
			print self.username,
			print '\t',
			print humanize.naturaltime(datetime.now()-datetime.fromtimestamp(self.recent_media[0]['time'])),
			print '\t',
			print self.photosPerDay(),
			print '\t',
			print self.likesPerPhoto()
		else:
			print self.username
			# print "No media available for this user"

def main():
	if len(sys.argv)<2:
		user_id = input("Enter instagram user ID: ")
	else:
		user_id = sys.argv[1]
	user_info = getUser(user_id)
	print "User name is", user_info['data']['username']
	print "User has", user_info['data']['counts']['follows'], "followings"
	self_user = Followee(user_id, user_info['data']['username'])
	self_user.getRecentMedia()
	self_user.printData()

	print "Getting followings info..."
	populateFollowings(user_id)

	print "Getting followings media..."
	for user in followees:
		user.getRecentMedia()
		user.printData()

def getUser(user_id):
	r = session.get('https://api.instagram.com/v1/users/'+str(user_id)+'/', params=payload)
	r = session.get('https://api.instagram.com/v1/users/self/', params=payload)
	return r.json()

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

@route('/')
def hello():
	if request.query.get('access_token') is not None:
		return template('answer.html', access_token=request.query.access_token)
	return template('before.html')

@post('/get_data')
def get_data():
	if request.query.get('access_token') is not None:
		return 'Data will be here'
	else:
		return 'Missing access_token'

run(host='localhost', port=8000, debug=True)

