"""Download button mixin

This file defines a download button mixin, as well as mixins for form handling functions and file creation functions.

The download button is responsible for:
1. Rendering a download button, progress bar, and script
2. Cache and session management
3. Handling the download process on click:
    3.1 Web form handling
    3.2 File creation
    3.3 Download
"""

from datetime import datetime
from flask import Markup, current_app, render_template, send_file, session
from random import choice
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, PickleType, inspect
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm import relationship
from sqlalchemy_function import FunctionBase
from sqlalchemy_function import FunctionMixin as FunctionMixinBase
from sqlalchemy_mutable import MutableListType, MutableDictType
import itertools
import json
import os
import string
import zipfile


class DownloadBtnMixin(FunctionBase):
    """Download button mixin"""

    """Columns and relationships"""
    _zipf_sfxs = Column(MutableListType)
    btn_classes = Column(MutableListType)
    btn_style = Column(MutableDictType)
    btn_template = Column(String)
    text = Column(Text)
    progress_classes = Column(MutableListType)
    progress_style = Column(MutableDictType)
    progress_template = Column(String)
    use_cache = Column(Boolean)
    form_id = Column(String)
    init_transition_speed = Column(String)
    filenames = Column(MutableListType)
    attachment_filename = Column(String)
    download_msg = Column(Text)

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
        id = inspect(self).identity
        return id[0] if id else None

    @property
    def model_id(self):
        return type(self).__name__+'-'+str(self._id)

    @property
    def btn_id(self):
        """Html id for the button <div> tag"""
        return self.model_id+'-btn'

    @property
    def progress_id(self):
        """Html id for the progress bar container""" 
        return self.model_id+'-progress'

    @property
    def progress_bar_id(self):
        """Html id for the progress bar"""
        return self.model_id+'-progress-bar'
    
    @property
    def progress_text_id(self):
        """Html id for the progress bar text"""
        return self.model_id+'-progress-text'
    
    """Session keys"""
    @property
    def _csrf_key(self):
        """Key for the CSRF token"""
        return self.model_id+'csrf'

    @property
    def _response_cached_key(self):
        """Key for response caching"""
        return self.model_id+'cache'

    @property
    def _zipf_name_key(self):
        """Key for zip file name"""
        return self.model_id+'zipf-name'

    @property
    def _zipf_sfx_key(self):
        """Key for zip file suffix"""
        return self.model_id+'zipf-sfx'
    
    @property
    def _filename_key(self):
        """Key for download file name"""
        return self.model_id+'filename'

    @property
    def _attachment_filename_key(self):
        """Key for attachment file name"""
        return self.model_id+'attachment_filename'

    """Html properties"""
    @property
    def _btn_classes(self):
        """Button <div> classes in html format"""
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
        """Progress bar <div> classes in html format"""
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

    def __init__(self, **kwargs):
        """Constructor

        1. Set function relationships for form handling and file creation 
        function models.
        2. Set a blank zip file suffix dictionary
        3. Set attributes

        Manager defaults are overridden by keyword arguments.
        """
        self._set_function_relationships()
        self._zipf_sfxs = []
        manager = current_app.extensions['download_btn_manager']
        self.__dict__.update(manager.default_settings)
        self.__dict__.update(kwargs)

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
    
    def reset(self, stage=None, pct_complete=None):
        """Reset the progress bar

        This method resets the progress bar by replacing its html. You will 
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

    """2. Cache and session management"""
    def cached(self):
        """Indicate the response is cached"""
        return (
            self.use_cache and self._response_cached_key in session
            and session[self._response_cached_key]
        )
    
    def clear_session(self):
        """Clear session and delete associated zip file"""
        name = session[self._zipf_name_key]
        sfx = session[self._zipf_sfx_key]
        try:
            os.remove('tmp/'+name)
        except:
            pass
        self._zipf_sfxs[sfx] = False
        session.pop(self._zipf_name_key, None)
        session.pop(self._zipf_sfx_key, None)

    def clear_csrf(self):
        """Clear CSRF token from session"""
        session.pop(self._csrf_key, None)

    """3. Web form handling"""
    """3.1 Web form handling"""
    def _handle_form(self, response):
        """Execute handle form functions with form response."""
        [
            f.func(f.parent, response, *f.args, **f.kwargs) 
            for f in self.handle_form_functions
        ]
    
    """3.2 File creation"""
    def _gen_zipf_name(self):
        """Generate a unique zip file name for the session
        
        This method generates a unique zip file name for the session. The 
        zip file name will be used to store zipped files. It will not be 
        necessary to zip files if the download button specifies only one 
        downloaded file.
        """
        sfx = self._gen_zipf_sfx()
        name = '{0}-{1}.zip'.format(self.model_id, sfx)
        session[self._zipf_name_key] = name
        session[self._zipf_sfx_key] = sfx
        return name

    def _gen_zipf_sfx(self):
        """Generate a unique zipfile suffix for the session
        
        Iterate through the zipfile suffixes until an inactive suffix is 
        found. Use this suffix for the zipfile name and mark it as active.

        If all suffixes in the zipfile suffix list are active, extend the 
        list.
        """
        for i, active in enumerate(self._zipf_sfxs):
            if not active:
                self._zipf_sfxs[i] = True
                return i
        self._zipf_sfxs.append(True)
        return len(self._zipf_sfxs) - 1

    def _create_files(self, app, zipf_name):
        """Create files for download

        This method performs three tasks:
        1. Execute the CreateFiles functions
        2. Zip files if necessary
        3. Send a 'download_ready' message

        Progress reports are yielded as server sent events.
        """
        app.app_context().push()
        db = app.extensions['download_btn_manager'].db
        db.session.add(self)
        gen = itertools.chain(
            *[f() for f in self.create_file_functions],
            self._zip_files(zipf_name), 
            self._download_ready()
        )
        sse_prev = sse_curr = datetime.now()
        for exp in gen:
            sse_prev, sse_curr = sse_curr, datetime.now()
            delta = (sse_curr - sse_prev).total_seconds()
            delta = min(delta, .5)
            delta = 0 if delta < .02 else delta
            yield self.transition_speed(str(delta)+'s')
            yield exp

    def _zip_files(self, zipf_name):
        """Zip files"""
        num_files = len(self.filenames)
        if num_files <= 1:
            return
        stage = 'Zipping Files'
        yield self.reset(stage, 0)
        zipf = zipfile.ZipFile('tmp/'+zipf_name, 'w', zipfile.ZIP_DEFLATED)
        for i, filename in enumerate(self.filenames):
            yield self.report(stage, 100.0*i/num_files)
            zipf.write(filename)
        yield self.report(stage, 100)
        zipf.close()

    def _download_ready(self):
        """Send a download ready message"""
        text = self._get_progress_text(self.download_msg)
        data = json.dumps({'text': text, 'pct_complete': 100})
        yield 'event: download_ready\ndata: {}\n\n'.format(data)

    """3.3 Download"""
    def _download(self):
        """Download file
        
        Download depends on the number of files to be downloaded:
        0: Return empty response
        1: Return the file as an attachment
        2+: Return the zip archive
        """
        num_files = len(self.filenames)
        if num_files == 0:
            return ('', 204)
        zipf_path = 'tmp/'+session[self._zipf_name_key]
        filename = self.filenames[0] if num_files == 1 else zipf_path
        if num_files == 1:
            attachment_filename = self.attachment_filename or filename
        else:
            attachment_filename = self.attachment_filename or 'download.zip'
        session[self._filename_key] = filename
        session[self._attachment_filename_key] = attachment_filename
        return self._get_response()

    def _get_response(self):
        """Get server response (i.e. attachment)"""
        filename = session[self._filename_key]
        if not filename.startswith('/'):
            filename = os.path.join(os.getcwd(), filename)
        attachment_filename = session[self._attachment_filename_key]
        response = send_file(
            filename, as_attachment=True, 
            attachment_filename=attachment_filename
        )
        self._handle_cache(response)
        return response
    
    def _handle_cache(self, response):
        """Handle caching"""
        if not self.use_cache:
            response.headers['use_cache-Control'] = (
                'no-use_cache, no-store, must-revalidate'
            )
            response.headers['Pragma'] = 'no-use_cache'
            response.headers['Expires'] = '0'
            self.clear_session()
        else:
            session[self._response_cached_key] = True


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