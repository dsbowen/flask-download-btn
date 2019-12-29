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

# 4. Create `CreateFile` and `HandleForm` models
class CreateFile(CreateFileMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bnt_id = db.Column(db.Integer, db.ForeignKey('download_btn.id'))

class HandleForm(HandleFormMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bnt_id = db.Column(db.Integer, db.ForeignKey('download_btn.id'))

# 5. Create database tables
db.create_all()

"""Helper methods and download URLs"""
HELLO_WORLD_URL = 'https://test-bucket2357.s3.us-east-2.amazonaws.com/hello_world.txt'
HELLO_MOON_URL = 'https://test-bucket2357.s3.us-east-2.amazonaws.com/hello_moon.txt'

def add_to_session(btn, key):
    db.session.add(btn)
    db.session.commit()
    session[key] = btn.id

def get_btn(key):
    if key in session:
        return DownloadBtn.query.get(session[key])

@app.before_first_request
def clear_session():
    session.clear()

"""Example 1: Basic use"""
@app.route('/')
def index():
    btn = get_btn('basic')
    if not btn:
        btn = DownloadBtn()
        btn.downloads = [(HELLO_WORLD_URL, 'hello_world.txt')]
        add_to_session(btn, 'basic')
    return render_template('index.html', download_btn=btn)

"""Example 2: Multiple files"""
@app.route('/mutli-file')
def multi_file():
    btn = get_btn('mutli-file')
    if not btn:
        btn = DownloadBtn()
        btn.downloads = [
            (HELLO_WORLD_URL, 'hello_world.txt'), 
            (HELLO_MOON_URL, 'hello_moon.txt')
        ]
        add_to_session(btn, 'mutli-file')
    return render_template('index.html', download_btn=btn)

"""Example 3: Callback routes"""
from flask import url_for

@app.route('/callback')
def callback():
    btn = get_btn('callback')
    if not btn:
        btn = DownloadBtn()
        btn.downloads = [(HELLO_WORLD_URL, 'hello_world.txt')]
        btn.callback = url_for('download_success')
        add_to_session(btn, 'callback')
    return render_template('index.html', download_btn=btn)

@app.route('/download-success')
def download_success():
    return 'Download Successful'

"""Example 4: Form handling"""
@app.route('/form-handling')
def form_handling():
    btn = get_btn('form-handling')
    if not btn:
        btn = DownloadBtn()
        HandleForm.select_files(btn)
        add_to_session(btn, 'form-handling')
    return render_template('form-handling.html', download_btn=btn)

@HandleForm.register
def select_files(btn, resp):
    btn.downloads = []
    files = resp.getlist('selectFiles')
    if 'hello_world.txt' in files:
        btn.downloads.append((HELLO_WORLD_URL, 'hello_world.txt'))
    if 'hello_moon.txt' in files:
        btn.downloads.append((HELLO_MOON_URL, 'hello_moon.txt'))

"""Example 5: File creation"""
import time

@app.route('/file-creation')
def file_creation():
    btn = get_btn('file-creation')
    if not btn:
        btn = DownloadBtn()
        btn.cache = 'default'
        CreateFile.create_file1(btn, seconds=5)
        CreateFile.create_file2(btn, centiseconds=400)
        btn.downloads = [
            (HELLO_WORLD_URL, 'hello_world.txt'), 
            (HELLO_MOON_URL, 'hello_moon.txt')
        ]
        add_to_session(btn, 'file-creation')
    return render_template('index.html', download_btn=btn)

@CreateFile.register
def create_file1(btn, seconds):
    stage = 'Creating File 1'
    yield btn.reset(stage=stage, pct_complete=0)
    if not btn.downloaded:
        for i in range(seconds):
            yield btn.report(stage, 100.0*i/seconds)
            time.sleep(1)
        yield btn.report(stage, 100.0)
        time.sleep(1)

@CreateFile.register
def create_file2(btn, centiseconds):
    stage = 'Creating File 2'
    yield btn.reset(stage, 0)
    if not btn.downloaded:
        for i in range(centiseconds):
            yield btn.report(stage, 100.0*i/centiseconds)
            time.sleep(.01)
        yield btn.report(stage, 100)
        time.sleep(.01)

"""Example 6: Temporary file creation"""
from base64 import b64encode

@app.route('/tmp-files')
def tmp_files():
    btn = get_btn('tmp-files')
    if not btn:
        btn = DownloadBtn()
        CreateFile.create_tmp_file(btn)
        add_to_session(btn, 'tmp-files')
    return render_template('index.html', download_btn=btn)

@CreateFile.register
def create_tmp_file(btn):
    stage = 'Creating temporary file'
    yield btn.reset(stage, 0)
    data = b64encode(b'Hello World')
    url = 'data:text/plain;base64,' + data.decode()
    btn.tmp_downloads = [(url, 'tmp_file.txt')]
    yield btn.report(stage, 100)

"""Example 7: With style"""
@app.route('/style')
def style():
    btn = get_btn('style')
    if not btn:
        btn = DownloadBtn()
        btn.btn_text = 'Custom Button Text'
        btn.btn_tag['class'].remove('btn-primary')
        btn.btn_tag['class'].append('btn-outline-primary')
        btn.progress_bar_tag['class'] += [
            'progress-bar-striped', 'progress-bar-animated'
        ]
        btn.cache = 'default'
        HandleForm.select_files(btn)
        CreateFile.create_file1(btn, seconds=4)
        CreateFile.create_file2(btn, centiseconds=300)
        btn.download_msg = 'Download Complete'
        add_to_session(btn, 'style')
    return render_template('style.html', download_btn=btn)

if __name__ == '__main__':
    app.run(debug=True)