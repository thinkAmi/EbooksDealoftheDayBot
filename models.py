# -*- coding: utf-8 -*-

from google.appengine.ext import ndb

class TweetHistory(ndb.Model):
    # idは "tweet" 固定
    last_message = ndb.StringProperty()


class ErrorMailHistory(ndb.Model):
    # idは "mail" 固定
    last_send_date = ndb.DateProperty()
