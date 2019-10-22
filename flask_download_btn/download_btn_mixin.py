from flask import Markup, current_app, render_template, send_file
from sqlalchemy import Column, Text, Float, PickleType, inspect
from sqlalchemy_mutable import MutableListType, MutableDictType

class DownloadBtnMixin():
    btn_classes = Column(MutableListType)
    text = Column(Text)
    progress_bar_classes = Column(MutableListType)
    stage = Column(Text)
    pct_complete = Column(Float)
    _func = Column(PickleType)
    args = Column(MutableListType)
    kwargs = Column(MutableDictType)

    @property
    def model_id(self):
        return type(self).__name__+'-'+str(self._id)

    @property
    def progress_model_id(self):
        return self.model_id+'-progress'

    @property
    def _id(self):
        id = inspect(self).identity
        return id[0] if id else None

    @property
    def func(self):
        return self._func

    @func.setter
    def func(self, value):
        assert callable(value) or value is None
        self._func = value

    @property
    def _btn_classes(self):
        return ' '.join(self.btn_classes)
    
    @property
    def _text(self):
        return self.text or ''
    
    @property
    def _progress_bar_classes(self):
        return ' '.join(self.progress_bar_classes)

    @property
    def _progress_text(self):
        stage = '' if self.stage is None else self.stage+': '
        if self.pct_complete is not None:
            pct_complete = '{:.0f}%'.format(self.pct_complete)
        else:
            pct_complete = ''
        return stage + pct_complete

    @property
    def _pct_complete(self):
        return self.pct_complete if self.pct_complete is not None else 0.0

    def __init__(
            self, btn_classes=None, text=None, progress_bar_classes=None,
            pct_complete=None, func=None, args=[], kwargs={}
        ):
        self.btn_classes = btn_classes
        self.text = text
        self.progress_bar_classes = progress_bar_classes
        self.pct_complete = pct_complete
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self._default_settings()

    def _default_settings(self):
        manager = current_app.extensions['download_btn_manager']
        self.btn_classes = self.btn_classes or manager.btn_classes
        self.progress_bar_classes = (
            self.progress_bar_classes or manager.progress_bar_classes
        )

    def render(self):
        return Markup(render_template('download_btn/button.html', btn=self))

    def script(self):
        return Markup(render_template('download_btn/script.html', btn=self))
    
    def _make_files(self):
        import time
        for i in range(5):
            yield 'event: progress_report\ndata: {}\n\n'.format(i)
            time.sleep(1)
        yield 'event: download_ready\ndata: \n\n'

    def _download(self):
        return send_file('text.txt', as_attachment=True)