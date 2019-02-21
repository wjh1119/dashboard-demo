import os
PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in \
        ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    FLASKY_MAIL_SENDER = 'Flasky Admin <flasky@example.com>'
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    HOLIDAYS = [
        '2018/01/06', '2018/01/07', '2018/01/13', '2018/01/14', '2018/01/20',
        '2018/01/21', '2018/01/27', '2018/01/28', '2018/02/03', '2018/02/04',
        '2018/02/10', '2018/02/11', '2018/02/14', '2018/02/15', '2018/02/16',
        '2018/02/17', '2018/02/18', '2018/02/19', '2018/02/20', '2018/02/21',
        '2018/02/22', '2018/02/25', '2018/03/03', '2018/03/04', '2018/03/10',
        '2018/03/11', '2018/03/17', '2018/03/18', '2018/03/24', '2018/03/25',
        '2018/03/31', '2018/04/01', '2018/04/05', '2018/04/06', '2018/04/07',
        '2018/04/14', '2018/04/15', '2018/04/21', '2018/04/22', '2018/04/29',
        '2018/04/30', '2018/05/01', '2018/05/05', '2018/05/06', '2018/05/12',
        '2018/05/13', '2018/05/19', '2018/05/20', '2018/05/26', '2018/05/27',
        '2018/06/02', '2018/06/03', '2018/06/09', '2018/06/10', '2018/06/16',
        '2018/06/17', '2018/06/18', '2018/06/23', '2018/06/24', '2018/06/30',
        '2018/07/01', '2018/07/07', '2018/07/08'
    ]

    N_SHOW_DAYS_SHORT = 5

    PARSE_START_DATE = '2017-03-01'
    # last_update_time = '2018-12-25 14:22:08'
    INTERVAL = 300
    UPDATE_AT_BEGIN = True
    CLEAR_TEMP_DATA = True
    N_GET_RECENT_DAY = 5

    HOST = '0.0.0.0'
    PORT = 4567

    LOAD_WEB_DATA = True

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(PROJECT_DIR, 'data', 'user', 'data-dev.sqlite')
    LOAD_CHART_DATA=True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(PROJECT_DIR, 'data', 'user', 'data-test.sqlite')
    LOAD_CHART_DATA=True


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(PROJECT_DIR, 'data', 'user', 'data-prd.sqlite')
    LOAD_CHART_DATA=True

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
