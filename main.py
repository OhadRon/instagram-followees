import requests
import os
import sys
import uuid
from bottle import route, run, request, template, redirect, post
from rq import Queue
from worker import conn
import utils
from redis import Redis

q = Queue(connection=conn)

session = requests.Session()

@route('/')
def start():
	if request.query.get('code') is not None:
		payload = { 
			'client_id': os.environ['CLIENT_ID'],
			'client_secret': os.environ['CLIENT_SECRET'],
			'grant_type': 'authorization_code',
			'redirect_uri': os.environ['BASE_URL'],
			'code': request.query.get('code'),
			'scope': 'basic+relationships',
		}

		r = session.post('https://api.instagram.com/oauth/access_token', data=payload)
		response = r.json()
		if 'access_token' in response:
			return template('answer.html', access_token=response['access_token'])
		else:
			return template('before.html', redirect_url = os.environ['BASE_URL'], client_id = os.environ['CLIENT_ID'])
	else:
		return template('before.html', redirect_url = os.environ['BASE_URL'], client_id = os.environ['CLIENT_ID'])


@route('/get_data')
def get_data():
	if request.query.get('access_token') is not None:
		CLIENT_ID=os.environ['CLIENT_ID']

		followees = []

		response = {}

		payload = {'client_id':CLIENT_ID, 'access_token': request.query.get('access_token')}

		def getUser():
			r = session.get('https://api.instagram.com/v1/users/self/', params=payload)
			return r.json()

		user_info = getUser()
		
		print "User name is", user_info['data']['username']

		response['self_user'] = user_info['data']['username']

		print "User has", user_info['data']['counts']['follows'], "followings"

		response['followings'] = user_info['data']['counts']['follows']

		def populateFollowings(user_id):
			paginated = True
			current_url = 'https://api.instagram.com/v1/users/'+str(user_id)+'/follows'
			while paginated:
				r = session.get(current_url, params=payload)
				for item in r.json()['data']:
					followees.append(item['id'])
				if 'next_url' in r.json()['pagination']:
					current_url = r.json()['pagination']['next_url']
				else: 
					paginated = False
			print len(followees), "Followings found"
			return True

		print "Getting followings info..."
		populateFollowings(user_info['data']['id'])

		response['jobs_list'] = "ig_joblist:"+str(uuid.uuid4())
		print "Creating jobs to get followings media...", response['jobs_list']

		if os.environ['DEBUG_MODE'] == 'TRUE':
			# Only get the first 5 followees to conserve time
			print "[DEBUG] Getting only first 5 followees"
			for user in followees[:5]:
				job = q.enqueue(utils.getFolloweeData, user, payload['client_id'], payload['access_token'])
				conn.sadd(response['jobs_list'], job.id)
		else:
			for user in followees:
				job = q.enqueue(utils.getFolloweeData, user, payload['client_id'], payload['access_token'])
				conn.sadd(response['jobs_list'], job.id)

		return response
	else:
		return 'Missing access_token'

@route('/refresh_state')
def refresh_state():
	if request.query.get('jobs_list') is not None:
		response = {}

		response['results'] = []

		jobs_list = request.query.get('jobs_list')
		print "Refreshing state", jobs_list

		jobs = conn.smembers(jobs_list)
		for job in jobs:
			current_job = q.fetch_job(job)
			if current_job.result is not None:
				conn.srem(jobs_list, current_job.id)
				response['results'].append(current_job.result)

			elif current_job.status == 'failed':
				conn.srem(jobs_list, current_job.id)

		# If these are the last jobs:
		if len(jobs) - len(response['results'])  == 0:
			response['done'] = True

		return response

	else:
		return 'Missing jobs list'

@route('/unfollow')
def unfollow():
	print "trying to unfollow",request.query.get('user_id')
	if request.query.get('user_id') is not None and request.query.get('access_token') is not None:
		payload = { 
			'access_token': request.query.get('access_token'),
			'ACTION':'unfollow',
		}
		print payload
		r = session.post('https://api.instagram.com/v1/users/'+request.query.get('user_id')+'/relationship', params=payload)
		return "Instagram replied:"+str(r.content)

@route('/follow')
def follow():
	print "trying to follow",request.query.get('user_id')
	if request.query.get('user_id') is not None and request.query.get('access_token') is not None:
		payload = { 
			'access_token': request.query.get('access_token'),
			'ACTION':'follow',
		}
		r = session.post('https://api.instagram.com/v1/users/'+request.query.get('user_id')+'/relationship', params=payload)
		return "Instagram replied:"+str(r.content)

run(host='0.0.0.0', port=sys.argv[1])