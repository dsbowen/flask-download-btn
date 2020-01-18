"""Download button mixin

This file defines a download button Mixin, as well as helper `Function` models
for handling forms and creating files.

The download button is responsible for:
1. Rendering a download button, progress bar, and script
2. Download process:
    2.1 Web form handling
    2.2 File creation
"""

from flask import Markup, current_app, render_template, session
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, inspect
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm import relationship
from sqlalchemy_function import FunctionMixin as FunctionMixinBase, FunctionRelator
from sqlalchemy_modelid import ModelIdBase
from sqlalchemy_mutable import MutableListType, MutableDictType
from sqlalchemy_mutablesoup import MutableSoupType

from copy import copy
from datetime import datetime
from random import choice
import itertools
import json
import os
import string


class DownloadBtnMixin(FunctionRelator, ModelIdBase):
    """Download button mixin"""

    """Columns and relationships"""
    btn = Column(MutableSoupType)
    progress = Column(MutableSoupType)
    cache = Column(String, default='no-store')
    form_id = Column(String)
    downloads = Column(MutableListType)
    download_msg = Column(Text)
    downloaded = Column(Boolean, default=False)
    callback = Column(Text)

    @declared_attr
    def handle_form_functions(self):
        return relationship(
            'HandleForm',
            backref='btn',
            order_by='HandleForm.index',
            collection_class=ordering_list('index')
        )
    
    @declared_attr
    def create_file_functions(self):
        return relationship(
            'CreateFile',
            backref='btn',
            order_by='CreateFile.index',
            collection_class=ordering_list('index')
        )

    """Identities"""
    @property
    def _id(self):
        ids = inspect(self).identity
        return '-'.join([str(id) for id in ids]) if ids else None

    @property
    def script_id(self):
        """HTML id for button script"""
        return self.model_id+'-script'

    @property
    def btn_id(self):
        """HTML id for the button <div> tag"""
        return self.model_id+'-btn'

    @property
    def progress_id(self):
        """HTML id for the progress bar container""" 
        return self.model_id+'-progress'

    @property
    def progress_bar_id(self):
        """HTML id for the progress bar"""
        return self.model_id+'-progress-bar'
    
    @property
    def progress_txt_id(self):
        """HTML id for the progress bar text"""
        return self.model_id+'-progress-txt'

    @property
    def a_id(self):
        """HTML id for the <a> download tag"""
        return self.model_id+'-a'

    """HTML properties"""
    @property
    def btn_tag(self):
        return self.btn.select_one('#'+self.btn_id)
    
    @property
    def progress_bar_tag(self):
        return self.progress.select_one('#'+self.progress_bar_id)

    @property
    def _csrf_key(self):
        """Key for the CSRF token"""
        return self.model_id+'csrf'

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
        """
        clean_downloads = []
        tmp_downloads = []
        if hasattr(self, 'tmp_downloads') and self.tmp_downloads:
            tmp_downloads = self.tmp_downloads
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

    def __init__(self, *args, **kwargs):
        """Constructor"""
        manager = current_app.extensions['download_btn_manager']
        manager.db.session.add(self)
        manager.db.session.flush([self])
        self.btn = render_template(
            'download_btn/button.html', btn=self
        )
        self.progress = render_template(
            'download_btn/progress.html', btn=self
        )
        self.downloads = []
        super().__init__(*args, **kwargs)

    """Modify button text"""
    @property
    def btn_text(self):
        return self.btn_tag.text

    @btn_text.setter
    def btn_text(self, val):
        self.btn.set_element('button', val)

    """Render download button, progress bar, and script"""
    def render_btn(self):
        """Render the download button"""
        return self.btn.render()

    def render_progress(self):
        """Render the progress bar
        
        The progress bar is rendered inside a container. The contents of the 
        container may be updated with progress reports during file creation.
        """
        container = '<div id="{0}" style="display: none;">{1}</div>'
        return Markup(container.format(self.progress_id, str(self.progress)))

    def script(self):
        """Render the download button script
        
        The script will call routes for form handling, file creation, and 
        download. Authentication for these routes requires a CSRF token. 
        This method creates a unique token and stores it in the session.
        """
        chars = string.ascii_letters + string.digits
        csrf_token = ''.join([choice(chars) for i in range(90)])
        session[self._csrf_key] = csrf_token
        btn_kwargs = {
            'id': self._id,
            'btn_cls': type(self).__name__,
            'csrf_token': csrf_token
        }
        return Markup(render_template(
            'download_btn/script.html', btn=self, btn_kwargs=btn_kwargs
        ))

    def clear_csrf(self):
        """Clear CSRF token from session"""
        session.pop(self._csrf_key, None)
    
    def reset(self, stage=None, pct_complete=None):
        """Reset the progress bar

        This method resets the progress bar by replacing its HTML. You will 
        typically want to reset the progress bar at the start of a new stage.
        """
        text = self._get_progress_text(stage, pct_complete)
        self.progress.select_one('#'+self.progress_txt_id).string = text
        pct_complete = str((pct_complete or 0)) + '%'
        self.progress.select_one('#'+self.progress_bar_id)['width'] = pct_complete
        data = json.dumps({'html': str(self.progress)})
        return 'event: reset\ndata: {}\n\n'.format(data)

    def report(self, stage=None, pct_complete=None):
        """Send a progress report
        
        This method reports file creation progress with a server sent event. 
        The download button script will update the progress bar accordingly.
        """
        text = self._get_progress_text(stage, pct_complete)
        data = json.dumps({'text': text, 'pct_complete': pct_complete})
        return 'event: progress_report\ndata: {}\n\n'.format(data)

    def _get_progress_text(self, stage=None, pct_complete=None):
        """Get progress bar text"""
        if pct_complete is None:
            pct_complete, pct_complete_txt = 0, ''
            stage = stage or ''
        else:
            pct_complete_txt = '{:.0f}%'.format(pct_complete)
            stage = stage+': ' if stage is not None else ''
        return stage + pct_complete_txt
    
    def transition_speed(self, speed):
        data = json.dumps({'speed': speed})
        return 'event: transition_speed\ndata: {}\n\n'.format(data)

    """2. Download process"""
    """2.1 Web form handling"""
    def _handle_form(self, response):
        """Execute handle form functions with form response."""
        [
            f.func(f.parent, response, *f.args, **f.kwargs) 
            for f in self.handle_form_functions
        ]
    
    """2.2 File creation"""
    def _create_files(self, app):
        """Create files for download

        This method executes the CreateFiles functions before sending a 
        'download_ready' message.

        Progress reports are yielded as server sent events.
        """
        with app.app_context():
            db = app.extensions['download_btn_manager'].db
            db.session.add(self)
            sse_prev = sse_curr = datetime.now()
            for f in self.create_file_functions:
                for exp in f():
                    yield exp
                    sse_prev, sse_curr = sse_curr, datetime.now()
                    yield self._update_transition_speed(sse_prev, sse_curr)
            download_ready_event = self._download_ready()
        yield download_ready_event

    def _update_transition_speed(self, sse_prev, sse_curr):
        """Update transition speed of progress bar
        
        Note that transition speeds of <.02 will not render properly. 
        Therefore, set the transition speed to 0 if the speed would 
        otherwise be <.02.
        """
        speed = (sse_curr - sse_prev).total_seconds()
        speed = min(speed, .5)
        speed = 0 if speed < .02 else speed
        return self.transition_speed(str(speed)+'s')

    def _download_ready(self):
        """Send a download ready message"""
        pct_complete = None if self.download_msg is None else 100
        text = self._get_progress_text(self.download_msg, pct_complete)
        data = json.dumps({
            'text': text,
            'pct_complete': pct_complete,
            'downloads': self._downloads,
            'cache': self.cache,
            'callback': self.callback,
        })
        return 'event: download_ready\ndata: {}\n\n'.format(data)


class FunctionMixin(FunctionMixinBase):
    @property
    def parent(self):
        return self.btn

    @parent.setter
    def parent(self, value):
        self.btn = value


class HandleFormMixin(FunctionMixin):
    pass


class CreateFileMixin(FunctionMixin):
    pass