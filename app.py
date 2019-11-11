"""Example app"""

"""Setup"""
# 1. Import download button manager and mixins
from flask_download_btn import CreateFileMixin, DownloadBtnManager, DownloadBtnMixin, HandleFormMixin

from flask import Flask, render_template, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# 2. Initialize download button manager with application and database
download_btn_manager = DownloadBtnManager(app, db=db)

# 3. Create download button model and register it with the manager
@DownloadBtnManager.register
class DownloadBtn(DownloadBtnMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

# 4. Create CreateFile and HandleForm models
class CreateFile(CreateFileMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bnt_id = db.Column(db.Integer, db.ForeignKey('download_btn.id'))

class HandleForm(HandleFormMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bnt_id = db.Column(db.Integer, db.ForeignKey('download_btn.id'))

# 5. Create database tables
db.create_all()

"""Helper methods"""
def get_btn(key):
    if key in session:
        return DownloadBtn.query.get(session[key])

def add_to_session(btn, key):
    db.session.add(btn)
    db.session.commit()
    session[key] = btn.id

@app.before_first_request
def clear_session():
    session.clear()

"""Examples"""
@app.route('/')
def index():
    """Example 1: Basic use"""
    btn = get_btn('example1')
    if not btn:
        btn = DownloadBtn()
        btn.text = 'Download Example 1'
        btn.files = ['hello_world.txt']
        add_to_session(btn, 'example1')
    return render_template('index.html', download_btn=btn)

@app.route('/example2')
def example2():
    """Example 2: Multiple files"""
    btn = get_btn('example2')
    if not btn:
        btn = DownloadBtn()
        btn.text = 'Download Example 2'
        btn.files = [
            'hello_world.txt', 'hello_moon.txt', ('tmp', 'hello_star.txt')
        ]
        btn.attachment_filename = 'example2.zip'
        add_to_session(btn, 'example2')
    return render_template('index.html', download_btn=btn)

from flask import url_for

@app.route('/example3')
def example3():
    """Example 3: Callback routes"""
    btn = get_btn('example3')
    if not btn:
        btn = DownloadBtn()
        btn.text = 'Download Example 3'
        btn.files = ['hello_world.txt']
        btn.callback = url_for('download_success')
        add_to_session(btn, 'example3')
    return render_template('index.html', download_btn=btn)

@app.route('/download-success')
def download_success():
    return 'Download Successful'

@app.route('/example4')
def example4():
    """Example 4: Form handling"""
    btn = get_btn('example4')
    if not btn:
        btn = DownloadBtn()
        btn.text = 'Download Example 4'
        HandleForm(btn, func=select_files)
        add_to_session(btn, 'example4')
    return render_template('example4.html', download_btn=btn)

def select_files(btn, response):
    btn.files = response.getlist('selectFiles')

import time

@app.route('/example5')
def example5():
    """Example 5: File creation"""
    btn = get_btn('example5')
    if not btn:
        btn = DownloadBtn()
        btn.text = 'Download Example 5'
        btn.use_cache = True
        CreateFile(btn, func=create_file1, kwargs={'seconds': 5})
        CreateFile(btn, func=create_file2, kwargs={'centiseconds': 400})
        btn.files = ['hello_world.txt', 'hello_moon.txt']
        add_to_session(btn, 'example5')
    return render_template('index.html', download_btn=btn)

def create_file1(btn, seconds):
    yield btn.reset(stage='Download Started', pct_complete=0)
    for i in range(seconds):
        yield btn.report('Creating File 1', 100.0*i/seconds)
        time.sleep(1)
    yield btn.report('Creating file 1', 100.0)
    time.sleep(1)

def create_file2(btn, centiseconds):
    yield btn.reset('Creating File 2', 0)
    for i in range(centiseconds):
        yield btn.report('Creating File 2', 100.0*i/centiseconds)
        time.sleep(.01)
    yield btn.report('Download Complete', 100)
    time.sleep(.01)

@app.route('/example6')
def example6():
    """Example 6: With style"""
    btn = get_btn('example6')
    if not btn:
        btn = DownloadBtn()
        btn.btn_classes.remove('btn-primary')
        btn.btn_classes.append('btn-outline-primary')
        btn.progress_classes.append('progress-bar-striped')
        btn.progress_classes.append('progress-bar-animated')
        btn.text = 'Download Example 6'
        HandleForm(btn, func=select_files)
        CreateFile(btn, func=create_file1, kwargs={'seconds': 4})
        CreateFile(btn, func=create_file2, kwargs={'centiseconds': 300})
        btn.download_msg = 'Download Complete'
        add_to_session(btn, 'example6')
    return render_template('example6.html', download_btn=btn)

if __name__ == '__main__':
    app.run(debug=True)