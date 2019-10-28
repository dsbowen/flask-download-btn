"""Download button mixin"""

from flask import Markup, current_app, render_template, send_file, session
from sqlalchemy import Column, ForeignKey, Integer, String, Text, PickleType, inspect
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm import relationship
from sqlalchemy_function import FunctionBase
from sqlalchemy_function import FunctionMixin as FunctionMixinBase
from sqlalchemy_mutable import MutableListType, MutableDictType
import itertools
import json
import os
import zipfile


class DownloadBtnMixin(FunctionBase):
    id = Column(Integer, primary_key=True)
    _zipf_sfxs = Column(MutableListType)
    btn_classes = Column(MutableListType)
    btn_template = Column(String)
    text = Column(Text)
    progress_classes = Column(MutableListType)
    progress_template = Column(String)
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

    @property
    def _zipf_name_key(self):
        return self.model_id+'zipf-name'

    @property
    def _zipf_sfx_key(self):
        return self.model_id+'zipf-sfx'

    @property
    def _btn_classes(self):
        """Button <div> classes in html format"""
        return ' '.join(self.btn_classes)
    
    @property
    def _text(self):
        return self.text or ''
    
    @property
    def _progress_classes(self):
        """Progress bar <div> classes in html format"""
        return ' '.join(self.progress_classes)

    @property
    def _form(self):
        return 'form' if self.form_id is None else '#'+self.form_id

    def __init__(
            self, btn_classes=None, btn_template=None, text=None, 
            progress_classes=None, progress_template=None, form_id=None, 
            handle_form_functions=[], create_file_functions=[],
            attachment_filename=None, filenames=[], download_msg=None
        ):
        self._set_function_relationships()
        self._zipf_sfxs = []
        self.btn_classes = btn_classes
        self.btn_template = btn_template
        self.text = text
        self.progress_classes = progress_classes
        self.progress_template = progress_template
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
        return Markup(render_template('download_btn/script.html', btn=self))

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

    def _handle_form(self, response):
        [
            f.func(f.parent, response, *f.args, **f.kwargs) 
            for f in self.handle_form_functions
        ]
    
    def _gen_zipf_name(self):
        """Generate a unique zipfile name for the session"""
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

        Call the create_files functions and return progress reports as server sent events. When the generator terminates, send a 'download_ready' message.
        """
        app.app_context().push()
        db = app.extensions['download_btn_manager'].db
        db.session.add(self)
        gen = itertools.chain(*[f() for f in self.create_file_functions])
        for exp in gen:
            yield exp
        for exp in self._zip_files(zipf_name):
            yield exp
        data = self.download_msg or ''
        json_data = json.dumps({'html': data})
        yield 'event: download_ready\ndata: {}\n\n'.format(json_data)

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
        response = send_file(
            filename, as_attachment=True, 
            attachment_filename=attachment_filename
        )
        response.headers['Cache-Control'] = (
            'no-cache, no-store, must-revalidate'
        )
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        self._deprecate_zipf()
        return response

    def _deprecate_zipf(self):
        name = session[self._zipf_name_key]
        sfx = session[self._zipf_sfx_key]
        try:
            os.remove('tmp/'+name)
        except:
            pass
        self._zipf_sfxs[sfx] = False
        session.pop(self._zipf_name_key)
        session.pop(self._zipf_sfx_key)


class FunctionMixin(FunctionMixinBase):
    id = Column(Integer, primary_key=True)

    @declared_attr
    def btn_id(self):
        return Column(Integer, ForeignKey('download_btn.id'))

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