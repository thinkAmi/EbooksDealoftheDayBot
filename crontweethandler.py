# -*- coding: utf-8 -*-

import webapp2
import os
from google.appengine.api.labs import taskqueue

class CronTweetHandler(webapp2.RequestHandler):
    def get(self):
        # デフォルト以外のタスクに入れる
        myask = taskqueue.Queue('tweetqueue')
        task = taskqueue.Task(url='/task/tweet')
        myask.add(task)


debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')
            
app = webapp2.WSGIApplication([
                               ('/cron/tweet', CronTweetHandler),
                               ], debug=debug)