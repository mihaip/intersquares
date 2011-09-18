import os

class _ConstantsDict(dict):
    def __getattr__(self, m):
        return self[m]

CONSTANTS = _ConstantsDict(
    APP_NAME='Intersquares',
    IS_DEV_SERVER=os.environ.get('HTTP_HOST', '').startswith('localhost'),
)
