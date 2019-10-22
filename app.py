from flask_download_btn import DownloadBtnManager, DownloadBtnMixin

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
download_btn_manager = DownloadBtnManager(app)

@download_btn_manager.register
class DownloadBtn(DownloadBtnMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

@app.before_first_request
def before_first_request():
    db.create_all()
    d = DownloadBtn(text='Download')
    db.session.add(d)
    db.session.commit()

@app.route('/')
def index():
    d = DownloadBtn.query.first()
    return render_template('index.html', download_btn=d)

if __name__ == '__main__':
    app.run()