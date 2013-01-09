# -*- coding: utf-8 -*-

import webapp2
import os
from google.appengine.api.labs import taskqueue

from tasktweetpublisherhandler import handlerUrls

class CronTweetHandler(webapp2.RequestHandler):
    def get(self):
        # デフォルト以外のタスクに入れる
        mytask = taskqueue.Queue('tweetqueue')

        for url in handlerUrls.itervalues():
            mytask.add(taskqueue.Task(url=url))



debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

app = webapp2.WSGIApplication([
                               ('/cron/tweet', CronTweetHandler),
                               ], debug=debug)