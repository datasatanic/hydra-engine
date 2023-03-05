import sys
from typing import Literal, Union

from pydantic import BaseSettings, Field, FilePath, validator


class HypercornConfig(BaseSettings):
    application_path: str = Field('hydra_engine:app')
    bind: str = Field('0.0.0.0:5000', env='BIND')
    include_server_header: bool = False

    graceful_timeout: int = Field(10, env='GRACEFUL_TIMEOUT')
    keep_alive_timeout: int = Field(60, env='KEEP_ALIVE_TIMEOUT')

    worker_class: str = 'uvloop' if 'uvloop' in  sys.modules else 'asyncio'
    workers: int = Field(1, env="WORKERS")

    # region Logging
    loglevel: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR'] = Field('INFO', env='LOG_LEVEL')
    debug: bool = False
    accesslog: Union[FilePath, str] = Field(None, env='ACCESSLOG')
    errorlog: Union[FilePath, str] = Field('-', env='ERRORLOG')
    access_log_format: str = '{"host":%(h)s,"user":%(u)s,"time":%(t)s,"method":%(m)s,"protocol":%(H)s,"scheme":%(S)s,' \
                             '"url":%(U)s,"query":%(q)s,"status":%(s)s,"response_length":%(B)s,"referer":%(f)s,' \
                             '"user_agent":%(a)s,"request_microseconds":%(D)s,"process_id":%(p)s}'
    logconfig_dict: dict = None

    # endregion

    @validator('loglevel', pre=True)
    def loglevel_upper(cls, v: str):
        return v.upper()

    @validator('debug', pre=True)
    def debug_mode(cls, v, values):
        return values['loglevel'] == 'DEBUG'

    @validator('logconfig_dict', pre=True)
    def configure_logconfig_dict(cls, v, values):
        return cls.configure_logger(values)

    # noinspection PyTypedDict
    @classmethod
    def configure_logger(cls, values):
        formatters: dict = {
            'default': {
                'format': '%(levelname)s %(asctime)s %(name)s %(message)s %(pathname)s %(funcName)s %(lineno)d  %('
                          'processName)s %(process)d %(threadName)s %(thread)d',
                '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                'rename_fields': {'asctime': 'time'}
            },
            'access': {'format': '%(message)s'}
        }
        handlers = {}
        errorlog_ = values['errorlog']
        accesslog_ = values['accesslog']
        if errorlog_ in ['-', None]:
            handlers['default'] = {'formatter': 'default',
                                   'class': 'logging.StreamHandler',
                                   'stream': 'ext://sys.stderr'}
        else:
            handlers['default'] = {
                'formatter': 'default',
                'class': 'logging.FileHandler',
                'filename': errorlog_
            }
        if accesslog_:
            if accesslog_ == '-':
                handlers['access'] = {'formatter': 'access',
                                      'class': 'logging.StreamHandler',
                                      'stream': 'ext://sys.stdout'}
            else:
                handlers['access'] = {'formatter': 'access',
                                      'class': 'logging.FileHandler',
                                      'filename': accesslog_}

        loggers: dict = {'hypercorn': {'handlers': ['default'], 'level': values['loglevel']},
                         'hypercorn.error': {'propagate': True},
                         'hypercorn.app': {'propagate': True}}
        loggers |= {'hypercorn.access': {'handlers': ['access'],
                                         'level': values['loglevel']}} if accesslog_ else {}

        return {'version': 1,
                'disable_existing_loggers': True,
                'formatters': formatters,
                'handlers': handlers,
                'loggers': loggers
                }
