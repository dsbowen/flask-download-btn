from flask_download_btn import DownloadBtnManager, DownloadBtnMixin

from flask import Flask, render_template, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.orderinglist import ordering_list

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

    handle_form_functions = db.relationship(
        'Function',
        order_by='Function.index',
        collection_class=ordering_list('index'),
        foreign_keys='Function.handle_form_id'
    )
    
    create_file_functions = db.relationship(
        'Function',
        order_by='Function.index',
        collection_class=ordering_list('index'),
        foreign_keys='Function.create_file_id'
    )


# create a Function model for form handling and file creation
from sqlalchemy_function import FunctionMixin

class Function(FunctionMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    index = db.Column(db.Integer)
    handle_form_id = db.Column(db.Integer, db.ForeignKey('download_btn.id'))
    create_file_id = db.Column(db.Integer, db.ForeignKey('download_btn.id'))


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
    btn.downloads = [(HELLO_WORLD_URL, 'hello_world.txt')]
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
    db.session.commit()
    return render_template('index.html', download_btn=btn)

# callback routes
from flask import url_for

@app.route('/callback')
def callback():
    btn = DownloadBtn()
    btn.downloads = [(HELLO_WORLD_URL, 'hello_world.txt')]
    btn.callback = url_for('download_success')
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
        Function(create_file0, msg='Hello, World!'), 
        Function(create_file1, msg=choices(string.ascii_letters, k=400))
    ]
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
    btn.downloads = [(url, 'tmp_file0.txt')]
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
    btn.tmp_downloads = [(url, 'tmp_file1.txt')]
    yield btn.report(stage, 100)

# button styling
@app.route('/style')
def style():
    btn = DownloadBtn()
    btn.btn_text = 'Custom Button Text'
    btn.btn_tag['class'].remove('btn-primary')
    btn.btn_tag['class'].append('btn-outline-primary')
    btn.progress_bar['class'] += [
        'progress-bar-striped', 'progress-bar-animated'
    ]
    btn.handle_form_functions = select_tmp_files
    btn.download_msg = 'Download Complete'
    db.session.commit()
    return render_template('style.html', download_btn=btn)

def select_tmp_files(response, btn):
    btn.downloads.clear()
    btn.create_file_functions.clear()
    files = response.getlist('selectFiles')
    if 'hello_world.txt' in files:
        btn.downloads = [(HELLO_WORLD_URL, 'hello_world.txt')]
    if 'ascii.txt' in files:
        btn.create_file_functions = [
            Function(create_file1, choices(string.ascii_letters, k=200))
        ]

if __name__ == '__main__':
    app.run(debug=True)