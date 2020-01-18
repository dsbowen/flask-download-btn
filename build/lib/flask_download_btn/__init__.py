"""Flask-Download-Btn

Flask-Download-Btn defines a SQLAlchemy Mixin for creating bootstrap download buttons 
in Flask.

This file defines the download button manager. The manager's functions are:
1. Register download button classes
2. Register routes used by the download button

The download process has three stages:
1. Web form handling
2. File creation
3. Download

The manager's routes reflect the stages of the download process.
"""

from flask_download_btn.download_btn_mixin import DownloadBtnMixin, CreateFileMixin, HandleFormMixin

from flask import Blueprint, Response, request, session
import os


class DownloadBtnManager():
    """Download button manager"""
    registered_classes = {}

    @classmethod
    def register(cls, btn_cls):
        """Update download button class registry"""
        cls.registered_classes[btn_cls.__name__] = btn_cls
        return btn_cls

    def __init__(self, app=None, db=None):
        """Constructor

        The constructor updates default settings for buttons. It also 
        creates a tmp folder for storing zip files which download buttons 
        will send to the client.
        """
        self.db = db
        if app is not None:
            self._init_app(app)
    
    def init_app(self, app, db=None):
        self.db = db or self.db
        self._init_app(app)

    def _init_app(self, app):
        self.app = app
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['download_btn_manager'] = self
        bp = Blueprint('download_btn', __name__, template_folder='templates')

        @bp.route('/download-btn/form/<id>/<btn_cls>', methods=['POST'])
        def handle_form(id, btn_cls):
            """Web form handling"""
            btn = self.get_btn(id, btn_cls)
            btn._handle_form(request.form)
            self.db.session.commit()
            return ''

        @bp.route('/download-btn/create_files/<id>/<btn_cls>')
        def create_files(id, btn_cls):
            """File creation"""
            btn = self.get_btn(id, btn_cls)
            return Response(
                btn._create_files(app), mimetype='text/event-stream'
            )

        @bp.route('/download-btn/downloaded/<id>/<btn_cls>', methods=['POST'])
        def downloaded(id, btn_cls):
            """Indicate that button files have been downloaded"""
            btn = self.get_btn(id, btn_cls)
            btn.downloaded = True
            self.db.session.commit()
            return ''

        app.register_blueprint(bp)

    def get_btn(self, id, btn_cls):
        """Return a download button given its id and class name
        
        Authentication is required to access a button for CSRF prevention.
        """
        btn = self.registered_classes[btn_cls].query.get(id)
        if session[btn._csrf_key] == request.args.get('csrf_token'):
            return btn
        raise ValueError('CSRF attempt detected and blocked')