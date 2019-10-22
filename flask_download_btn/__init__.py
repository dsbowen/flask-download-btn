from flask_download_btn.download_btn_mixin import DownloadBtnMixin

from flask import Blueprint, Response, request


class DownloadBtnManager():
    registered_classes = {}

    @classmethod
    def register(cls, btn_cls):
        cls.registered_classes[btn_cls.__name__] = btn_cls
        return btn_cls

    def __init__(self, app=None, **kwargs):
        self.btn_classes = ['btn', 'btn-primary']
        self.progress_bar_classes = ['progress-bar']
        self.setattrs(**kwargs)
        if app is not None:
            self._init_app(app)
    
    def init_app(self, app, **kwargs):
        self.setattrs(**kwargs)
        self._init_app(app)

    def _init_app(self, app):
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['download_btn_manager'] = self

        bp = Blueprint('download_btn', __name__, template_folder='templates')
        @bp.route('/_download/<id>/<btn_cls>')
        def _download(id, btn_cls):
            btn = self.registered_classes[btn_cls].query.get(id)
            return Response(btn._download(), mimetype='text/event-stream')
        app.register_blueprint(bp)
    
    def setattrs(self, btn_classes=None, progress_bar_classes=None):
        self.btn_classes = btn_classes or self.btn_classes
        self.progress_bar_classes = (
            progress_bar_classes or self.progress_bar_classes
        )