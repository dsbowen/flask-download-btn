"""# Download button manager"""

from .download_btn_mixin import DownloadBtnMixin

from flask import Blueprint, Response, request, session

default_settings = {
    'db': None,
    'btn_template': 'download_btn/button.html',
    'progress_template': 'download_btn/progress.html',
}


class DownloadBtnManager():
    """
    The manager has two responsibilities:

    1. Register download button classes.
    2. Register routes used by the download button.

    Parameters
    ----------
    app : flask.app.Flask or None, default=None
        Flask application with which download buttons are associated.

    \*\*kwargs :
        You can set the download button manager's attributes by passing them 
        as keyword arguments.

    Attributes
    ----------
    db : flask_sqlalchemy.SQLAlchemy or None, default=None
        SQLAlchemy database associated with the Flask app.

    btn_template : str, default='download_btn/button.html'
        Path to the default button template.

    progress_template : str, default='download_btn/progress.html'
        Path to the default progress bar template.

    Notes
    -----
    If `app` and `db` are not set on initialization, they must be set using 
    the `init_app` method before the app is run.

    Examples
    --------
    ```python
    from flask import Flask
    from flask_download_btn import DownloadBtnManager
    from flask_sqlalchemy import SQLAlchemy

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db = SQLAlchemy(app)
    download_btn_manager = DownloadBtnManager(app, db)
    ```
    """

    # maps name of button classes to button classes
    # used in the `_get_btn` method
    _registered_classes = {}

    @classmethod
    def register(cls, btn_cls):
        """
        Decorator for updating the download button class registry.
        
        Parameters
        ----------
        btn_cls : class
            Class of the registered button.

        Returns
        -------
        btn_cls

        Examples
        --------
        ```python
        from flask_download_btn import DownloadBtnMixin

        @DownloadBtnManager.register
        class DownloadBtn(DownloadBtnMixin, db.Model):
        \    ...
        ```
        """
        cls._registered_classes[btn_cls.__name__] = btn_cls
        return btn_cls

    def __init__(self, app=None, **kwargs):
        settings = default_settings.copy()
        settings.update(kwargs)
        [setattr(self, key, val) for key, val in settings.items()]
        if app is not None:
            self._init_app(app)
    
    def init_app(self, app, **kwargs):
        """
        Initialize the download button manager with the application.

        Parameters
        ----------
        app : flask.app.Flask
            Application with which the download button manager is associated.

        \*\*kwargs :
            You can set the download button manager's attributes by passing
            them as keyword arguments.
        """
        [setattr(self, key, val) for key, val in kwargs.items()]
        self._init_app(app)

    def _init_app(self, app):
        """
        The download process has three stages:

        1. Web form handling
        2. File creation
        3. Download

        The manager's routes reflect the stages of the download process.
        """
        self.app = app
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['download_btn_manager'] = self
        bp = Blueprint('download_btn', __name__, template_folder='templates')

        @bp.route('/download-btn/form/<id>/<btn_cls>', methods=['POST'])
        def handle_form(id, btn_cls):
            """Web form handling"""
            btn = self._get_btn(id, btn_cls)
            btn._handle_form(request.form)
            self.db.session.commit()
            return ''

        @bp.route('/download-btn/create_files/<id>/<btn_cls>')
        def create_files(id, btn_cls):
            """File creation"""
            btn = self._get_btn(id, btn_cls)
            return Response(
                btn._create_files(app), mimetype='text/event-stream'
            )

        @bp.route('/download-btn/downloaded/<id>/<btn_cls>', methods=['POST'])
        def downloaded(id, btn_cls):
            """Indicate that button files have been downloaded"""
            btn = self._get_btn(id, btn_cls)
            btn.downloaded = True
            self.db.session.commit()
            return ''

        app.register_blueprint(bp)

    def _get_btn(self, id, btn_cls):
        """
        Get a download button. This method prevents CSRF by checking that the 
        CSRF token sent with the request matches the CSRF token stored in the 
        session.

        Parameters
        ----------
        id : 
            Identity of the button.

        btn_cls : str
            Name of the button class.
        
        Returns
        -------
        button : btn_cls
            Button of type `btn_cls` with the identity `id`.
        """
        btn = self._registered_classes[btn_cls].query.get(id)
        if session[btn.get_id('csrf')] == request.args.get('csrf_token'):
            return btn
        raise ValueError('CSRF attempt detected and blocked')