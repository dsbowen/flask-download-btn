# Setup

We begin by setting up a Flask app with a Flask-SQLAlchemy database. To use Flask-Download-Btn, we create a `DownloadBtnManager` and a `DownloadBtn` model. Write the following code in `app.py`.

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
    # LATER: HANDLE FORM AND CREATE FILE FUNCTION RELATIONSHIPS GO HERE

# LATER: FUNCTION MODEL DEFINED HERE

# create the database and clear the session when the app starts
@app.before_first_request
def before_first_request():
    db.create_all()
    session.clear()

# DOWNLOAD URLS GO HERE
# VIEW FUNCTIONS GO HERE

if __name__ == '__main__':
    app.run(debug=True)
```

Next, pick two download URLs, or use mine.

```python
HELLO_WORLD_URL = 'https://test-bucket2357.s3.us-east-2.amazonaws.com/hello_world.txt'
HELLO_MOON_URL = 'https://test-bucket2357.s3.us-east-2.amazonaws.com/hello_moon.txt'
```

Now create a Jinja template in your `templates` folder. The template must:

1. Include Bootstrap CSS and Javascript
2. Include the download button script
3. Render the download button and progress bar

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

Our folder structure looks like:

```
templates/
    index.html
app.py
```