# -*- coding: utf-8 -*-

import webapp2
import os
import logging

from google.appengine.api import mail
from google.appengine.api import users
import yaml

class TaskErrorMailHandler(webapp2.RequestHandler):
    def post(self):

        # 例外が出た場合、エラーログを残し、タスクを終了する。
        try:
            self._send(self.request)

        except Exception, e:
            logging.error(e)


    def _send(self, request):
        host = request.host
        splited = host.split('.')
        email = u'attention@' + splited[0] + u'.appspotmail.com'

        mail.send_mail_to_admins(
            sender=email,
            subject=request.get('subject'),
            body=u'件名のエラーが発生しました。',
            )



debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')
            
app = webapp2.WSGIApplication([
                               ('/task/errormail', TaskErrorMailHandler),
                               ], debug=debug)