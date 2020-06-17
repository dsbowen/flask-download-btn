<script src="https://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML" type="text/javascript"></script>

<link rel="stylesheet" href="https://assets.readthedocs.org/static/css/readthedocs-doc-embed.css" type="text/css" />

<style>
    a.src-href {
        float: right;
    }
    p.attr {
        margin-top: 0.5em;
        margin-left: 1em;
    }
    p.func-header {
        background-color: gainsboro;
        border-radius: 0.1em;
        padding: 0.5em;
        padding-left: 1em;
    }
    table.field-table {
        border-radius: 0.1em
    }
</style># Download button manager

<table class="docutils field-list field-table" frame="void" rules="none">
    <col class="field-name" />
    <col class="field-body" />
    <tbody valign="top">
        
    </tbody>
</table>



##flask_download_btn.**DownloadBtnManager**

<p class="func-header">
    <i>class</i> flask_download_btn.<b>DownloadBtnManager</b>(<i>app=None, **kwargs</i>) <a class="src-href" target="_blank" href="https://github.com/dsbowen/flask-download-btn/flask_download_btn/__init__.py#L15">[source]</a>
</p>

The manager has two responsibilities:

1. Register download button classes.
2. Register routes used by the download button.

<table class="docutils field-list field-table" frame="void" rules="none">
    <col class="field-name" />
    <col class="field-body" />
    <tbody valign="top">
        <tr class="field">
    <th class="field-name"><b>Parameters:</b></td>
    <td class="field-body" width="100%"><b>app : <i>flask.app.Flask or None, default=None</i></b>
<p class="attr">
    Flask application with which download buttons are associated.
</p>
<b>**kwargs : <i></i></b>
<p class="attr">
    You can set the download button manager's attributes by passing them as keyword arguments.
</p></td>
</tr>
<tr class="field">
    <th class="field-name"><b>Attributes:</b></td>
    <td class="field-body" width="100%"><b>db : <i>flask_sqlalchemy.SQLAlchemy or None, default=None</i></b>
<p class="attr">
    SQLAlchemy database associated with the Flask app.
</p>
<b>btn_template : <i>str, default='download_btn/button.html'</i></b>
<p class="attr">
    Path to the default button template.
</p>
<b>progress_template : <i>str, default='download_btn/progress.html'</i></b>
<p class="attr">
    Path to the default progress bar template.
</p></td>
</tr>
    </tbody>
</table>

####Notes

If `app` and `db` are not set on initialization, they must be set using
the `init_app` method before the app is run.

####Examples

```python
from flask import Flask
from flask_download_btn import DownloadBtnManager
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
download_btn_manager = DownloadBtnManager(app, db)
```

####Methods



<p class="func-header">
    <i></i> <b>register</b>(<i>cls, btn_cls</i>) <a class="src-href" target="_blank" href="https://github.com/dsbowen/flask-download-btn/flask_download_btn/__init__.py#L66">[source]</a>
</p>

Decorator for updating the download button class registry.

<table class="docutils field-list field-table" frame="void" rules="none">
    <col class="field-name" />
    <col class="field-body" />
    <tbody valign="top">
        <tr class="field">
    <th class="field-name"><b>Parameters:</b></td>
    <td class="field-body" width="100%"><b>btn_cls : <i>class</i></b>
<p class="attr">
    Class of the registered button.
</p></td>
</tr>
<tr class="field">
    <th class="field-name"><b>Returns:</b></td>
    <td class="field-body" width="100%"><b>btn_cls : <i></i></b>
<p class="attr">
    
</p></td>
</tr>
    </tbody>
</table>

####Examples

```python
from flask_download_btn import DownloadBtnMixin

@DownloadBtnManager.register
class DownloadBtn(DownloadBtnMixin, db.Model):
    ...
```



<p class="func-header">
    <i></i> <b>init_app</b>(<i>self, app, **kwargs</i>) <a class="src-href" target="_blank" href="https://github.com/dsbowen/flask-download-btn/flask_download_btn/__init__.py#L100">[source]</a>
</p>

Initialize the download button manager with the application.

<table class="docutils field-list field-table" frame="void" rules="none">
    <col class="field-name" />
    <col class="field-body" />
    <tbody valign="top">
        <tr class="field">
    <th class="field-name"><b>Parameters:</b></td>
    <td class="field-body" width="100%"><b>app : <i>flask.app.Flask</i></b>
<p class="attr">
    Application with which the download button manager is associated.
</p>
<b>**kwargs : <i></i></b>
<p class="attr">
    You can set the download button manager's attributes by passing them as keyword arguments.
</p></td>
</tr>
    </tbody>
</table>

