# Basic use

We start with a basic example in which we create a download button with a single download file. The download URL is `HELLO_WORLD_URL`, and the download file will be named `hello_world.txt`.

Put this view function in `app.py`

```python
@app.route('/')
def index():
    btn = DownloadBtn()
    btn.downloads = [(HELLO_WORLD_URL, 'hello_world.txt')]
    db.session.commit()
    return render_template('index.html', download_btn=btn)
```

Now we are ready to run our app. In your terminal window, enter:

```
$ python app.py
```

And navigate to <http://localhost:5000/>. Click the download button to download `hello_world.txt`.

## Downloading multiple files

We create a download button which downloads two files: `hello_world.txt` and `hello_moon.txt`.

```python
@app.route('/multi-file')
def multi_file():
    btn = DownloadBtn()
    btn.downloads = [
        (HELLO_WORLD_URL, 'hello_world.txt'), 
        (HELLO_MOON_URL, 'hello_moon.txt')
    ]
    db.session.commit()
    return render_template('index.html', download_btn=btn)
```

## Callback routes

This download button will redirect the client to a 'Success' page after the download has finished.

```python
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
```