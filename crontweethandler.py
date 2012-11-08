# -*- coding: utf-8 -*-

import webapp2
import os
from google.appengine.api.labs import taskqueue

class CronTweetHandler(webapp2.RequestHandler):
    def get(self):
        # デフォルト以外のタスクに入れる
        maytask = taskqueue.Queue('tweetqueue')

        # Ebookのサイトごとに追加
        # Apress
        apress = taskqueue.Task(url='/task/tweet/apress')
        maytask.add(apress)

        # PEARSON
        pearson = taskqueue.Task(url='/task/tweet/pearson')
        maytask.add(pearson)

        # O'Reilly
        oreilly = taskqueue.Task(url='/task/tweet/oreilly')
        maytask.add(oreilly)

        # O'Reilly Microsoft Press
        omspress = taskqueue.Task(url='/task/tweet/oreillymspress')
        maytask.add(omspress)



debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')
            
app = webapp2.WSGIApplication([
                               ('/cron/tweet', CronTweetHandler),
                               ], debug=debug)