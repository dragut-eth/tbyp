from random import randint
from datetime import datetime, timedelta

import wallet
from database import execute, fetchone, commit, rowcount, fetchall
from search import search_users

POST_REWARD = 0.1 # 10% reward

def get_profile(id):
    execute("SELECT id,handle,name,key FROM profile WHERE id=%s", (id,))
    row = fetchone()
    if row == None:
        return False
    return row

def get_profile_id(handle):
    execute("SELECT id FROM profile WHERE handle=%s", (handle,))
    row = fetchone()
    if row == None:
        return False
    return row['id']

def get_hashtag_id(hashtag, create=False):
    hashtag=_hashtag(hashtag)
    execute("SELECT id FROM hashtag WHERE hashtag=%s", (hashtag,))
    row = fetchone()
    if row != None:
        return row['id']
    if not create:
        return False
    execute("INSERT INTO hashtag (hashtag) VALUES (%(hashtag)s) RETURNING id", {'hashtag': hashtag})
    commit()
    return fetchone()['id']

def get_hashtag(id):
    execute("SELECT id,hashtag FROM hashtag WHERE id=%s", (id,))
    row = fetchone()
    if row == None:
        return False
    return row

def get_profile_address(id):
    execute("SELECT address FROM profile WHERE id=%s", (id,))
    row = fetchone()
    if row == None:
        return False
    return row['address']

def get_new_profiles():
    execute("SELECT id,handle,name FROM profile ORDER BY id DESC LIMIT 5")
    rows = fetchall()
    if rows == None:
        return []
    return rows

def get_popular_tags():
    execute("SELECT hashtag FROM hashtag INNER JOIN (SELECT *,COUNT(*) AS ct FROM (SELECT hashtagid FROM tag ORDER BY rowid  DESC LIMIT 100) AS a GROUP BY hashtagid ORDER BY ct DESC) AS b ON hashtag.id=hashtagid LIMIT 5")
    rows = fetchall()
    if rows == None:
        return []
    return rows
    
def list_profiles(address):
    execute("SELECT id,handle,name FROM profile WHERE address=%s", (address,))
    rows = fetchall()
    if rows == None:
        return False
    return rows

def search(search):
    return search_users(search)

def forum(hashtagid, user):
    execute("SELECT post.id,handle,name,post.profileid,post.datetime,post,replyto,yea,nay,replies,stake FROM tag INNER JOIN post ON post.id=postid INNER JOIN profile ON profile.id=post.profileid WHERE tag.hashtagid=%(hashtagid)s ORDER BY post.datetime DESC LIMIT 50", {'hashtagid': hashtagid})
    feed = fetchall()
    return _process(feed, user)

def thread(postid, user):
    execute("SELECT post.id,handle,name,post.profileid,post.datetime,post,yea,nay,replies,stake FROM post INNER JOIN profile ON profile.id=post.profileid WHERE post.replyto=%(replyto)s ORDER BY post.datetime DESC LIMIT 50", {'replyto': postid})
    feed = fetchall()
    return _process(feed, user)

def _create_account(address, handle, name):
    now = datetime.now()
    execute("INSERT INTO profile (address, datetime, handle, name) VALUES (%(address)s, %(datetime)s, %(handle)s, %(name)s) RETURNING id", {'address': address, 'datetime': now.strftime("%Y%m%d%H%M.%S"),'handle': handle, 'name': name})
    commit()
    profileid = fetchone()['id']
    execute("INSERT INTO follow (profileid, followid) VALUES (%(profileid)s, %(followid)s)", {'profileid': profileid, 'followid': profileid})
    commit()
    return profileid

def _find_handle(name):
    f=filter(str.isalnum,name)
    handle="".join(f).lower()
    for x in range(10):
        if not get_profile_id(handle):
            return(handle)
        handle += str(randint(1,10))
    return False

def _hashtag(hashtag):
    f=filter(str.isalnum,hashtag)
    hashtag="".join(f).lower()
    return hashtag

def _process(posts, user):
    yesterday = datetime.now() - timedelta(days=1)
    yesterday = yesterday.strftime("%Y%m%d%H%M.%S")
    remove = set()
    result = []
    for post in posts:
        if post['id'] in remove:
            continue
        elif str(post['datetime']) < yesterday:
            if post['nay'] > post['yea']:
# post to be removed
                continue
            elif post['stake']>0:
# stake to be unlock + reward
                _reward(post['profileid'], post['id'], post['stake'])
                pass
            else:
                post['status'] = 'lock'
        else:
            execute("SELECT vote FROM vote WHERE postid=%(postid)s AND profileid=%(profileid)s", {'postid': post['id'], 'profileid': user.profileid})
            if vote := fetchone():
                post['status'] = vote['vote']
            else:
                post['status'] = 'open'
        post['date']=_date(post['datetime'])
        if post.get("replyto"):
            reply=user.readPost(post['replyto'])
            if len(reply)>0:
                post['reply']=reply[0]
                remove.add(post['reply']['id'])
        result.append(post)
    return result

def _reward(profileid, postid, stake):
        execute("UPDATE post SET stake=0 WHERE profileid=%(profileid)s AND id=%(postid)s AND stake=%(stake)s", {'profileid': profileid, 'postid': postid, 'stake': stake})
        commit()
        if rowcount() > 0:
            wallet_address = get_profile_address(profileid)
            reward_wallet = wallet.Wallet(wallet_address)
            reward_wallet.unlock(stake,stake*POST_REWARD)

def _date(post):
    now = float(datetime.now().strftime("%Y%m%d%H%M.%S"))
    delta = now - post
    if delta < 100:
        if delta > 60: delta = delta - 40
        return "{:.0f}m".format(delta)
    elif delta < 10000:
        delta = ((now*24)-(post*24))/10000
        return "{:.0f}h".format(delta+1)
    elif delta < 100000:
        return "{:.0f}d".format(delta/10000)
    else:
        date = datetime.strptime(str(post), "%Y%m%d%H%M.%S" )
        return date.strftime("%b %-d")
