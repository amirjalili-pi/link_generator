import datetime
import json

from flask import Flask, render_template, redirect, url_for, jsonify, request, flash
from flask_bootstrap import Bootstrap
import pymongo
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, BooleanField
from wtforms.validators import DataRequired, URL
from bson.objectid import ObjectId


# Encoder
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


# App Settings
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6dnzWlSihBXox7C0sKR6b'
Bootstrap(app)

# Database Settings
client = pymongo.MongoClient('127.0.0.1', 27017)
db = client.place
video = db.link
accounts = db.account


# Forms
class GenerateLinkForm(FlaskForm):
    user_name = StringField("User Name", validators=[DataRequired()])
    expire_at = DateField("Expire At", validators=[DataRequired()])
    video_url = StringField("Video Url", validators=[DataRequired(), URL()])
    show_controls = BooleanField("Show Controls")
    loop_play = BooleanField("Loop Play")
    submit = SubmitField("Generate Link")


# Add Some Data to Database
# accounts.insert_many([{"name": "Amirmahdi", "family": "Jalili", "age": 23},
#                       {"name": "Hasan", "family": "Afshar", "age": "20"}])


# Main page
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/add", methods=["get", "post"])
def add():
    form = GenerateLinkForm()
    if request.method == "POST":
        if form.validate_on_submit():
            account = accounts.find_one({"name": form.user_name.data})
            if account:
                video.insert_one({"player_id": account["_id"],
                                  "video_url": form.video_url.data,
                                  "created_at": datetime.datetime.now().strftime("%Y/%m/%d"),
                                  "expired_at": form.expire_at.data.strftime("%Y/%m/%d"),
                                  "show_controls": form.show_controls.data,
                                  "loop_play": form.loop_play.data})
                last_video = list(video.find().sort([("_id", pymongo.DESCENDING)]))[0]
                flash(f"You're link: http://127.0.0.1:5000/video_link?pid={account['_id']}&vid={last_video['_id']}",
                      "success")
                return redirect("/")
            flash("Something happened try again")
            return redirect("/")
    return render_template('add.html', form=form)


@app.route("/video_link")
def video_link():
    video_id = request.args.get("vid")
    target_video = video.find_one({"_id": ObjectId(video_id)})
    if target_video:
        create_date = datetime.datetime.strptime(target_video["created_at"], "%Y/%m/%d")
        expire_date = datetime.datetime.strptime(target_video["expired_at"], "%Y/%m/%d")
        if create_date > expire_date:
            return jsonify({"msg": "Sorry the link is expired"}), 404
        data = json.loads(JSONEncoder().encode(target_video))
        return render_template("player.html", url=target_video["video_url"],
                               control=json.dumps(data["show_controls"]), loop=json.dumps(data["loop_play"]))
