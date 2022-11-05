from operator import truediv
import re
from datetime import datetime, timedelta
from werkzeug.exceptions import Forbidden

from database import execute, fetchone, commit, rowcount, fetchall
import main

FOLLOW_PROFILE_PRICE = 1
POST_PRICE = 1
TAG_PRICE = 1
POST_EDIT_PRICE = 1
POST_STAKE_VOLUME = 0.5  # 50% staking
VOTE_REWARD = 0.1

class User:
    def __init__(self, wallet, profileid):
        self.wallet = wallet
        self.profileid = profileid
        if profile := main.get_profile(profileid):
            self.id = profile['id']
            self.name = profile['name']
            self.handle = profile['handle']

    def onlyOwner(function):
        def wrapper(*args, **kwargs):
            self = args[0]
            execute("SELECT id FROM profile WHERE id=%(profileid)s AND address=%(address)s", {'profileid': self.profileid, 'address': self.wallet.address})
            row = fetchone()
            if row == None:
                raise Forbidden()
            return function(*args, **kwargs)
        return wrapper

    @onlyOwner
    def writePost(self, post, replyto=None):
        tags = set()
        if len(post)==0 or len(post)>255:
            return False
        now = datetime.now()

        hashtags = re.findall("#(\w+)", post)
        for hashtag in hashtags:
            tags.add(main.get_hashtag_id(hashtag, True))

        stake = POST_STAKE_VOLUME*self.get_followed_profiles_count()
        if stake == 0: stake=POST_STAKE_VOLUME
        if not self.wallet.pay_stake(POST_PRICE+len(tags)*TAG_PRICE, stake ):
            return False

        execute("INSERT INTO post (datetime, profileid, post, replyto, stake) VALUES (%(datetime)s, %(profileid)s, %(post)s, %(replyto)s, %(stake)s) RETURNING id", {'datetime': now.strftime("%Y%m%d%H%M.%S"), 'profileid': self.profileid, 'post': post, 'replyto': replyto, 'stake': stake })
        commit()
        postid = fetchone()['id']

        for hashtagid in tags:
            execute("INSERT INTO tag (hashtagid, postid) VALUES (%(hashtagid)s, %(postid)s)", {'hashtagid': hashtagid, 'postid': postid})
            commit()

        return True

    @onlyOwner
    def replyPost(self, postid, post):
        if self.writePost(post, postid):
            execute("UPDATE post SET replies=replies+1 WHERE id=%(postid)s", {'postid': postid})
            commit()
            return True
        return False

    @onlyOwner
    def editPost(self, postid, post):
        if len(post)==0 or len(post)>280:
            return False
        now = datetime.now()
        if not self.wallet.pay(POST_EDIT_PRICE):
            return False
        execute("UPDATE post SET post=%(post)s WHERE id=%(postid)s AND profileid=%(profileid)s AND stake>0", {'post': post, 'postid': postid, 'profileid': self.profileid})
        commit()
        return True

    @onlyOwner
    def deletePost(self, postid):
        yesterday = datetime.now() - timedelta(days=1)
        yesterday = yesterday.strftime("%Y%m%d%H%M.%S")
        execute("SELECT stake FROM post WHERE profileid=%(profileid)s AND id=%(postid)s AND datetime>%(yesterday)s", {'profileid': self.profileid, 'postid': postid, 'yesterday': yesterday})
        post = fetchone()
        if post and post['stake']>0:
            self.wallet.unlock(post['stake'])
        execute("DELETE FROM post WHERE profileid=%(profileid)s AND id=%(postid)s", {'profileid': self.profileid, 'postid': postid})
        commit()

    def readPost(self, postid):
        execute("SELECT post.id AS id,handle,name,post.profileid,post.datetime,post,yea,nay,replies,stake FROM post INNER JOIN profile ON profile.id=post.profileid WHERE post.id=%(postid)s", {'postid': postid})
        posts = fetchall()
        return main._process(posts, self)

    @onlyOwner
    def feed(self):
        execute("SELECT post.id,handle,name,post.profileid,post.datetime,post,replyto,yea,nay,replies,stake FROM follow INNER JOIN post ON post.profileid=followid INNER JOIN profile ON profile.id=post.profileid WHERE follow.profileid=%(profileid)s ORDER BY post.datetime DESC LIMIT 50", {'profileid': self.profileid})
        feed = fetchall()
        return main._process(feed, self)

    def posts(self, user):
        execute("SELECT post.id AS id,handle,name,post.profileid,post.datetime,post,replyto,yea,nay,replies,stake FROM post INNER JOIN profile ON profile.id=post.profileid WHERE post.profileid=%(profileid)s ORDER BY post.datetime DESC LIMIT 50", {'profileid': self.profileid})
        posts = fetchall()
        return main._process(posts, user)

    @onlyOwner
    def follow(self, followid):
        execute("SELECT rowid FROM follow WHERE profileid=%(profileid)s AND followid=%(followid)s", {'profileid': self.profileid, 'followid': followid})
        if fetchone():
            return False
        follow_address = main.get_profile_address(followid)
        if not follow_address:
            return False
        if not self.wallet.transfer(FOLLOW_PROFILE_PRICE, follow_address):
            return False
        execute("INSERT INTO follow (profileid, followid) VALUES (%(profileid)s, %(followid)s)", {'profileid': self.profileid, 'followid': followid})
        commit()
        return True

    @onlyOwner
    def yea(self, postid):
        yesterday = datetime.now() - timedelta(days=1)
        yesterday = yesterday.strftime("%Y%m%d%H%M.%S")
    # can't vote on your own post or post lock
        execute("SELECT id FROM post WHERE id=%(postid)s AND profileid!=%(profileid)s AND datetime>%(yesterday)s", {'postid': postid, 'profileid': self.profileid, 'yesterday': float(yesterday)})
        post = fetchone()
        if not post:
            return False
        execute("SELECT vote FROM vote WHERE postid=%(postid)s AND profileid=%(profileid)s", {'postid': postid, 'profileid': self.profileid})
        vote = fetchone()
    # already voted yae
        if vote and vote['vote'] == 1:
            return False
        execute("INSERT INTO vote (profileid,postid,vote) VALUES (%(profileid)s,%(postid)s,%(vote)s) ON CONFLICT (profileid,postid) DO UPDATE SET vote=%(vote)s", {'profileid': self.profileid, 'postid': postid, 'vote':1 })
        commit()
        if vote and vote['vote'] == -1:
            execute("UPDATE post SET yea=yea+1,nay=nay-1 WHERE id=%(postid)s", {'postid': post['id']})
        else:
            self.wallet.earn(VOTE_REWARD)
            execute("UPDATE post SET yea=yea+1 WHERE id=%(postid)s", {'postid': post['id']})
        commit()
        return True

    @onlyOwner
    def nay(self, postid):
        yesterday = datetime.now() - timedelta(days=1)
        yesterday = yesterday.strftime("%Y%m%d%H%M.%S")
    # can't vote on your own post or post lock
        execute("SELECT id FROM post WHERE id=%(postid)s AND profileid!=%(profileid)s AND datetime>%(yesterday)s", {'postid': postid, 'profileid': self.profileid, 'yesterday': float(yesterday)})
        post = fetchone()
        if not post:
            return False
        execute("SELECT vote FROM vote WHERE postid=%(postid)s AND profileid=%(profileid)s", {'postid': postid, 'profileid': self.profileid})
        vote = fetchone()
    # already voted nay
        if vote and vote['vote'] == -1:
            return False
        execute("INSERT INTO vote (profileid,postid,vote) VALUES (%(profileid)s,%(postid)s,%(vote)s) ON CONFLICT (profileid,postid) DO UPDATE SET vote=%(vote)s", {'profileid': self.profileid, 'postid': postid, 'vote':-1 })
        commit()
        if vote and vote['vote'] == 1:
            execute("UPDATE post SET yea=yea-1,nay=nay+1 WHERE id=%(postid)s", {'postid': post['id']})
        else:
            self.wallet.earn(VOTE_REWARD)
            execute("UPDATE post SET nay=nay+1 WHERE id=%(postid)s", {'postid': post['id']})
        commit()
        return True

    @onlyOwner
    def unfollow(self, followid):
        execute("DELETE FROM follow WHERE profileid=%(profileid)s AND followid=%(followid)s", {'profileid': self.profileid, 'followid': followid})
        commit()

    @onlyOwner
    def deleteAccount(self):
    # delete profile
        execute("DELETE FROM profile WHERE id=%(profileid)s AND address=%(address)s", {'profileid': self.profileid, 'address': self.wallet.address})
        commit()
        if rowcount() > 0:
    # delete follow
            execute("DELETE FROM follow WHERE profileid=%(profileid)s OR followid=%(profileid)s", {'profileid': self.profileid})
            commit()
    # delete post
            execute("DELETE FROM post WHERE profileid=%(profileid)s", {'profileid': self.profileid})
            commit()

    @onlyOwner
    def editAccount(self, handle, name):
        if len(name)<3 or len(name)>32 or len(handle)<3 or len(handle)>32:
            return False
        f=filter(str.isalnum, handle)
        handle="".join(f).lower()
        if handle!=self.handle and main.get_profile_id(handle):
            return False
        execute("UPDATE profile SET handle=%(handle)s,name=%(name)s WHERE id=%(profileid)s AND address=%(address)s", {'handle':handle, 'name':name, 'profileid': self.profileid, 'address': self.wallet.address})
        commit()
        return True

    def get_followed_profiles(self):
        execute("SELECT profile.id AS followid,handle,name FROM follow INNER JOIN profile ON profile.id=follow.followid WHERE follow.profileid=%(profileid)s ORDER BY name DESC", {'profileid': self.profileid})
        rows = fetchall()
        if rows == None:
            return False
        return rows

    def is_followed(self, followid):
        execute("SELECT profileid FROM follow WHERE profileid=%(profileid)s AND followid=%(followid)s", {'profileid': self.profileid, 'followid': followid})
        row = fetchone()
        if row == None:
            return False
        return True

    def get_followed_profiles_count(self):
        execute("SELECT count(*) AS count FROM follow INNER JOIN profile ON profile.id=follow.followid WHERE follow.profileid=%(profileid)s", {'profileid': self.profileid})
        return fetchone()['count']

    def get_post(self, postid):
        execute("SELECT post.id AS id,name,post.profileid,post.datetime,post,yea,nay FROM post INNER JOIN profile ON profile.id=post.profileid WHERE post.id=%(postid)s", {'postid': postid})
        return fetchone()
