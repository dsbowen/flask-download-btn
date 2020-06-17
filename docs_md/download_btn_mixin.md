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
</style># Download button mixin

<table class="docutils field-list field-table" frame="void" rules="none">
    <col class="field-name" />
    <col class="field-body" />
    <tbody valign="top">
        
    </tbody>
</table>



##flask_download_btn.**DownloadBtnMixin**

<p class="func-header">
    <i>class</i> flask_download_btn.<b>DownloadBtnMixin</b>(<i>btn_template=None, progress_template=None, **kwargs</i>) <a class="src-href" target="_blank" href="https://github.com/dsbowen/flask-download-btn/flask_download_btn/download_btn_mixin.py#L20">[source]</a>
</p>

Subclass the `DownloadnBtnMixin` to create download button models.
Download buttons are responsible for:

1. Rendering a download button, progress bar, and download script.
2. Web form handling (optional).
3. File creation (optional).

<table class="docutils field-list field-table" frame="void" rules="none">
    <col class="field-name" />
    <col class="field-body" />
    <tbody valign="top">
        <tr class="field">
    <th class="field-name"><b>Parameters:</b></td>
    <td class="field-body" width="100%"><b>btn_template : <i>str or None, default=None</i></b>
<p class="attr">
    Name of the download button html template. If <code>None</code>, the download button manager's <code>btn_template</code> is used.
</p>
<b>progress_template : <i>str or None, default=None</i></b>
<p class="attr">
    Name of the progress bar html template. If <code>None</code>, the download button manager's <code>progress_template</code> is used.
</p>
<b>**kwargs : <i></i></b>
<p class="attr">
    You can set the download button's attribtues by passing them as keyword arguments.
</p></td>
</tr>
<tr class="field">
    <th class="field-name"><b>Attributes:</b></td>
    <td class="field-body" width="100%"><b>btn : <i>sqlalchemy_mutablesoup.MutableSoup</i></b>
<p class="attr">
    Download button html soup.
</p>
<b>btn_tag : <i>bs4.Tag</i></b>
<p class="attr">
    Download button tag.
</p>
<b>btn_text : <i>str, default='Download'</i></b>
<p class="attr">
    Text of the download button.
</p>
<b>cache : <i>str, default='no-store'</i></b>
<p class="attr">
    Cache response directive. See <a href="https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control">https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control</a>.
</p>
<b>callback : <i>str or None, default=None</i></b>
<p class="attr">
    Name of the callback view function. If this is not <code>None</code>, the client is redirected to the callback URL after download has completed.
</p>
<b>downloads : <i>list, default=[]</i></b>
<p class="attr">
    List of downloads. Items of this list may be URLs (str) or (URL, file_name) tuples (str, str).
</p>
<b>download_msg : <i>str, default=''</i></b>
<p class="attr">
    Message which will be briefly displayed after the download has completed.
</p>
<b>downloaded : <i>bool, default=False</i></b>
<p class="attr">
    Indicates that the file(s) associated with this button has been downloaded.
</p>
<b>form_id : <i>str or None, default=None</i></b>
<p class="attr">
    ID of the form processed by the download button. If you are not processing a form, or there is only one form on the page, leave this as <code>None</code>. If there are multiple forms on the page, set <code>form_id</code> to the ID of the form associated with the download button.
</p>
<b>progress : <i>sqlalchemy_mutbalesoup.MutableSoup</i></b>
<p class="attr">
    Progress bar html soup.
</p>
<b>progress_bar : <i>bs4.Tag</i></b>
<p class="attr">
    Progress bar tag.
</p>
<b>progress_text : <i>bs4.Tag</i></b>
<p class="attr">
    Progress bar text tag.
</p></td>
</tr>
<tr class="field">
    <th class="field-name"><b>Function attributes:</b></td>
    <td class="field-body" width="100%"><b>handle_form_functions : <i>list, default=[]</i></b>
<p class="attr">
    <code>HandleForm</code> functions are executed sequentially after the download button is clicked. These functions process the response from any form which may be associated with the download button.
</p>
<b>create_file_functions : <i>list, default=[]</i></b>
<p class="attr">
    <code>CreateFile</code> functions are executed sequentially after the <code>HandleForm</code> functions.
</p></td>
</tr>
    </tbody>
</table>



####Methods



<p class="func-header">
    <i></i> <b>get_id</b>(<i>self, sfx</i>) <a class="src-href" target="_blank" href="https://github.com/dsbowen/flask-download-btn/flask_download_btn/download_btn_mixin.py#L192">[source]</a>
</p>

Get the CSS id associated with download button attributes.

<table class="docutils field-list field-table" frame="void" rules="none">
    <col class="field-name" />
    <col class="field-body" />
    <tbody valign="top">
        <tr class="field">
    <th class="field-name"><b>Parameters:</b></td>
    <td class="field-body" width="100%"><b>sfx : <i>str</i></b>
<p class="attr">
    Suffix of the CSS id.
</p></td>
</tr>
<tr class="field">
    <th class="field-name"><b>Suffix values:</b></td>
    <td class="field-body" width="100%"><b>btn : <i>download button tag</i></b>
<p class="attr">
    
</p>
<b>csrf : <i>key for CSRF token lookup in session</i></b>
<p class="attr">
    
</p>
<b>progress : <i>progress bar <code>&lt;div&gt;</code> container</i></b>
<p class="attr">
    
</p>
<b>progress-bar : <i>progress bar tag</i></b>
<p class="attr">
    
</p>
<b>progress-txt : <i>progress bar text</i></b>
<p class="attr">
    
</p></td>
</tr>
<tr class="field">
    <th class="field-name"><b>Returns:</b></td>
    <td class="field-body" width="100%"><b>id : <i>str</i></b>
<p class="attr">
    Of the form 'self.model_id-sfx'.
</p></td>
</tr>
    </tbody>
</table>





<p class="func-header">
    <i></i> <b>render_progress</b>(<i>self</i>) <a class="src-href" target="_blank" href="https://github.com/dsbowen/flask-download-btn/flask_download_btn/download_btn_mixin.py#L221">[source]</a>
</p>

Render the progress bar inside a container which sets the
progress bar display style to none. The contents of the container
may be updated with progress reports during file creation.

<table class="docutils field-list field-table" frame="void" rules="none">
    <col class="field-name" />
    <col class="field-body" />
    <tbody valign="top">
        <tr class="field">
    <th class="field-name"><b>Returns:</b></td>
    <td class="field-body" width="100%"><b>progress : <i>flask.Markup</i></b>
<p class="attr">
    Rendered progress bar wrapped in a display none container. Insert this into a <code>&lt;body&gt;</code> tag in a Jinja template.
</p></td>
</tr>
    </tbody>
</table>





<p class="func-header">
    <i></i> <b>script</b>(<i>self</i>) <a class="src-href" target="_blank" href="https://github.com/dsbowen/flask-download-btn/flask_download_btn/download_btn_mixin.py#L238">[source]</a>
</p>

Render the download button script.

The script will call routes for form handling, file creation, and
download. Authentication for these routes requires a CSRF token.
This method creates a unique token and stores it in the session.

<table class="docutils field-list field-table" frame="void" rules="none">
    <col class="field-name" />
    <col class="field-body" />
    <tbody valign="top">
        <tr class="field">
    <th class="field-name"><b>Returns:</b></td>
    <td class="field-body" width="100%"><b>script : <i>flask.Markup</i></b>
<p class="attr">
    Rendered download button javascript. Insert this into a <code>&lt;head&gt;</code> tag in a Jinja template.
</p></td>
</tr>
    </tbody>
</table>





<p class="func-header">
    <i></i> <b>clear_csrf</b>(<i>self</i>) <a class="src-href" target="_blank" href="https://github.com/dsbowen/flask-download-btn/flask_download_btn/download_btn_mixin.py#L264">[source]</a>
</p>

Clear CSRF token from session. Call this method to revoke client permission to download the file.

<table class="docutils field-list field-table" frame="void" rules="none">
    <col class="field-name" />
    <col class="field-body" />
    <tbody valign="top">
        <tr class="field">
    <th class="field-name"><b>Returns:</b></td>
    <td class="field-body" width="100%"><b>CSRF token : <i>str or None</i></b>
<p class="attr">
    
</p></td>
</tr>
    </tbody>
</table>





<p class="func-header">
    <i></i> <b>reset</b>(<i>self, stage='', pct_complete=None</i>) <a class="src-href" target="_blank" href="https://github.com/dsbowen/flask-download-btn/flask_download_btn/download_btn_mixin.py#L274">[source]</a>
</p>

Resets the progress bar by replacing its html. You will typically
want to reset the progress bar at the start of a new stage.

<table class="docutils field-list field-table" frame="void" rules="none">
    <col class="field-name" />
    <col class="field-body" />
    <tbody valign="top">
        <tr class="field">
    <th class="field-name"><b>Parameters:</b></td>
    <td class="field-body" width="100%"><b>stage : <i>str, default=''</i></b>
<p class="attr">
    Stage of file creation. e.g. 'Compiling file 0'.
</p>
<b>pct_complete : <i>float or None, default=None</i></b>
<p class="attr">
    Percent of the stage complete. If <code>None</code>, the progress bar will display the <code>stage</code> without a percent complete message.
</p></td>
</tr>
<tr class="field">
    <th class="field-name"><b>Returns:</b></td>
    <td class="field-body" width="100%"><b>reset event : <i>str</i></b>
<p class="attr">
    Server sent event to reset the progress bar.
</p></td>
</tr>
    </tbody>
</table>





<p class="func-header">
    <i></i> <b>report</b>(<i>self, stage='', pct_complete=None</i>) <a class="src-href" target="_blank" href="https://github.com/dsbowen/flask-download-btn/flask_download_btn/download_btn_mixin.py#L300">[source]</a>
</p>

Reports file creation progress by updating the progress bar html.

<table class="docutils field-list field-table" frame="void" rules="none">
    <col class="field-name" />
    <col class="field-body" />
    <tbody valign="top">
        <tr class="field">
    <th class="field-name"><b>Parameters:</b></td>
    <td class="field-body" width="100%"><b>stage : <i>str, default=''</i></b>
<p class="attr">
    Stage of file creation. e.g. 'Compiling file 0'.
</p>
<b>pct_complete : <i>float or None, default=None</i></b>
<p class="attr">
    Percent of the stage complete. If <code>None</code>, the progress bar will display the <code>stage</code> without a percent complete message.
</p></td>
</tr>
<tr class="field">
    <th class="field-name"><b>Returns:</b></td>
    <td class="field-body" width="100%"><b>report event : <i>str</i></b>
<p class="attr">
    Server sent event to update the progress bar.
</p></td>
</tr>
    </tbody>
</table>





<p class="func-header">
    <i></i> <b>transition_speed</b>(<i>self, speed</i>) <a class="src-href" target="_blank" href="https://github.com/dsbowen/flask-download-btn/flask_download_btn/download_btn_mixin.py#L333">[source]</a>
</p>

Set the transition speed for the progress bar.

<table class="docutils field-list field-table" frame="void" rules="none">
    <col class="field-name" />
    <col class="field-body" />
    <tbody valign="top">
        <tr class="field">
    <th class="field-name"><b>Parameters:</b></td>
    <td class="field-body" width="100%"><b>speed : <i>str</i></b>
<p class="attr">
    Number of seconds for the transiton, e.g. '.5s'
</p></td>
</tr>
<tr class="field">
    <th class="field-name"><b>Returns:</b></td>
    <td class="field-body" width="100%"><b>transition speed event : <i>str</i></b>
<p class="attr">
    Server sent event to update the transition speed.
</p></td>
</tr>
    </tbody>
</table>

