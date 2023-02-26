######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask 
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login
import mysql.connector
from mysql.connector import errorcode
from collections import defaultdict

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'b0st0nuniv2023'
app.config['MYSQL_DATABASE_DB'] = 'photoshare6'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('home.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		fname=request.form.get('fname')
		lname=request.form.get('lname')
		email=request.form.get('email')
		password=request.form.get('password')
		gender=request.form.get('gender')
		dob=request.form.get('dob')
		hometown=request.form.get('hometown')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (fname, lname, email, password, gender, dob, hometown) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(fname, lname, email, password, gender, dob, hometown)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('home.html', name=email, message='Account Created!')
	else:
		print("couldn't find all tokens")
		return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]

def getUsersAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT Name, album_id, date_of_creation FROM Albums WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE return a list of tuples, [(Name, album_id, date_of_creation), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

@app.route('/friends', methods=['GET'])
@flask_login.login_required
def friends():
	friends = list_friends()
	return render_template('friends.html', data = friends, supress='True')

def list_friends():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT fname, lname, email FROM Users WHERE user_id IN (SELECT UID2 FROM Friendship WHERE UID1 = '{0}' UNION SELECT UID1 FROM Friendship WHERE UID2 = '{0}')".format(uid))
	data = cursor.fetchall()
	return data

@app.route("/friends", methods=['GET', 'POST'])
@flask_login.login_required
#function which allows you to add a friend
def add_friend():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	try:
		friend = request.form.get('addfriend')
		cursor = conn.cursor()
		cursor.execute("SELECT user_id from Users WHERE email = '{0}'".format(friend))
		uid2 = cursor.fetchall()[0][0]
		cursor.execute("INSERT INTO Friendship (UID1, UID2) VALUES ('{0}', '{1}')".format(uid, uid2))
		conn.commit()
		return render_template('friends.html', message='Friend Added!')
	except mysql.connector.IntegrityError:
		print("already friends")
		return flask.redirect(flask.url_for('friends'))
	except:
		print("error adding friend") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('friends'))
#end friends code



@app.route('/feed')
def feed():
	photos = feed_photos()
	filter_albums = list_albums_public()
	return render_template('feed.html', data = filter_albums, photos = photos, base64 = base64)

@app.route("/feed", methods=['GET'])
def feed_photos():
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures ORDER BY picture_id DESC")
	photo_info = cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]
	completed_tuples = []
	for tup in photo_info:
		cursor = conn.cursor()
		cursor.execute("SELECT COUNT(user_id) FROM Likes WHERE Likes.picture_id = '{0}'".format(tup[1]))
		likes = cursor.fetchall()[0][0]
		likers = list_likers(tup[1])
		cursor = conn.cursor()
		cursor.execute("SELECT email, text FROM Comments INNER JOIN Users ON Users.user_id = Comments.user_id WHERE Comments.picture_id = '{0}'".format(tup[1]))
		comments = cursor.fetchall()
		completed_tuples.append((tup[0], tup[1], tup[2], likes, likers, comments))
	return completed_tuples

def list_albums_public():
	cursor = conn.cursor()
	cursor.execute("SELECT Name FROM Albums")
	albumList = cursor.fetchall()
	return albumList

@app.route("/feed", methods=['POST'])
def filter_by_album():
	album = request.form.get('filterAlbum')
	cursor = conn.cursor()
	cursor.execute("SELECT album_id FROM Albums WHERE Albums.Name = '{0}'".format(album))
	aid = cursor.fetchall()[0][0]

	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE Pictures.album_id = '{0}'".format(aid))
	filtered_photos = cursor.fetchall()

	filter_albums = list_albums_public()

	return render_template('feed.html', data = filter_albums, photos = filtered_photos, base64 = base64)

@app.route("/feed/<photo_id>", methods=['GET', 'POST'])
@flask_login.login_required
def like_photo(photo_id):
	uid = getUserIdFromEmail(flask_login.current_user.id)

	cursor = conn.cursor()
	cursor.execute("SELECT * FROM Likes WHERE Likes.user_id = '{0}' AND Likes.picture_id = '{1}'".format(uid, photo_id))
	like_status = cursor.fetchall()
	if len(like_status) == 0:
		cursor = conn.cursor()
		cursor.execute("INSERT INTO Likes (user_id, picture_id) VALUES ('{0}', '{1}')".format(uid, photo_id))
		conn.commit()
	else:
		cursor = conn.cursor()
		cursor.execute("DELETE FROM Likes WHERE Likes.user_id = '{0}' AND Likes.picture_id = '{1}'".format(uid, photo_id))
		conn.commit()


	photos = feed_photos()
	filter_albums = list_albums_public()
	return render_template('feed.html', data = filter_albums, photos = photos, base64 = base64)


def list_likers(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT fname, lname, email FROM Likes JOIN Users ON Likes.user_id = Users.user_id WHERE Likes.picture_id = '{0}'".format(pid))
	likers = cursor.fetchall()
	return likers
#end feed code


@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('home.html', name=flask_login.current_user.id, message="Here's your profile")

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		album = request.form.get("album")
		cursor = conn.cursor()
		cursor.execute("SELECT album_id FROM Albums WHERE Albums.Name = '{0}'".format(album))
		aid = cursor.fetchall()[0][0]
		photo_data =imgfile.read()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Pictures (imgdata, user_id, caption, album_id) VALUES (%s, %s, %s, %s)''', (photo_data, uid, caption, aid))
		conn.commit()
		return render_template('photos.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		albums = list_albums()
		return render_template('upload.html', data = albums, supress='True')

def list_albums():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT Name FROM Albums WHERE Albums.user_id = '{0}'".format(uid))
	albumList = cursor.fetchall()
	return albumList

#end photo uploading code


@app.route('/photos', methods=['GET'])
@flask_login.login_required
def photos(): 
	uid = getUserIdFromEmail(flask_login.current_user.id)
	photos = getUsersPhotos(uid)
	return render_template('photos.html', photos = photos, supress='True', base64=base64)

@app.route('/photos/<photo_id>', methods=['POST'])
@flask_login.login_required
def delete_photo(photo_id): 
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Pictures WHERE picture_id= '{0}'".format(photo_id))
	conn.commit()
	return render_template('photos.html', photos = getUsersPhotos(uid), supress='True')
#end photo code



@app.route('/albums', methods=['GET'])
@flask_login.login_required
def albums():
	albums = list_albums()
	return render_template('albums.html', data = albums, supress='True')

@app.route('/albums', methods=['POST'])
@flask_login.login_required
def manage_albums():
	if request.form["btn"] == "Create":
		uid = getUserIdFromEmail(flask_login.current_user.id)
		try:
			name = request.form.get('albumName')
			if name == "" or name is None:
				return "Error with album name"
			cursor = conn.cursor()
			cursor.execute("INSERT INTO Albums (user_id, Name) VALUES ('{0}', '{1}')".format(uid, name))
			conn.commit()
			return render_template('albums.html', message="Album '{0}' Created!".format(name))
		except mysql.connector.IntegrityError:
			print("Album name already exists!")
			return flask.redirect(flask.url_four('albums'))
		except:
			print("Error creating new album!")
			return flask.redirect(flask.url_four('albums'))
	elif request.form["btn"] == "Delete":
		try:
			name = request.form.get("deleteAlbum")
			if name == "":
				return "Error: Name is empty"
			if name is None:
				return "Error: Name is None"
			cursor = conn.cursor()
			cursor.execute("SELECT album_id FROM Albums WHERE Albums.Name = '{0}'".format(name))
			aid = cursor.fetchall()[0][0]
			cursor = conn.cursor()
			cursor.execute("DELETE FROM Pictures WHERE Pictures.album_id = '{0}'".format(aid))
			conn.commit()
			cursor = conn.cursor()
			cursor.execute("DELETE FROM Albums WHERE Albums.album_id = '{0}'".format(aid))
			conn.commit()
			return render_template('albums.html', message="Album '{0}' Deleted!".format(name))
		except:
			print("Error deleting album!")
			return flask.redirect(flask.url_four('albums'))
#end album code

@app.route('/recommendations', methods=['GET'])
@flask_login.login_required
def recommendations():
	friend_recs = recommended_friends()
	return render_template('recommendations.html', data = friend_recs, supress='True')


def recommended_friends():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	user_friends = list_friends() #returns a list of tuples (fname, lname, email)
	user_friends_list =  []
	# this loop returns a list of tuples where each tuple contains the user id of the users friends
	for friend in user_friends:
		cursor = conn.cursor()
		cursor.execute("SELECT user_id FROM Users WHERE Users.email = '{0}'".format(friend[2]))
		user_friends_list.append(cursor.fetchall()[0]) 
	# grab each friend of all the friends and add their user_id to a list
	recommendation_list = []
	for friend_uid in user_friends_list:
		cursor = conn.cursor()
		cursor.execute("SELECT fname, lname, email FROM Users WHERE user_id IN (SELECT UID2 FROM Friendship WHERE UID1 = '{0}' AND UID2 <> '{1}' UNION SELECT UID1 FROM Friendship WHERE UID2 = '{0}'  AND UID1 <> '{1}')".format(friend_uid[0], uid))
		recommendation_list += (cursor.fetchall())
	recommendation_dict = defaultdict(int)
	for friend_tuple in recommendation_list:
		recommendation_dict[friend_tuple]+=1
	sorted_dict = sorted(recommendation_dict.items(), key=lambda x:x[1], reverse=True)
	final_with_duplicates = []
	for tup in sorted_dict:
		final_with_duplicates.append(tup[0])
	final_list = []
	for friend in final_with_duplicates:
		if friend not in user_friends:
			final_list.append(friend)
	return final_list
#end recommendations code

@app.route('/add_comment/<photo_id>', methods=['POST'])
@flask_login.login_required
def add_comment(photo_id):
	comment_text = request.form.get("comment")
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("INSERT INTO Comments (text, user_id, picture_id) VALUES ('{0}', '{1}', '{2}')".format(comment_text, uid, photo_id))
	conn.commit()

	photos = feed_photos()
	filter_albums = list_albums_public()
	return render_template('feed.html', data = filter_albums, photos = photos, base64 = base64)

@app.route('/search_comments', methods=["POST"])
@flask_login.login_required
def search_comments():
	comment_text = request.form.get("comment_text")

	#get all user_id who have added a comment that matches the commetn_text
	cursor = conn.cursor()
	cursor.execute("SELECT fname, lname, email FROM Comments JOIN Users on Comments.user_id = Users.user_id WHERE Comments.text = '{0}'".format(comment_text))

	photos = feed_photos()
	filter_albums = list_albums_public()
	return render_template('feed.html', data = filter_albums, photos = photos, comment_search = cursor.fetchall(), comm_text = comment_text, base64 = base64)

#end comments code

#default page
@app.route("/", methods=['GET'])
def home():
	return render_template('home.html', message='Welecome to Photoshare')


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
