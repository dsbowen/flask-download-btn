"""Example app"""

# 1. Import download button manager and mixin
from flask_download_btn import DownloadBtnManager, DownloadBtnMixin

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# 2. Initialize download button manager with application
download_btn_manager = DownloadBtnManager(app)

# 3. Create download button model and register it with the manager
@DownloadBtnManager.register
class DownloadBtn(DownloadBtnMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

def get_btn(name):
    btn = DownloadBtn.query.filter_by(name=name).first()
    if not btn:
        btn = DownloadBtn()
        btn.name = name
        db.session.add(btn)
    return btn

@app.before_first_request
def before_first_request():
    db.create_all()

@app.route('/')
def index():
    """Example 1: Basic use"""
    btn = get_btn('example1')
    btn.text = 'Download Example 1'
    btn.filenames = ['hello_world.txt']
    db.session.commit()
    return render_template('index.html', download_btn=btn)

@app.route('/example2')
def example2():
    """Example 2: Multiple files"""
    btn = get_btn('example2')
    btn.text = 'Download Example 2'
    btn.filenames = ['hello_world.txt', 'hello_moon.txt']
    btn.attachment_filename = 'download.zip'
    db.session.commit()
    return render_template('index.html', download_btn=btn)

@app.route('/example3')
def example3():
    """Example 3: make_file function"""
    btn = get_btn('example3')
    btn.text = 'Download Example 3'
    btn.filenames = ['hello_world.txt']
    btn.make_files = make_files
    btn.kwargs = {'centiseconds': 200}
    db.session.commit()
    return render_template('index.html', download_btn=btn)

def make_files(btn, centiseconds):
    yield btn.report(stage='Download Started', pct_complete=0)
    for i in range(centiseconds):
        yield btn.report('Making Files stage 1', 100.0*i/centiseconds)
        time.sleep(.01)
    for i in range(centiseconds):
        yield btn.report('Making files stage 2', 100.0*i/centiseconds)
        time.sleep(.01)

@app.route('/example4')
def example4():
    btn = get_btn('example4')
    btn.text = 'Download Example 4'
    btn.form_id = 'formId'
    btn.form_handler = select_files
    db.session.commit()
    return render_template('example4.html', download_btn=btn)

def select_files(btn, response):
    btn.filenames = response.getlist('selectFiles')
    db.session.commit()

if __name__ == '__main__':
    app.run()