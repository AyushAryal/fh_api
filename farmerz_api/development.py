from .settings import *

INSTALLED_APPS += ['django_extensions']

GRAPH_MODELS = {
    'app_labels': ['authentication', 'store'],
    'exclude_models': ['Group', 'AbstractUser', 'Token', 'Session', 'ContentType',
                       'AbstractBaseSession', 'TokenProxy', 'LogEntry', 'Permission'],
    'hide_edge_labels': True,
    'color_code_deletions': True,
    'arrow_shape': 'normal',
}

CORS_ALLOW_ALL_ORIGINS = True

EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = BASE_DIR / 'logs'
