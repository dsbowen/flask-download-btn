"""# Download button mixin"""

from flask import current_app, render_template, session
from sqlalchemy import Boolean, Column, Integer, String, Text, inspect
from sqlalchemy_modelid import ModelIdBase
from sqlalchemy_mutable import MutableListType
from sqlalchemy_mutable import HTMLAttrsType

from datetime import datetime
from random import choice
import json

import string


class DownloadBtnMixin(ModelIdBase):
    """
    Subclass the `DownloadnBtnMixin` to create download button models. 
    Download buttons are responsible for:

    1. Rendering a download button, progress bar, and download script.
    2. Web form handling (optional).
    3. File creation (optional).

    Parameters and attributes
    -------------------------
    btn_template : str or None, default=None
        Name of the download button html template. If `None`, the download 
        button manager's `btn_template` is used.

    btn_attrs : dict
        Button html attributes.

    progress_template : str or None, default=None
        Name of the progress bar html template. If `None`, the download button
        manager's `progress_template` is used.

    progress_attrs : dict
        Progress container html attributes.

    progress_bar_attrs : dict
        Progress bar html attributes.

    progress_text_attrs : dict
        Progress bar text container html attributes.

    handle_form_functions : list, default=[]
        Functions executed sequentially after the download button is clicked. 
        These functions process the response from any form which may be 
        associated with the download button.

    create_file_functions : list, default=[]
        Functions executed sequentially after the `handle_form_functions`. 
        These are typically used to create temporary download files.

    cache : str, default='no-store'
        Cache response directive. See <https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control>.

    callback : str or None, default=None
        Name of the callback view function. If this is not `None`, the client 
        is redirected to the callback URL after download has completed.

    downloads : list, default=[]
        List of downloads. Items of this list may be URLs (str) or 
        (URL, file_name) tuples (str, str).

    download_msg : str, default=''
        Message which will be briefly displayed after the download has 
        completed.

    form_id : str or None, default=None
        ID of the form processed by the download button. If you are not 
        processing a form, or there is only one form on the page, leave this 
        as `None`. If there are multiple forms on the page, set `form_id` to 
        the ID of the form associated with the download button.

    Additional attributes
    ---------------------
    progress_text : str, default=''
        Progress bar text.

    downloaded : bool, default=False
        Indicates that the file(s) associated with this button has been 
        downloaded.
    """
    btn_template = Column(String)
    btn_attrs = Column(HTMLAttrsType)
    btn_text = Column(String)

    progress_template = Column(String)
    progress_attrs = Column(HTMLAttrsType)
    progress_bar_attrs = Column(HTMLAttrsType)
    progress_text = Column(String, default='')
    progress_text_attrs = Column(HTMLAttrsType)

    handle_form_functions = Column(MutableListType)
    create_file_functions = Column(MutableListType)

    cache = Column(String)
    callback = Column(String)
    downloads = Column(MutableListType)
    download_msg = Column(Text)
    downloaded = Column(Boolean, default=False)
    form_id = Column(String)

    @property
    def _form(self):
        """Web form selector"""
        return 'form' if self.form_id is None else '#'+self.form_id

    @property
    def _downloads(self):
        """Return a `clean_downloads` list of (url, filename) tuples

        `clean_downloads` is derived from the `downloads` and 
        `tmp_downloads` attributes. `tmp_downloads` is cleared on database 
        commit, and should be used for serving temporary files through data 
        urls.

        Note: tmp_downloads is not a column because it may be very large.
        """
        def get_tmp_downloads():
            if not hasattr(self, 'tmp_downloads') or not self.tmp_downloads:
                return []
            if isinstance(self.tmp_downloads, list):
                return self.tmp_downloads
            return [self.tmp_downloads]

        clean_downloads = []
        tmp_downloads = get_tmp_downloads()
        for download in self.downloads + tmp_downloads:
            if isinstance(download, tuple):
                url, filename = download
            elif isinstance(download, str):
                url, filename = download, 'download'
            else:
                raise ValueError(
                    'Download must be str (url) or tuple (url, filename)'
                )
            clean_downloads.append({'url': url, 'filename': filename})
        return clean_downloads

    def __init__(
            self, 
            btn_template=None, 
            btn_attrs={
                'class': ['btn', 'btn-primary', 'w-100'], 
                'type': 'button'
            },
            btn_text='Download',
            progress_template=None,
            progress_attrs={
                'class': ['progress', 'position-relative'],
                'style': {
                    'height': '25px',
                    'background-color': 'rgb(200,200,200)',
                    'margin-top': '10px',
                    'margin-bottom': '10px',
                    'box-shadow': '0 1px 2px rbga(0,0,0,0.25) inset'
                }
            },
            progress_bar_attrs={
                'class': ['progress-bar'],
                'role': 'progress-bar',
                'width': '0%',
                'style': {'transition': 'width .5s'}
            },
            progress_text_attrs={
                'class': [
                    'justify-content-center', 
                    'd-flex', 
                    'position-absolute', 
                    'w-100', 
                    'align-items-center'
                ]
            },
            cache='no-store',
            callback=None,
            handle_form_functions=[],
            create_file_functions=[],
            downloads=[],
            download_msg='',
            form_id=None,
            **kwargs
        ):
        manager = current_app.extensions['download_btn_manager']
        self.btn_template = btn_template or manager.btn_template
        self.btn_attrs = btn_attrs
        self.btn_text = btn_text
        self.progress_template = (
            progress_template or manager.progress_template
        )
        self.progress_attrs = progress_attrs
        self.progress_bar_attrs = progress_bar_attrs
        self.progress_text_attrs = progress_text_attrs
        self.cache = cache
        self.callback = callback
        self.handle_form_functions = handle_form_functions
        self.create_file_functions = create_file_functions
        self.downloads = downloads
        self.tmp_downloads = []
        self.download_msg = download_msg
        self.form_id = form_id
        super().__init__(**kwargs)

    def get_id(self, sfx):
        """
        Get the CSS id associated with download button attributes.

        Parameters
        ----------
        sfx : str
            Suffix of the CSS id.

        Suffix values
        -------------
        btn : download button tag

        csrf : key for CSRF token lookup in session

        progress : progress bar `<div>` container

        progress-bar : progress bar tag

        progress-txt : progress bar text

        script : javascript

        Returns
        -------
        id : str
            Of the form 'self.model_id-sfx'.
        """
        return self.model_id + '-' + sfx

    # 1. Render a download button, progress bar, and download button script
    def render_btn(self):
        return render_template(self.btn_template, btn=self)

    def render_progress(self):
        """
        Render the progress bar inside a container which sets the 
        progress bar display style to none. The contents of the container 
        may be updated with progress reports during file creation.

        Returns
        -------
        progress : flask.Markup
            Rendered progress bar wrapped in a display none container. 
            Insert this into a `<body>` tag in a Jinja template.
        """
        return '<div id="{0}" style="display: none;">{1}</div>'.format(
            self.get_id('progress'), 
            render_template(self.progress_template, btn=self)
        )

    def render_script(self):
        """
        Render the download button script.
        
        The script will call routes for form handling, file creation, and 
        download. Authentication for these routes requires a CSRF token. 
        This method creates a unique token and stores it in the session.

        Returns
        -------
        script : flask.Markup
            Rendered download button javascript. Insert this into a 
            `<head>` tag in a Jinja template.
        """
        chars = string.ascii_letters + string.digits
        csrf_token = ''.join([choice(chars) for i in range(90)])
        session[self.get_id('csrf')] = csrf_token
        btn_kwargs = {
            'id': inspect(self).identity[0],
            'btn_cls': type(self).__name__,
            'csrf_token': csrf_token
        }
        return render_template(
            'download_btn/script.html', btn=self, btn_kwargs=btn_kwargs
        )

    def clear_csrf(self):
        """
        Clear CSRF token from session. Call this method to revoke client permission to download the file.
        
        Returns
        -------
        CSRF token : str or None
        """
        return session.pop(self.get_id('csrf'), None)
    
    def reset(self, stage='', pct_complete=None):
        """
        Resets the progress bar by replacing its html. You will typically 
        want to reset the progress bar at the start of a new stage.

        Parameters
        ----------
        stage : str, default=''
            Stage of file creation. e.g. 'Compiling file 0'.

        pct_complete : float or None, default=None
            Percent of the stage complete. If `None`, the progress bar 
            will display the `stage` without a percent complete message.

        Returns
        -------
        reset event : str
            Server sent event to reset the progress bar.
        """
        text = self._get_progress_text(stage, pct_complete)
        self.progress_text = text
        pct_complete = str((pct_complete or 0)) + '%'
        self.progress_bar_attrs['width'] = pct_complete
        html = render_template(self.progress_template, btn=self)
        data = json.dumps({'html': html})
        return 'event: reset\ndata: {}\n\n'.format(data)

    def report(self, stage='', pct_complete=None):
        """
        Reports file creation progress by updating the progress bar html.

        Parameters
        ----------
        stage : str, default=''
            Stage of file creation. e.g. 'Compiling file 0'.

        pct_complete : float or None, default=None
            Percent of the stage complete. If `None`, the progress bar 
            will display the `stage` without a percent complete message.

        Returns
        -------
        report event : str
            Server sent event to update the progress bar.
        """
        text = self._get_progress_text(stage, pct_complete)
        data = json.dumps({'text': text, 'pct_complete': pct_complete})
        return 'event: progress_report\ndata: {}\n\n'.format(data)

    def _get_progress_text(self, stage='', pct_complete=None):
        """
        Get progress bar text.
        
        Format is 'stage: pct_complete_txt'.
        """
        pct_complete_txt = (
            '' if pct_complete is None else '{:.0f}%'.format(pct_complete)
        )
        return (stage+': ' if stage else '') + pct_complete_txt
    
    def transition_speed(self, speed):
        """
        Set the transition speed for the progress bar.

        Parameters
        ----------
        speed : str
            Number of seconds for the transiton, e.g. '.5s'

        Returns
        -------
        transition speed event : str
            Server sent event to update the transition speed.
        """
        data = json.dumps({'speed': speed})
        return 'event: transition_speed\ndata: {}\n\n'.format(data)

    # 2. Web form handling
    def _handle_form(self, response):
        """Execute handle form functions with form response."""
        [func(response, self) for func in self.handle_form_functions]
    
    # 3. File creation
    def _create_files(self, app):
        """Create files for download

        This method executes the CreateFiles functions before sending a 
        'download_ready' message.

        Progress reports are yielded as server sent events.
        """
        def update_transition_speed():
            """Update transition speed of progress bar
        
            Note that transition speeds of <.02 will not render properly. 
            Therefore, set the transition speed to 0 if the speed would 
            otherwise be <.02.
            """
            speed = (sse_curr - sse_prev).total_seconds()
            speed = min(speed, .5)
            speed = 0 if speed < .02 else speed
            return self.transition_speed(str(speed)+'s')

        def download_ready():
            # send a download ready message
            pct_complete = None if not self.download_msg else 100
            text = self._get_progress_text(self.download_msg, pct_complete)
            data = json.dumps({
                'text': text,
                'pct_complete': pct_complete,
                'downloads': self._downloads,
                'cache': self.cache,
                'callback': self.callback,
            })
            return 'event: download_ready\ndata: {}\n\n'.format(data)

        with app.app_context():
            app.extensions['download_btn_manager'].db.session.add(self)
            sse_prev = sse_curr = datetime.now()
            for func in self.create_file_functions:
                for exp in func(self):
                    yield exp
                    sse_prev, sse_curr = sse_curr, datetime.now()
                    yield update_transition_speed()
            download_ready_event = download_ready()
        # need to exit the app context before the last yield
        # otherwise you get hanging connection to database
        yield download_ready_event