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

@app.before_first_request
def before_first_request():
    db.create_all()

"""Examples"""
@app.route('/')
def index():
    """Example 1: Basic use"""
    btn = DownloadBtn.query.filter_by(name='example1').first()
    if not btn:
        btn = DownloadBtn()
        btn.name = 'example1'
        btn.text = 'Download Example 1'
        btn.filenames = ['hello_world.txt']
        db.session.add(btn)
        db.session.commit()
    return render_template('index.html', download_btn=btn)

@app.route('/example2')
def example2():
    """Example 2: Multiple files"""
    btn = DownloadBtn.query.filter_by(name='example2').first()
    if not btn:
        btn = DownloadBtn()
        btn.name = 'example2'
        btn.text = 'Download Example 2'
        btn.filenames = ['hello_world.txt', 'hello_moon.txt']
        btn.attachment_filename = 'example2.zip'
        db.session.add(btn)
        db.session.commit()
    return render_template('index.html', download_btn=btn)

from flask import url_for

@app.route('/example3')
def example3():
    """Example 3: Callback routes"""
    btn = DownloadBtn.query.filter_by(name='example3').first()
    if not btn:
        btn = DownloadBtn()
        btn.name = 'example3'
        btn.text = 'Download Example 3'
        btn.filenames = ['hello_world.txt']
        btn.callback = url_for('download_success')
        db.session.add(btn)
        db.session.commit()
    return render_template('index.html', download_btn=btn)

@app.route('/download-success')
def download_success():
    return 'Download Successful'

@app.route('/example4')
def example4():
    """Example 4: Form handling"""
    btn = DownloadBtn.query.filter_by(name='example4').first()
    if not btn:
        btn = DownloadBtn()
        btn.name = 'example4'
        btn.text = 'Download Example 4'
        HandleForm(btn, func=select_files)
        db.session.add(btn)
        db.session.commit()
    return render_template('example4.html', download_btn=btn)

def select_files(btn, response):
    btn.filenames = response.getlist('selectFiles')

import time

@app.route('/example5')
def example5():
    """Example 5: File creation"""
    session.clear()
    btn = DownloadBtn.query.filter_by(name='example5').first()
    if not btn:
        btn = DownloadBtn()
        btn.name = 'example5'
        btn.text = 'Download Example 5'
        btn.use_cache = True
        CreateFile(btn, func=create_file1, kwargs={'seconds': 5})
        CreateFile(btn, func=create_file2, kwargs={'centiseconds': 400})
        btn.filenames = ['hello_world.txt', 'hello_moon.txt']
        db.session.add(btn)
        db.session.commit()
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
    session.clear()
    btn = DownloadBtn.query.filter_by(name='example6').first()
    if not btn:
        btn = DownloadBtn()
        btn.name = 'example6'
        btn.btn_classes.remove('btn-primary')
        btn.btn_classes.append('btn-outline-primary')
        btn.progress_classes.append('progress-bar-striped')
        btn.progress_classes.append('progress-bar-animated')
        btn.text = 'Download Example 6'
        HandleForm(btn, func=select_files)
        CreateFile(btn, func=create_file1, kwargs={'seconds': 4})
        CreateFile(btn, func=create_file2, kwargs={'centiseconds': 300})
        btn.transition_speed = '.7s'
        btn.download_msg = 'Download Complete'
        db.session.add(btn)
        db.session.commit()
    return render_template('example6.html', download_btn=btn)

if __name__ == '__main__':
    app.run(debug=True)