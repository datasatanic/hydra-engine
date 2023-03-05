from .configs import config
import sys
import logging
import json


class _AnsiColorizer(object):
    _colors = dict(black=30, red=31, green=32, yellow=33,
                   blue=34, magenta=35, cyan=36, white=37, critred=-1)

    def __init__(self, stream):
        self.stream = stream

    @classmethod
    def supported(cls, stream=sys.stdout):
        if not stream.isatty():
            return False  # auto color only on TTYs
        try:
            import curses
        except ImportError:
            return False
        else:
            try:
                try:
                    return curses.tigetnum("colors") > 2
                except curses.error:
                    curses.setupterm()
                    return curses.tigetnum("colors") > 2
            except:
                raise
                return False

    def write(self, text, color):
        color = self._colors[color]
        res = f'\x1b[31;1m{text}\x1b[0m' if color == -1 else f'\x1b[{color};20m{text}\x1b[0m'
        self.stream.write(res)


class ColorHandler(logging.StreamHandler):
    def __init__(self, stream=sys.stdout):
        super(ColorHandler, self).__init__(_AnsiColorizer(stream))
        self.msg_colors = {
            logging.DEBUG: "magenta",
            logging.INFO: "cyan",
            logging.WARNING: "yellow",
            logging.ERROR: "red",
            logging.CRITICAL: "critred"
        }

    def get_color(self, levelno, default='blue'):
        return self.msg_colors.get(levelno, default)

    def emit(self, record):
        color = self.get_color(record.levelno, 'blue')
        self.stream.write(self.format(record) + "\n", color)


class DevFormatter(logging.Formatter):

    def __init__(self, fmt):
        self.max_len_name = 13
        self.max_len_msg = config.message_init_maxlen
        self.max_len_level_name = 5
        self.max_len_filename = 19
        new_fmt = fmt
        if isinstance(fmt, dict):
            new_fmt = json.dumps({k: f"%({v})s" for k, v in fmt.items()}, indent=None if config.json_inline else 4)
        super(DevFormatter, self).__init__(fmt=new_fmt)

    def format(self, record):
        # name
        if (name_l := len(record.name)) > self.max_len_name:
            self.max_len_name = name_l
        record.name = record.name + ' ' * (self.max_len_name - name_l)

        # message
        if (msg_l := len(record.getMessage())) > self.max_len_msg:
            self.max_len_msg = msg_l
        record.msg = record.msg + ' ' * (self.max_len_msg - msg_l)

        # level
        if (levelname_l := len(record.levelname)) > self.max_len_level_name:
            self.max_len_level_name = levelname_l
        record.levelname = record.levelname + ' ' * (self.max_len_level_name - levelname_l)

        # filename
        if (filename_l := len(record.filename)) > self.max_len_filename:
            self.max_len_filename = filename_l
        record.filename = record.filename + ' ' * (self.max_len_filename - filename_l)

        return super(DevFormatter, self).format(record)


jsonlogger_fmt = {
    "asctime": "asctime",
    "name": "name",
    "levelname": "levelname",
    "filename": "filename",
    "lineno": "lineno",
    "funcName": "funcName",
    "process": "process",
    "message": "message"
}

jsonlogger_fmt_error = {
    "asctime": "asctime",
    "name": "name",
    "levelname": "levelname",
    "filename": "filename",
    "lineno": "lineno",
    "funcName": "funcName",
    "process": "process",
    "message": "message",
    "error": "error"
}

dev_fmt = "%(asctime)s: %(name)s | %(levelname)s | %(message)s | %(filename)s ➜ %(funcName)s(line:%(lineno)s)"

glob_handler = "hydra_engine._logging.ColorHandler" if config.use_log_colors else "logging.StreamHandler"
glob_fmt = dev_fmt if config.log_format == 'DEV' else jsonlogger_fmt
if isinstance(glob_fmt, dict):
    glob_fmt = json.dumps({k: f"%({v})s" for k, v in glob_fmt.items()}, indent=None if config.json_inline else 4)
glob_frmttr = DevFormatter if config.log_format == 'DEV' else logging.Formatter

global_logging_config: dict = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        'default': {
            "()": glob_frmttr,
            "fmt": glob_fmt
        },

        "error-fmtr": {
            "()": glob_frmttr,
            "fmt": glob_fmt
        },
    },

    "handlers": {
        "default": {
            "formatter": "default",
            "class": glob_handler,
            "stream": "ext://sys.stderr",
        },
        "error-handler": {
            "formatter": "error-fmtr",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    },

    "loggers": {
        "common_logger": {"handlers": ["default"], "level": config.log_level},
        "error_logger": {"handlers": ["error-handler"], "level": config.log_level},
        "uvicorn": {"handlers": ["default"], "level": config.log_level},
        "uvicorn.error": {"handlers": ["default"], "level": config.log_level, "propagate": False},
        "uvicorn.access": {"handlers": ["default"], "level": config.log_level, "propagate": False},
    },
}
