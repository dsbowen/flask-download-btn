"""Flask-Download-Btn

Flask-Download-Btn provides a mixin for creating bootstrap download buttons in Flask.
"""

from flask_download_btn.download_btn_mixin import DownloadBtnMixin

from flask import Blueprint, Response, request


class DownloadBtnManager():
    """Download button manager"""
    registered_classes = {}

    @classmethod
    def register(cls, btn_cls):
        """Download button class registry"""
        cls.registered_classes[btn_cls.__name__] = btn_cls
        return btn_cls

    def __init__(self, app=None, **kwargs):
        self.btn_classes = ['btn', 'btn-primary']
        self.btn_template = 'download_btn/button.html'
        self.progress_classes = ['progress-bar']
        self.progress_template = 'download_btn/progress.html'
        self.setattrs(**kwargs)
        if app is not None:
            self._init_app(app)
    
    def init_app(self, app, **kwargs):
        self.setattrs(**kwargs)
        self._init_app(app)

    def setattrs(
            self, btn_classes=None, btn_template=None, 
            progress_classes=None, progress_template=None,
        ):
        self.btn_classes = btn_classes or self.btn_classes
        self.btn_template = btn_template or self.btn_template
        self.progress_classes = progress_classes or self.progress_classes
        self.progress_template = progress_template or self.progress_template

    def _init_app(self, app):
        self.app = app
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['download_btn_manager'] = self
        bp = Blueprint('download_btn', __name__, template_folder='templates')

        @bp.route('/download-btn/form/<id>/<btn_cls>', methods=['POST'])
        def handle_form(id, btn_cls):
            btn = self.get_btn(id, btn_cls)
            btn._handle_form(request.form)
            return ''

        @bp.route('/download-btn/make_files/<id>/<btn_cls>')
        def make_files(id, btn_cls):
            """Runs the download button's make_files function

            The make_files function must return a stream of server sent events. The SSE's report download progress to the client.
            """
            btn = self.get_btn(id, btn_cls)
            return Response(
                btn._make_files_wrapper(app), mimetype='text/event-stream'
            )

        @bp.route('/download-btn/download/<id>/<btn_cls>')
        def download(id, btn_cls):
            """Download files"""
            btn = self.get_btn(id, btn_cls)
            return btn._download()

        app.register_blueprint(bp)

    def get_btn(self, id, btn_cls):
        """Return a download button given its id and class name"""
        return self.registered_classes[btn_cls].query.get(id)
    