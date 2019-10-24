"""Download button mixin"""

from flask import Markup, current_app, render_template, send_file
from sqlalchemy import Column, String, Text, PickleType, inspect
from sqlalchemy_mutable import MutableListType, MutableDictType
import json
import os
import zipfile

class DownloadBtnMixin():
    btn_classes = Column(MutableListType)
    btn_template = Column(String)
    text = Column(Text)
    progress_classes = Column(MutableListType)
    progress_template = Column(String)
    form_id = Column(String)
    form_handler = Column(PickleType)
    _make_files = Column(PickleType)
    args = Column(MutableListType)
    kwargs = Column(MutableDictType)
    attachment_filename = Column(String)
    filenames = Column(MutableListType)
    download_msg = Column(Text)

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
    def zipf_name(self):
        """Identity of the zip file"""
        return self.model_id+'.zip'

    @property
    def make_files(self):
        return self._make_files

    @make_files.setter
    def make_files(self, value):
        assert callable(value) or value is None
        self._make_files = value

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

    def __init__(
            self, btn_classes=None, btn_template=None, text=None, 
            progress_classes=None, progress_template=None,
            form_id=None, form_handler=None,
            make_files=None, args=[], kwargs={},
            attachment_filename=None, filenames=[], download_msg=None
        ):
        self.btn_classes = btn_classes
        self.btn_template = btn_template
        self.text = text
        self.progress_classes = progress_classes
        self.progress_template = progress_template
        self.form_id = form_id
        self.form_handler = form_handler
        self.make_files = make_files
        self.args = args
        self.kwargs = kwargs
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
        if self.form_handler is None:
            return
        self.form_handler(self, response)

    def _make_files_wrapper(self, app):
        """Wrap the make_files function

        Call the make_files function and return progress reports as server sent events. When the make_files generator terminates, send a 'download_ready' message.
        """
        app.app_context().push()
        if self.make_files is not None:
            for exp in self.make_files(self, *self.args, **self.kwargs):
                yield exp
        for exp in self._zip_files():
            yield exp
        data = self.download_msg or ''
        json_data = json.dumps({'html': data})
        yield 'event: download_ready\ndata: {}\n\n'.format(json_data)

    def _zip_files(self):
        """Zip files"""
        num_files = len(self.filenames)
        if num_files <= 1:
            return
        try:
            os.remove(self.zipf_name)
        except:
            pass
        zipf = zipfile.ZipFile(self.zipf_name, 'w', zipfile.ZIP_DEFLATED)
        for i, filename in enumerate(self.filenames):
            yield self.report('Zipping Files', 100.0*i/num_files)
            zipf.write(filename)
        yield self.report('Zipping Files', 100.0)
        zipf.close()

    def _download(self):
        """Download file"""
        num_files = len(self.filenames)
        if num_files == 0:
            return
        filename = self.filenames[0] if num_files == 1 else self.zipf_name
        response = send_file(
            filename, as_attachment=True,
            attachment_filename=self.attachment_filename
        )
        response.headers['Cache-Control'] = (
            'no-cache, no-store, must-revalidate'
        )
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        if filename == self.zipf_name:
            os.remove(self.zipf_name)
        return response
