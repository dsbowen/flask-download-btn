"""Download button mixin

On click, a download button performs three functions:
1. Web form handling
2. File creation
3. Download
"""

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
    btn_template = Column(String)
    text = Column(Text)
    progress_classes = Column(MutableListType)
    progress_template = Column(String)
    use_cache = Column(Boolean)
    form_id = Column(String)
    attachment_filename = Column(String)
    filenames = Column(MutableListType)
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
        """Html id for the progress bar <div> tag""" 
        return self.model_id+'-progress'
    
    """Session keys"""
    @property
    def _csrf_key(self):
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
    def _text(self):
        """Button text"""
        return self.text or ''
    
    @property
    def _progress_classes(self):
        """Progress bar <div> classes in html format"""
        return ' '.join(self.progress_classes)

    @property
    def _form(self):
        """Web form selector"""
        return 'form' if self.form_id is None else '#'+self.form_id

    def __init__(
            self, btn_classes=None, btn_template=None, text=None, 
            progress_classes=None, progress_template=None, use_cache=None, 
            form_id=None, handle_form_functions=[], create_file_functions=[],
            attachment_filename=None, filenames=[], download_msg=None
        ):
        self._set_function_relationships()
        self._zipf_sfxs = []
        self.btn_classes = btn_classes
        self.btn_template = btn_template
        self.text = text
        self.progress_classes = progress_classes
        self.progress_template = progress_template
        self.use_cache = use_cache
        self.form_id = form_id
        self.handle_form_functions = handle_form_functions
        self.create_file_functions = create_file_functions
        self.attachment_filename = attachment_filename
        self.filenames = filenames
        self.download_msg = download_msg
        self._default_settings()

    def _default_settings(self):
        """Default settings
        
        Use download button manager default settings unless otherwise specified.
        """
        manager = current_app.extensions['download_btn_manager']
        self.btn_classes = self.btn_classes or manager.btn_classes
        self.btn_template = self.btn_template or manager.btn_template
        self.progress_classes = (
            self.progress_classes or manager.progress_classes
        )
        self.progress_template = (
            self.progress_template or manager.progress_template
        )
        self.use_cache = (
            self.use_cache if self.use_cache is not None else manager.use_cache
        )

    """Methods for response caching and html rendering"""
    def cached(self):
        """Indicate the response is cached"""
        return (
            self.use_cache and self._response_cached_key in session
            and session[self._response_cached_key]
        )

    def render_btn(self):
        """Render the button <div> tag"""
        return Markup(render_template(self.btn_template, btn=self))

    def render_progress(self):
        """Render the progress bar container
        
        This will be updated with server sent progress reports from make_files.
        """
        return Markup('<div id="{}"></div>'.format(self.progress_id))

    def script(self):
        """Render the download button script"""
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

    def report(self, stage=None, pct_complete=None):
        """Send a progress report
        
        This method returns a server sent event. The data are an updated progress bar. The download button script updates the progress bar when it receives this message.
        """
        stage = '' if stage is None else stage+': '
        if pct_complete is None:
            pct_complete, pct_complete_txt = 0, ''
        else:
            pct_complete_txt = '{:.0f}%'.format(pct_complete)
        text = stage + pct_complete_txt
        data = render_template(
            self.progress_template, 
            btn=self, pct_complete=pct_complete, text=text
        )
        json_data = json.dumps({'html': data})
        return 'event: progress_report\ndata: {}\n\n'.format(json_data)

    """Web form handling"""
    def _handle_form(self, response):
        """Execute handle form functions with form response"""
        [
            f.func(f.parent, response, *f.args, **f.kwargs) 
            for f in self.handle_form_functions
        ]
    
    """File creation"""
    def _gen_zipf_name(self):
        """Generate a unique zip file name for the session
        
        This method generates a unique zip file name for the session. The zip file name will be used to store zipped files. It will not be necessary to zip files if the download button specifies only one downloaded file.
        """
        sfx = self._gen_zipf_sfx()
        name = '{0}-{1}.zip'.format(self.model_id, sfx)
        session[self._zipf_name_key] = name
        session[self._zipf_sfx_key] = sfx
        return name

    def _gen_zipf_sfx(self):
        """Generate a unique zipfile suffix for the session
        
        Iterate through the zipfile suffixes until an inactive suffix is found. Use this suffix for the zipfile name and mark it as active.

        If all suffixes in the zipfile suffix list are active, extend the list.
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
            self._zip_files(zipf_name), self._download_ready()
        )
        for exp in gen:
            yield exp

    def _zip_files(self, zipf_name):
        """Zip files"""
        num_files = len(self.filenames)
        if num_files <= 1:
            return
        zipf = zipfile.ZipFile('tmp/'+zipf_name, 'w', zipfile.ZIP_DEFLATED)
        for i, filename in enumerate(self.filenames):
            yield self.report('Zipping Files', 100.0*i/num_files)
            zipf.write(filename)
        yield self.report('Zipping Files', 100.0)
        zipf.close()

    def _download_ready(self):
        """Send a download ready message"""
        data = self.download_msg or ''
        json_data = json.dumps({'html': data})
        yield 'event: download_ready\ndata: {}\n\n'.format(json_data)

    """Download"""
    def _download(self):
        """Download file"""
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

    """Clear session and CSRF authentication"""
    def clear_session(self):
        """Deprecate the current zip file"""
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
        session.pop(self._csrf_key, None)


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