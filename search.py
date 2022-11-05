from database import execute, fetchall

def dict_factory(row):
    return row['field']

def search_users(search):
    execute("SELECT * FROM (SELECT name||' @'||handle AS field FROM profile ORDER by name LIMIT 50) AS a UNION SELECT * FROM (SELECT '@'||handle AS field FROM profile ORDER BY handle LIMIT 50) AS b")
    profiles = list(map(dict_factory,fetchall()))
    execute("SELECT '#'||hashtag AS field FROM hashtag INNER JOIN (SELECT *,COUNT(*) AS ct FROM (SELECT hashtagid FROM tag ORDER BY rowid  DESC LIMIT 100) AS a GROUP BY hashtagid ORDER BY ct DESC) AS b ON hashtag.id=hashtagid LIMIT 15")
    hashtags = list(map(dict_factory,fetchall()))
    rows = profiles + hashtags
    if len(search) > 0:
        if search[0]=='@':
            execute("SELECT '@'||handle AS field FROM profile ORDER BY handle LIMIT 50", {'search': search[1:]})
        elif search[0]=='#':
            execute("SELECT '#'||hashtag AS field FROM hashtag ORDER BY hashtag LIMIT 50", {'search': search[1:]})
        else:
            execute("SELECT * FROM (SELECT name||' @'||handle AS field FROM profile WHERE name LIKE %(search)s ORDER by name LIMIT 50) AS a UNION SELECT * FROM (SELECT '@'||handle AS field FROM profile WHERE handle LIKE %(search)s ORDER BY handle LIMIT 50) AS b", {'search': search+'%'})
        if results:=list(map(dict_factory,fetchall())):
            rows = sorted(set(rows+results))
    if rows == None:
        return []
    return rows