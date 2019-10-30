# Flask-Download-Btn

Flask-Download-Btn defines a [SQLALchemy Mixin](https://docs.sqlalchemy.org/en/13/orm/extensions/declarative/mixins.html) for creating [Bootstrap](https://getbootstrap.com/) download buttons in a [Flask](https://palletsprojects.com/p/flask/) application.

Its key features are:
1. *Automatic enabling and disabling*: A download button is automatically disabled on click and re-enabling on download completion.
2. *Web form handling*: Applications can modify a download button on click based on web form responses.
3. *Progress bar*: Download buttons report progress using a progress bar updated with server-sent events.

## Example: Basic use

Suppose we want to include a download button which downloads `hello_world.txt`. On click, we want to disable the button and re-enable it when the file finishes downloading.

After setup, we can achieve this with the following:

```python
@app.route('/')
def index():
    btn = DownloadBtn.query.filter_by(name='example1').first()
    if not btn:
        btn = DownloadBtn()
        btn.name = 'example1'
        btn.text = 'Download Example 1'
        btn.filenames = ['hello_world.txt']
        db.session.add(btn)
        db.session.commit()
    return render_template('index.html', download_btn=btn)
```

## Documentation

You can find the latest documentation at [https://dsbowen.github.io/flask-download-btn](https://dsbowen.github.io/flask-download-btn).

## License

Publications which use this software should include the following citation for SQLAlchemy-Function and its dependencies, [SQLAlchemy-Function](https://dsbowen.github.io/sqlalchemy-function) and [SQLAlchemy-Mutable](https://dsbowen.github.io/sqlalchemy-mutable):

Bowen, D.S. (2019). Flask-Download-Btn\[Computer software\]. [https://dsbowen.github.io/flask-download-btn](https://dsbowen.github.io/flask-download-btn).

Bowen, D.S. (2019). SQLAlchemy-Function \[Computer software\]. [https://dsbowen.github.io/sqlalchemy-function](https://dsbowen.github.io/sqlalchemy-function).

Bowen, D.S. (2019). SQLAlchemy-Mutable \[Computer software\]. [https://dsbowen.github.io/sqlalchemy-mutable](https://dsbowen.github.io/sqlalchemy-mutable).

This project is licensed under the MIT License [LICENSE](https://github.com/dsbowen/flask-download-btn/blob/master/LICENSE).