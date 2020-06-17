Flask-Download-Btn defines a [SQLALchemy Mixin](https://docs.sqlalchemy.org/en/13/orm/extensions/declarative/mixins.html) for creating [Bootstrap](https://getbootstrap.com/) download buttons in a [Flask](https://palletsprojects.com/p/flask/) application.

Its features include:

1. **Automatic enabling and disabling.** A download button is automatically disabled on click and re-enabled on download completion.
2. **CSRF protection.** The download button checks for a CSRF authentication token to ensure the client has permission to download the requested file.
3. **Web form handling.** Download buttons are responsive to web forms.
4. **Pre-download operations.** Download buttons can easily perform operations before files are downloaded, making it easy to create temporary download files.
5. **Progress bar.** Update your clients on download progress with server sent events.

## Installation

```
$ pip install flask-download-btn
```

## Quickstart

Our folder structure will look like:

```
templates/
    index.html
app.py
```

In `templates/index.html`, paste the following Jinja template:

```html
<html>
    <head>
        <!-- include Bootstrap CSS and Javascript -->
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css">
        <script src="https://code.jquery.com/jquery-3.4.1.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/popper.js@1.16.0/dist/umd/popper.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/js/bootstrap.min.js"></script>
        <!-- include download button script -->
        {{ download_btn.script() }}
    </head>
    <body>
        <!-- render the download button and progress bar -->
        {{ download_btn.btn.render() }}
        {{ download_btn.render_progress() }}
    </body>
</html>
```

In `app.py`:

```python
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

# create the database and clear the session when the app starts
@app.before_first_request
def before_first_request():
    db.create_all()
    session.clear()

HELLO_WORLD_URL = 'https://test-bucket2357.s3.us-east-2.amazonaws.com/hello_world.txt'

# basic use
@app.route('/')
def index():
    btn = DownloadBtn()
    btn.downloads = [(HELLO_WORLD_URL, 'hello_world.txt')]
    db.session.commit()
    return render_template('index.html', download_btn=btn)
```

Run the app with:

```
$ python app.py
```

And navigate to <http://localhost:5000/>. Click the download button to download a text file with `'Hello, World!'`.

## Citation

```
@software{bowen2020flask-download-btn,
  author = {Dillon Bowen},
  title = {Flask-Download-Btn},
  url = {https://dsbowen.github.io/flask-download-btn/},
  date = {2020-06-17},
}
```

## License

Users must cite this package in any publications which use it.

It is licensed with the MIT [License](https://github.com/dsbowen/flask-download-btn/blob/master/LICENSE).