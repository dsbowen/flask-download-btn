# Form handling

We often want our download button to be responsive to web forms. In this example, we will create a web form which allows clients to select which files they want to download.

## Template

We begin by creating a Jinja template called `form-handling.html` in the `templates` folder. Our folder structure looks like:

```
templates/
    form-handling.html
    index.html
app.py
```

In `form-handling.html`:

```html
<html>
    <head>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css">
        <script src="https://code.jquery.com/jquery-3.4.1.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js"></script>
        <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js"></script>
        {{ download_btn.script() }}
    </head>
    <body>
        <form>
            <div id="selectFiles" name="selectFiles">
                <p>Select files to download.</p>
                <div class="form-check">
                    <input id="helloWorld" name="selectFiles" type="checkbox" class="form-check-input" value="hello_world.txt">
                    <label class="form-check-label" for="helloWorld">Hello World</label>
                </div>
                <div class="form-check">
                    <input id="helloMoon" name="selectFiles" type="checkbox" class="form-check-input" value="hello_moon.txt">
                    <label class="form-check-label" for="helloMoon">Hello Moon</label>
                </div>
            </div>
        </form>
        {{ download_btn.btn.render() }}
        {{ download_btn.render_progress() }}
    </body>
</html>
```

## Function model

Forms are handled by [Function models](https://dsbowen.github.io/sqlalchemy-function). To begin, we define a `Function` model and give `DownloadBtn` a relationship to it named `handle_form_functions`.

```python
@DownloadBtnManager.register
class DownloadBtn(DownloadBtnMixin, db.Model):
    ...
    handle_form_functions = db.relationship(
        'Function',
        order_by='Function.index',
        collection_class=ordering_list('index'),
        foreign_keys='Function.handle_form_id'
    )

from sqlalchemy_function import FunctionMixin

class Function(FunctionMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    index = db.Column(db.Integer)
    handle_form_id = db.Column(db.Integer, db.ForeignKey('download_btn.id'))
```

## View function

Form handling Functions always take the client's form response as their first argument, and the Download Button to which they are related as their second argument. The response is a `werkzeug.datastructures.ImmutableMultiDict` object.

We can pass in additional arguments and keyword arguments by setting the Function's `args` and `kwargs` attributes.

```python
@app.route('/form-handling')
def form_handling():
    btn = DownloadBtn()
    btn.handle_form_functions = select_files
    db.session.commit()
    return render_template('form-handling.html', download_btn=btn)

def select_files(response, btn):
    btn.downloads.clear()
    files = response.getlist('selectFiles')
    if 'hello_world.txt' in files:
        btn.downloads.append((HELLO_WORLD_URL, 'hello_world.txt'))
    if 'hello_moon.txt' in files:
        btn.downloads.append((HELLO_MOON_URL, 'hello_moon.txt'))
```