# -*- coding: utf-8 -*-

import webapp2
import os

from django.utils import feedgenerator

from models import TweetHistory


class FeedHandler(webapp2.RequestHandler):
    def get(self):
        feed = feedgenerator.Rss201rev2Feed(
            title=u'Ebooks Deal of the Day',
            link=self.request.path_url,
            description=u'Feed: Ebooks Deal of the Day',
            language=u'ja'
            )

        # TweetHistoryにはFeedを取得している会社しか存在していないので、全件取得する
        # fetch()のlimitを指定しないと、全件取ってくるもよう
        results = TweetHistory.query().fetch()


        for result in results:
            # last_messageは全角スペースで区切ると、最後に各社サイトへのURLがあるため、それをFeedのURLとして設定する
            splited = result.last_message.split(u'　')

            feed.add_item(
                title=result.last_message,
                link=splited[-1],
                description=result.last_message
                )


        # RSS文字列にして出力
        rss = feed.writeString('utf-8')

        self.response.headers['Content-Type']='text/xml; charset=utf-8'
        self.response.out.write(rss)




debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')
            
app = webapp2.WSGIApplication([
                              ('/feed', FeedHandler),
                              ], debug=debug)