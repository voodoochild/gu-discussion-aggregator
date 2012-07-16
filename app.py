import requests
import json
import operator
from redis import StrictRedis
from celery import Celery
from flask import Flask, make_response


DISCUSSION_API = 'http://discussionapi.guardian.co.uk/discussion-api/'
CONTENT_API = 'http://content.guardianapis.com/'
CACHE_DATA_FOR = 60 * 60 * 6 # seconds
BROKER_URL = 'redis://'
CELERY_RESULT_BACKEND = 'redis://'


app = Flask(__name__)
redis = StrictRedis('localhost', 6379)
celery = Celery('app')


@app.route('/comments/latest/<userid>')
def latest_comments(userid):
    """Return JSON of recent comment counts by section"""
    cached_data = redis.get('da/users/{}'.format(userid))
    if cached_data:
        response = make_response(cached_data)
    else:
        get_user_comments.delay(userid)
        response = make_response(json.dumps({}))
    response.mimetype = 'application/json'
    return response


@celery.task(name='get-user-comments')
def get_user_comments(userid):
    """Build a map of recent comment counts by section"""
    r = requests.get(
        '{}profile/{}/comments?pageSize=50'.format(DISCUSSION_API, userid)
    )

    # If call failed, swallow the error and return no data
    if r.status_code != 200:
        return json.dumps({})

    # Map article keys to number of comments
    comments = {}
    for comment in json.loads(r.content)['comments']:
        key = comment['discussion']['key']
        if not key in comments:
            comments[key] = 0
        comments[key] = comments[key] + 1

    # Sort by comment count
    comments = sorted(
        comments.iteritems(), key=operator.itemgetter(1), reverse=True
    )

    # Map comments to sections
    key_sections = redis.hgetall('da/key-sections')
    for key, count in comments:
        if not key in key_sections.keys():
            r = requests.get('{}{}'.format(CONTENT_API, key[1:]))
            try:
                content = json.loads(r.content)
                section = content['response']['content']['sectionId']
                redis.hset('da/key-sections', key, section)
                key_sections[key] = section
            except ValueError:
                del comments[key] # couldn't lookup section, so ignore it

    # Map comments to sections
    comments_sections = {}
    for key, count in comments:
        section = key_sections[key]
        if not section in comments_sections:
            comments_sections[section] = 0
        comments_sections[section] = comments_sections[section] + count

    # Cache response in redis
    rkey = 'da/users/{}'.format(userid)
    data = json.dumps(comments_sections)
    pipe = redis.pipeline()
    pipe.set(rkey, data)
    pipe.expire(rkey, CACHE_DATA_FOR)
    pipe.execute()

    return data


if __name__ == '__main__':
    app.run(debug=True)
