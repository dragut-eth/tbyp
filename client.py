from web3 import Web3
from eth_account.messages import encode_defunct
import re
import secrets
from os import environ as config
from flask import Flask, render_template, redirect, request, session, url_for, abort, send_from_directory, flash, escape
from flask_session import Session
from werkzeug.exceptions import HTTPException
from wallet import Wallet
from user import User
import main
import database

SIGNING_MESSAGE = "Sign this message to prove that you have access to this wallet and log in. This won’t cost you anything."

app = Flask(__name__)
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = "filesystem"
Session(app)

database.initialize() 

@app.route("/")
def index():
    if not session.get("wallet"):
        return redirect("/connect")

    if request.args.get("profile"):
        session["profile"] = int(request.args.get("profile"))

    wallet = Wallet(session["wallet"])
    if session.get("profile"):
        user = User(wallet, session["profile"])
    else:
        user = None

    if user and request.args.get("post"):
        post = user.readPost(request.args.get("post"))
    else:
        post = None

    if request.args.get("@"):
        if profileid := main.get_profile_id(request.args.get("@")):
            profile = main.get_profile(profileid)
        else:
            profile = None
    else:
        profile = None

    if request.args.get("H"):
        if hashtagid := main.get_hashtag_id(request.args.get("H")):
            hashtag = main.get_hashtag(hashtagid)
        else:
            hashtag = None
    else:
        hashtag = None


    return render_template('index.html', wallet=wallet, user=user, profile=profile, post=post, hashtag=hashtag, config=config)

@app.route("/post", methods=["POST"])
def post():
    if request.method == "POST":
        if request.form.get("post") and session["wallet"] and session["profile"]:
            wallet = Wallet(session["wallet"])
            user = User(wallet, session["profile"])
            user.writePost(request.form.get("post"))
    return redirect("/")

@app.route("/update/<int:postid>", methods=["POST", "GET"])
def update(postid):
    params = next(iter(request.referrer.split("?")[1:2]), "")
    if request.method == "GET":
        if session["wallet"] and session["profile"]:
            wallet = Wallet(session["wallet"])
            user = User(wallet, session["profile"])
            if request.args.get("delete"):
                user.deletePost(postid)
            else:
                return render_template("update.html", params=params, post=user.get_post(postid))

    elif request.method == "POST":
        if session["wallet"] and session["profile"]:
            wallet = Wallet(session["wallet"])
            user = User(wallet, session["profile"])
            user.editPost(postid, request.form.get("post"))

    return redirect(f"/?{params}")

@app.route("/reply/<int:postid>", methods=["POST"])
def reply(postid):
    if session["wallet"] and session["profile"]:
        wallet = Wallet(session["wallet"])
        user = User(wallet, session["profile"])
        user.replyPost(postid, request.form.get("post"))

    return redirect(f"/?post={postid}")

@app.route("/connect", methods=["POST", "GET"])
def connect():
    if request.method == "POST":
        signature = request.form.get("signature")
        address = request.form.get("wallet")
        message = SIGNING_MESSAGE + "\n\n" + session["secret"]
        message = encode_defunct(text=message)
        w3 = Web3()
        result = w3.eth.account.recover_message(message, signature=signature)
        if result == address:
            session["wallet"] = address
            if profile_list:=main.list_profiles(address):
                if len(profile_list)==1:
                    return redirect(f"/?profile={profile_list[0]['id']}")
            return redirect("/")

    session["secret"] = secrets.token_urlsafe()
    message = SIGNING_MESSAGE + "\\n\\n" + session["secret"]
    return render_template("connect.html", message=message)

@app.route("/create", methods=["POST", "GET"])
def create():
    if not session.get("wallet"):
        return redirect("/connect")
    session["profile"] = None
   
    if request.method == "POST":
        if name:=request.form.get("name"):
            wallet = Wallet(session["wallet"])
            profileid = wallet.createAccount(name)
            if not profileid:
                flash('profile already exist or not enough credit', 'error')
                return render_template("create.html")
            session["profile"] = profileid
        return redirect("/")
    return render_template("create.html")

@app.route("/edit/<int:profileid>", methods=["POST", "GET"])
def edit(profileid):
    if request.method == "GET":
        profile = main.get_profile(profileid)

    elif request.method == "POST":
        if request.form.get("handle") and request.form.get("name") and session["wallet"]:
            wallet = Wallet(session["wallet"])
            user = User(wallet, profileid)
            if not user.editAccount(request.form.get("handle"),request.form.get("name")):
                flash('profile already exist', 'error')
                return render_template("edit.html", profile=user)
        return redirect("/")

    return render_template("edit.html", profile=profile)

@app.route("/delete/<int:profileid>")
def delete(profileid):
    if session["wallet"]:
        wallet = Wallet(session["wallet"])
        user = User(wallet, profileid)
        user.deleteAccount()

    session["profile"] = None
    return redirect("/")

@app.template_global()
def feed(profileid=None):
    if session["wallet"] and session["profile"]:
        wallet = Wallet(session["wallet"])
        user = User(wallet, session["profile"])
        if profileid:
            feed = User(wallet, profileid).posts(user)
        else:
            feed = user.feed()
        return feed
    abort(404)

@app.template_global()
def forum(hashtagid):
    if session["wallet"] and session["profile"]:
        wallet = Wallet(session["wallet"])
        user = User(wallet, session["profile"])
        return main.forum(hashtagid, user)
    abort(404)

@app.template_global()
def thread(postid):
    if session["wallet"] and session["profile"]:
        wallet = Wallet(session["wallet"])
        user = User(wallet, session["profile"])
        return main.thread(postid, user)
    abort(404)

@app.template_global()
def list_user_profiles():
    if session["wallet"]:
        return main.list_profiles(session["wallet"])
    return False

@app.template_global()
def new_profiles():
    return main.get_new_profiles()

@app.template_global()
def popular_tags():
    return main.get_popular_tags()

@app.route("/upvote/<int:postid>")
def upvote(postid):
    params = next(iter(request.referrer.split("?")[1:2]), "")
    if session["wallet"] and session["profile"]:
        wallet = Wallet(session["wallet"])
        user = User(wallet, session["profile"])
        user.yea(postid)
    return redirect(f"/?{params}")

@app.route("/downvote/<int:postid>")
def downvote(postid):
    params = next(iter(request.referrer.split("?")[1:2]), "")
    if session["wallet"] and session["profile"]:
        wallet = Wallet(session["wallet"])
        user = User(wallet, session["profile"])
        user.nay(postid)
    return redirect(f"/?{params}")

@app.route("/follow/<int:followid>")
def follow(followid):
    if session["wallet"] and session["profile"]:
        wallet = Wallet(session["wallet"])
        user = User(wallet, session["profile"])
        user.follow(followid)
    return redirect("/")

@app.route("/unfollow/<int:followid>")
def unfollow(followid):
    if session["wallet"] and session["profile"]:
        wallet = Wallet(session["wallet"])
        user = User(wallet, session["profile"])
        user.unfollow(followid)
    return redirect("/")

@app.route("/explorer", methods=["POST", "GET"])
def explorer():
    search = ""
    if request.method == "POST":
        if search:=request.form.get("search"):
            handle = re.findall("@(\w+)", search)
            if len(handle)>0:
                if main.get_profile_id(handle[0]):
                    return redirect(f"/?@={handle[0]}")
            handle = re.findall("#(\w+)", search)
            if len(handle)>0:
                if main.get_hashtag_id(handle[0]):
                    return redirect(f"/?H={handle[0]}")
    fields = main.search(search)
    fields = [str(escape(field)) for field in fields]
    return render_template("explorer.html", fields=fields, search=search)

@app.route("/logout")
def logout():
    session["wallet"] = session["profile"] = None
    return redirect("/")

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static','favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.before_request
def before_request():
    pass

@app.after_request
def after_request(response):
    return response

@app.route("/error", methods=["POST", "GET"])
def error():
    abort(400)

@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return e
    flash(e, 'error')
    print(e)

if __name__ == "__main__":
        app.run(debug=True)

