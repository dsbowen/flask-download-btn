# Putting it all together

In this final example, we use both handle form and create file functions and add some style to our download button and progress bar.

Create a `style.html` Jinja template. Our folder structure looks like:

```
templates/
    form-handling.html
    index.html
    style.html
app.py
```

The template looks like:

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
    <div class="container h-100">
    <div class="row h-100 justify-content-center align-items-center">
        <form>
            {{ download_btn.render_progress() }}
            <div id="selectFiles" name="selectFiles">
                <p>Select files to download.</p>
                <div class="custom-control custom-checkbox">
                    <input id="helloWorld" name="selectFiles" type="checkbox" class="custom-control-input" value="hello_world.txt">
                    <label class="custom-control-label" for="helloWorld">Hello World</label>
                </div>
                <div class="custom-control custom-checkbox">
                    <input id="ascii" name="selectFiles" type="checkbox" class="custom-control-input" value="ascii.txt">
                    <label class="custom-control-label" for="ascii">Random ascii</label>
                </div>
            </div>
            <br>
            {{ download_btn.btn.render() }}
        </form>
    </div>
    </div>
    </body>
</html>
```

In `app.py`:

```python
@app.route('/style')
def style():
    btn = DownloadBtn()
    btn.btn_text = 'Custom Button Text'
    btn.btn_tag['class'].remove('btn-primary')
    btn.btn_tag['class'].append('btn-outline-primary')
    btn.progress_bar['class'] += [
        'progress-bar-striped', 'progress-bar-animated'
    ]
    btn.handle_form_functions = select_tmp_files
    btn.download_msg = 'Download Complete'
    db.session.commit()
    return render_template('style.html', download_btn=btn)

def select_tmp_files(response, btn):
    btn.downloads.clear()
    btn.create_file_functions.clear()
    files = response.getlist('selectFiles')
    if 'hello_world.txt' in files:
        btn.downloads = [(HELLO_WORLD_URL, 'hello_world.txt')]
    if 'ascii.txt' in files:
        btn.create_file_functions = [
            Function(create_file1, choices(string.ascii_letters, k=200))
        ]
```