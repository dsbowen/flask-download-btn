# File creation

We often want to perform an operation before a file is downloaded. This operation often involves creating the download file itself.

In this example, we create two temporary download files and report download progress to the client using a progress bar.

## Relationship

We add a `create_file_functions` relationship from `DownloadBtn` to `Function`.

```python
@DownloadBtnManager.register
class DownloadBtn(DownloadBtnMixin, db.Model):
    ...
    create_file_functions = db.relationship(
        'Function',
        order_by='Function.index',
        collection_class=ordering_list('index'),
        foreign_keys='Function.create_file_id'
    )

...

class Function(FunctionMixin, db.Model):
    ...
    create_file_id = db.Column(db.Integer, db.ForeignKey('download_btn.id'))
```

## View function

We add the following view function to `app.py`.

```python
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
```

## Create file functions

Create file functions always take the download button to which they are related as their first argument. We can pass in additional arguments and keyword arguments by setting the Function's `args` and `kwargs` attributes.

In our 0th file creation function, we store `Hello, World!` in a data URL. We cache the result by exiting the function early if the download button has already been clicked.

```python
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
```

In our 1st file creation function, we store a random string of ascii letters in a data URL. Because we want to store a different random string each time the download button is clicked, we store the URL in the download button's `tmp_downloads` attribute.

```python
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
```