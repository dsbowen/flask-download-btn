from flask_download_btn import DownloadBtnManager, DownloadBtnMixin

from flask import Flask, render_template, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_mutable import partial

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# initialize download button manager with application and database
download_btn_manager = DownloadBtnManager(app, db=db)


# create download button model and register it with the manager
@DownloadBtnManager.register
class DownloadBtn(DownloadBtnMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)


# create the database and clear the session when the app starts
@app.before_first_request
def before_first_request():
    db.create_all()
    session.clear()

# download URLs
HELLO_WORLD_URL = 'https://test-bucket2357.s3.us-east-2.amazonaws.com/hello_world.txt'
HELLO_MOON_URL = 'https://test-bucket2357.s3.us-east-2.amazonaws.com/hello_moon.txt'

# basic use
@app.route('/')
def index():
    btn = DownloadBtn()
    btn.downloads = (HELLO_WORLD_URL, 'hello_world.txt')
    print(btn.btn_attrs)
    db.session.add(btn)
    db.session.commit()
    return render_template('index.html', download_btn=btn)

# multiple files
@app.route('/multi-file')
def multi_file():
    btn = DownloadBtn()
    btn.downloads = [
        (HELLO_WORLD_URL, 'hello_world.txt'), 
        (HELLO_MOON_URL, 'hello_moon.txt')
    ]
    db.session.add(btn)
    db.session.commit()
    return render_template('index.html', download_btn=btn)

# callback routes
from flask import url_for

@app.route('/callback')
def callback():
    btn = DownloadBtn()
    btn.downloads = (HELLO_WORLD_URL, 'hello_world.txt')
    btn.callback = url_for('download_success')
    db.session.add(btn)
    db.session.commit()
    return render_template('index.html', download_btn=btn)

@app.route('/download-success')
def download_success():
    return 'Download Successful'

# web form handling
@app.route('/form-handling')
def form_handling():
    btn = DownloadBtn()
    btn.handle_form_functions = select_files
    db.session.add(btn)
    db.session.commit()
    return render_template('form-handling.html', download_btn=btn)

def select_files(response, btn):
    btn.downloads.clear()
    files = response.getlist('selectFiles')
    if 'hello_world.txt' in files:
        btn.downloads.append((HELLO_WORLD_URL, 'hello_world.txt'))
    if 'hello_moon.txt' in files:
        btn.downloads.append((HELLO_MOON_URL, 'hello_moon.txt'))

# file creation
import string
from random import choices

@app.route('/file-creation')
def file_creation():
    btn = DownloadBtn()
    btn.cache = 'default'
    btn.create_file_functions = [
        partial(create_file0, msg='Hello, World!'), 
        partial(create_file1, msg=choices(string.ascii_letters, k=400))
    ]
    db.session.add(btn)
    db.session.commit()
    return render_template('index.html', download_btn=btn)

import time
from base64 import b64encode

def create_file0(btn, msg):
    if btn.downloaded:
        return
    stage = 'Creating File 0'
    yield btn.reset(stage=stage, pct_complete=0)
    data = ''
    for i, char in enumerate(msg):
        data += char
        yield btn.report(stage, 100.0*i/len(msg))
        time.sleep(.5)
    data = b64encode(data.encode())
    url = 'data:text/plain;base64,' + data.decode()
    btn.downloads = (url, 'tmp_file0.txt')
    db.session.commit()
    yield btn.report(stage, 100.0)

def create_file1(btn, msg):
    stage = 'Creating File 1'
    yield btn.reset(stage, 0)
    data = ''
    for i, char in enumerate(msg):
        data += char
        yield btn.report(stage, 100.0*i/len(msg))
        time.sleep(.01)
    data = b64encode(data.encode())
    url = 'data:text/plain;base64,' + data.decode()
    btn.tmp_downloads = (url, 'tmp_file1.txt')
    yield btn.report(stage, 100)

# button styling
@app.route('/style')
def style():
    btn = DownloadBtn()
    btn.btn_text = 'Custom Button Text'
    btn.btn_attrs['class'].remove('btn-primary')
    btn.btn_attrs['class'].append('btn-outline-primary')
    btn.progress_bar_attrs['class'] += [
        'progress-bar-striped', 'progress-bar-animated'
    ]
    btn.handle_form_functions = select_tmp_files
    btn.download_msg = 'Download Complete'
    db.session.add(btn)
    db.session.commit()
    return render_template('style.html', download_btn=btn)

def select_tmp_files(response, btn):
    btn.downloads.clear()
    btn.create_file_functions.clear()
    files = response.getlist('selectFiles')
    if 'hello_world.txt' in files:
        btn.downloads = (HELLO_WORLD_URL, 'hello_world.txt')
    if 'ascii.txt' in files:
        file_content = choices(string.ascii_letters, k=200)
        btn.create_file_functions = partial(create_file1, file_content)

if __name__ == '__main__':
    app.run(debug=True)