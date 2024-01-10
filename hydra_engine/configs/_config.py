from pydantic import BaseSettings, Field, validator, HttpUrl
import platform


class Config(BaseSettings):
    # service parameters

    force_recreate_at_start: bool = Field(True, env='FORCE_RECREATE_AT_START')
    crontab_string: str = Field('* * * * *', env='CRONTAB_STRING')
    service_port: int = Field(8084, env='SERVICE_PORT')
    uvicorn_workers: int = Field(1, env='WORKERS')
    uvicorn_access_logs: bool = Field(True, env='USE_UVICORN_ACCESS_LOGS')
    message_init_maxlen: int = Field(65)

    hydra_result_page_size: int = Field(10, env='CONFIGURATOR_RESULT_PAGE_SIZE')
    hydra_max_result_page_size: int = Field(500, env='CONFIGURATOR_MAX_RESULT_PAGE_SIZE')
    reindex_hydra_reschedule_in_seconds: int = Field(30, env='REINDEX_WORKPLACE_RESCHEDULE_IN_SECONDS')

    log_level: str = Field('DEBUG', env='LOG_LEVEL')
    log_format: str = Field('DEV', env='LOG_FORMAT')  # DEV or JSON
    use_log_colors: bool = Field(1, env='USE_LOG_COLORS')
    json_inline: bool = Field(1, env='JSON_INLINE')

    # index
    filespath: str = Field('files/', env='FILES_PATH')
    tree_filename: str = Field('ui.meta', env='TREE_FILENAME')
    wizard_filename: str = Field('wizard.meta', env='WIZARD_FILENAME')
    index_path: str = Field('hydra_engine/files/index/', env='INDEX_PATH')
    accessible_when_reindex: bool = Field(True, env='ACCESSIBLE_WHEN_REINDEX')
    use_ram_storage: bool = Field(False, env='USE_RAM_STORAGE')

    # 2 all envs end for new keycloak test
    db_adress: str = Field('localhost:5432', env='PROVIDER_DBSTORAGE_ADDRESS')
    db_dbname: str = Field('hydra-index', env='PROVIDER_DBSTORAGE_DBNAME')
    db_user: str = Field('postgres', env='PROVIDER_DBSTORAGE_USER')
    db_password: str = Field('', env='PROVIDER_DBSTORAGE_pwd')

    dictionaries_fid: str = Field('TEST', env='PROVIDER_FID')

    # consul
    platform: str = Field(f"{platform.system()}")

    @validator('log_level')
    def log_level_lower(cls, v):
        return v.upper()
