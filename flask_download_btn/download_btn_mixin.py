"""Download button mixin

This file defines a download button mixin, as well as mixins for form handling functions and file creation functions.

The download button is responsible for:
1. Rendering a download button, progress bar, and script
2. Download process:
    2.1 Web form handling
    2.2 File creation
"""

from datetime import datetime
from flask import Markup, current_app, render_template, session
from random import choice
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, PickleType, inspect
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm import relationship
from sqlalchemy_function import FunctionRelator
from sqlalchemy_function import FunctionMixin as FunctionMixinBase
from sqlalchemy_mutable import MutableListType, MutableDictType
import itertools
import json
import os
import string


class DownloadBtnMixin(FunctionRelator):
    """Download button mixin"""

    """Columns and relationships"""
    btn_classes = Column(MutableListType)
    btn_style = Column(MutableDictType)
    btn_template = Column(String)
    text = Column(Text)
    progress_classes = Column(MutableListType)
    progress_style = Column(MutableDictType)
    progress_template = Column(String)
    cache = Column(String)
    form_id = Column(String)
    init_transition_speed = Column(String)
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
    def model_id(self):
        return type(self).__name__+'-'+str(self._id)

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
    def progress_text_id(self):
        """HTML id for the progress bar text"""
        return self.model_id+'-progress-text'

    @property
    def a_id(self):
        """HTML id for the <a> download tag"""
        return self.model_id+'-a'

    """HTML properties"""
    @property
    def _csrf_key(self):
        """Key for the CSRF token"""
        return self.model_id+'csrf'

    @property
    def _btn_classes(self):
        """Button <div> classes in HTML format"""
        return ' '.join(self.btn_classes)

    @property
    def _btn_style(self):
        return self._style(self.btn_style)
    
    @property
    def _text(self):
        """Button text"""
        return self.text or ''
    
    @property
    def _progress_classes(self):
        """Progress bar <div> classes in HTML format"""
        return ' '.join(self.progress_classes)

    @property
    def _progress_style(self):
        return self._style(self.progress_style)

    def _style(self, style):
        return ' '.join([key+': '+val+';' for key, val in style.items()])

    @property
    def _form(self):
        """Web form selector"""
        return 'form' if self.form_id is None else '#'+self.form_id

    @property
    def _downloads(self):
        downloads = []
        for download in self.downloads:
            if isinstance(download, tuple):
                url, filename = download
            elif isinstance(download, str):
                url, filename = download, 'download'
            else:
                raise ValueError(
                    'Download must be str (url) or tuple (url, filename)'
                )
            downloads.append({'url': url, 'filename': filename})
        return downloads

    def __init__(self, *args, **kwargs):
        """Constructor

        1. Set function relationships for form handling and file creation 
        function models.
        2. Set a blank zip file suffix dictionary
        3. Set attributes

        Manager defaults are overridden by keyword arguments.
        """
        manager = current_app.extensions['download_btn_manager']
        self.__dict__.update(manager.default_settings)
        self.__dict__.update(kwargs)
        super().__init__(*args, **kwargs)

    """Render download button, progress bar, and script"""
    def render_btn(self):
        """Render the download button"""
        return Markup(render_template(self.btn_template, btn=self))

    def render_progress(self):
        """Render the progress bar
        
        The progress bar is rendered inside a container. The contents of the 
        container may be updated with progress reports during file creation.
        """
        container = '<div id="{0}" style="display: none;">{1}</div>'
        content = render_template(
            self.progress_template, btn=self, pct_complete=0, text=''
        )
        return Markup(container.format(self.progress_id, content))

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

        `reset` executes faster than `report`. Therefore, you may also want 
        to use `reset` instead of `report` when sending rapid progress 
        updates (~10ms or faster).
        """
        text = self._get_progress_text(stage, pct_complete)
        html = render_template(
            self.progress_template, 
            btn=self, pct_complete=pct_complete, text=text
        )
        data = json.dumps({'html': html})
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
        """Update transition speed of progress bar"""
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


"""HandleForm and CreateFile Mixins"""
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