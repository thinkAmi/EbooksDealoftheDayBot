# -*- coding: utf-8 -*-

import webapp2
import os
import logging
import datetime
import json

from google.appengine.api import urlfetch
from google.appengine.api import mail

from python_twitter.twitter import TwitterError
from twitterhelper import TwitterHelper
from models import TweetHistory, ErrorMailHistory


# ツイートする抽象クラス：実際は、このクラスを継承して利用する
# ソース自体は、tasktweetpublisherhandler.pyにコードを書く
class TaskTweetBaseHandler(webapp2.RequestHandler):
    def post(self):

        # 例外が出た場合、エラーログを残し、タスクを終了する。
        try:
            self._tweet()

        except TwitterError, e:
            if e.message == u'Status is a duplicate.':
                # 重複Tweetはよくあることなので、infoレベルにする
                logging.info(u'Duplicate posted')
            else:
                logging.error(e)

        except Exception, e:
            logging.error(e)



    def _tweet(self):
        message = self._get_DOTD()

        if message is None:
            # エラーを出力
            logging.error(u'Cannot Get DOTD')
            self._send_error_mail(self._errorContents)
            return


        # すでにツイート済の場合、ログに残して、ツイートせずに終了
        if self._has_tweeted(message):
            logging.info(u'Already posted')
            return


        # tweetする
        twitter = TwitterHelper()
        twitter.tweet(message)


        # 重複ツイートを避けるため、datastoreにツイート内容を保存
        self._save_tweet_message(message)



    def _get_DOTD(self):
        if hasattr(self, '_feedUrl'):
            return self._get_DOTD_from_feed()

        elif hasattr(self, '_scrapeUrl'):
            return self._get_DOTD_from_web()

        else:
            # ここまで来た場合、プログラムでオーバーライドが適切に行われていないと考えられるため、エラーで落とせるようにする
            return None


    def _get_DOTD_from_feed(self):
        # 子クラスで指定したFeedのURLを元に、、Deal of the Day のデータを取得する
        # 取得できない場合、Noneを返す

        # 必須パラメータなので、呼び出し元のサーバーIPアドレスを取得する
        ip = os.environ['REMOTE_ADDR']

        # Google Feed API での1件フェッチ
        url = (
            u'https://ajax.googleapis.com/ajax/services/feed/load?v=1.0&q='
            + self._feedUrl
            + u'&num=1'
            + u'&userip=' + ip
            )
        feed = urlfetch.fetch(url)

        j = json.loads(feed.content)
        entries = j['responseData']['feed']['entries']
        for entry in entries:
            # entriesは1件だけのため、forの中で処理をしてしまう
            result = self._create_message(entry['title'])
            return result

        # ここまで来た場合、該当するデータがないということで、Noneを返す
        return None


    def _get_DOTD_from_web(self):
        title = self.scrape()
        result = self._create_message(title)
        return result


    def _create_message(self, title):
        # 複数回使う可能性があるものは、最初に編集しておく
        # また、先頭に空白・タブ・改行が入ってくる可能性があるため、それらも削除する
        publisher = u'[' + self._tweetId + u']　'
        ebookTitle = self.edit_title(title).lstrip()

        msg = publisher + ebookTitle + u'　' + self._dealUrl
        if len(msg) <= 140:
            return msg

        msg = publisher + ebookTitle
        if len(msg) <= 140:
            return msg

        msg = ebookTitle
        if len(msg) <= 140:
            return msg

        return ebookTitle[0:140]



    def _has_tweeted(self, message):
        # データストアを検索し、値が一致すれば、すでにツイート済
        history = TweetHistory.get_by_id(self._tweetId)

        if history is None:
            # エンティティがない場合は、まだツイートしていない
            return False
        elif message == history.last_message:
            return True
        else:
            return False



    def _save_tweet_message(self, message):
        # ツイートした内容をデータストアに保存する
        history = TweetHistory(id=self._tweetId, last_message=message)
        history.put()



    def _send_error_mail(self, errorType):
        # エラーの場合、管理者メール送信タスクを作成する
        # 送信履歴がないこと・本日はまだ送信していないことが条件
        # ndbの場合キャッシュをするので、キャッシュはオフにしておく
        history = ErrorMailHistory.get_by_id(
                        errorType,
                        use_cache=False,
                        use_memcache=False
                        )

        if history is None:
            self._add_send_error_mail_task(history, errorType)
            return

        now = datetime.datetime.utcnow()
        if history.last_send_date < now.date():
            self._add_send_error_mail_task(history, errorType)
            return



    def _add_send_error_mail_task(self, history, errorType):
        # メールの送信、送信履歴の更新
        taskqueue.add(
            url='/task/errormail',
            params={'subject': errorType}
            )

        if history is None:
            history = ErrorMailHistory(id=errorType)

        now = datetime.datetime.utcnow()
        history.last_send_date = now.date()
        history.put()


    '''
    以下、具象クラスでオーバーライドが任意のメソッド
    '''

    def edit_title(self, title):
        # feedのタイトルが長いなどの場合、編集して返すためのメソッド
        return title

    def scrape(self):
        # 対象のWebサイトをスクレイピングして返すためのメソッド
        return None
