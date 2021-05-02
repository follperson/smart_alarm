import os
from flask import Flask, render_template, g


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'smart_alarm.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    from . import db
    db.init_app(app)

    from . import alarms
    app.register_blueprint(alarms.bp)

    from . import sound_profiles
    app.register_blueprint(sound_profiles.bp)

    from . import color_profiles
    app.register_blueprint(color_profiles.bp)

    from . import wakeup
    app.register_blueprint(wakeup.bp)

    with app.app_context():
        wakeup.get_watcher()

    return app


# if __name__ == '__main__':
#     create_app()
