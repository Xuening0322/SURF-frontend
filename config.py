class Config(object):
    DEBUG = False
    TESTING = False

    # need to override this for production
    UPLOADS = '/Users/spoa/Documents/SURF-frontend/app/static/uploads'
    SESSION_COOKIE_SECURE = True
    # override this dummy secret key
    SECRET_KEY = '123456'

class ProductionConfig(Config):
    pass

class DevelopmentConfig(Config):
    DEBUG = True
    # need to override this for production
    UPLOADS = '/Users/spoa/Documents/SURF-frontend/app/static/uploads'
    SESSION_COOKIE_SECURE = False

class TestingConfig(Config):
    TESTING = True