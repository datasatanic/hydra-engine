import os
import shutil
from timeit import default_timer as timer
from copy import copy
from collections import deque

import logging

from whoosh import query as wq
from whoosh import index
from whoosh.filedb.filestore import RamStorage
from whoosh.qparser import MultifieldParser, SingleQuotePlugin, PlusMinusPlugin
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
import datetime as dt
import warnings
import tzlocal
from whoosh import query, sorting
from whoosh.searching import ResultsPage

# import asyncpg
from ..configs import config
from hydra_engine.search.status import IndexStatus
from hydra_engine.search.doc_parser import get_documents_from_hydra

logger = logging.getLogger('common_logger')


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class HydraSearcher(metaclass=SingletonMeta):
    __dbconnstr = f"postgresql://{config.db_user}:{config.db_password}@" \
                  f"{config.db_adress}/{config.db_dbname}"

    def __init__(self, index_name: str, schema):
        self.pagelen = 10
        self.pagelen_limit = 1000
        self.accessible_when_reindex = config.accessible_when_reindex
        self._main_index_lock = True
        self._wait_for_add_tasks = False
        self.index_name = index_name
        self.schema = schema
        self.index_status = None
        self.index_storage = self.__initialize_index()
        self.spare_index_storage = None
        self.documents_at_index_hash_sums = {}
        self.final_documents = deque()
        self.is_scheduled = False

        self.is_reindexing = False
        self.has_scheduled = False
        self.started_schedule = False

        # Order matters!
        self.qp = MultifieldParser(schema.showable_fields, schema=schema)
        self.qp.add_plugin(SingleQuotePlugin())  # exact hit with "term" in quotes
        self.qp.add_plugin(PlusMinusPlugin(minusexpr=r"^-| -"))  # required terms with "+" / exclude term with "-"

        if self.has_scheduled and not self.started_schedule:
            self.started_schedule = True

        match self.index_status:
            case IndexStatus.EMPTY:
                pass
            case IndexStatus.CREATED:
                pass
            case IndexStatus.NEED_TO_UNSTASH:
                pass

        self.scheduler = AsyncIOScheduler(timezone=str(tzlocal.get_localzone()))
        self.scheduler.start()

        self._main_index_lock = False

        # async def post_init(self):
        #     if self.index_status == IndexStatus.NEED_TO_UNSTASH:
        #         bytes_count, files = await self.__unstash_index_from_db()
        #         if bytes_count == -1:  # unstash from db failed
        #             logger.info(f"Unstash failed. Handling  situation for {self.index_name}")
        #             self.__failed_unstash_callback()
        #             return
        #
        #         if len(files) > 0:
        #             self.index_storage.storage.destroy()
        #             self.index_storage.storage.locks = {}
        #             self.index_storage.storage.files = files
        #             self.index_status = IndexStatus.READ_FROM_DISK
        #             logger.info(f"Successfully unstash index from DB")
        #             return

        self.index_status = IndexStatus.EMPTY

    # read index from file / create if empty
    def __create_empty_index(self):
        """Creates empty file-index with ram/file storage"""
        return index.create_in(
            config.index_path,
            self.schema,
            indexname=self.index_name
        ) if not config.use_ram_storage else RamStorage().create().create_index(self.schema, indexname=self.index_name)

    def __initialize_index(self):
        """initialize index"""
        index_path = config.index_path
        # dir check or create
        if not os.path.exists(index_path):
            os.makedirs(index_path)

        # parameter to clear old index
        if config.force_recreate_at_start:
            if not config.use_ram_storage:
                # clear dir
                for root, dirs, files in os.walk(index_path):
                    for f in files:
                        os.unlink(os.path.join(root, f))
                    for d in dirs:
                        shutil.rmtree(os.path.join(root, d))

            # creates new index
            self.index_status = IndexStatus.EMPTY
            logger.debug(f'CREATED EMPTY RAM index for <{self.index_name}>')
            return self.__create_empty_index()

        else:
            if config.use_ram_storage:
                """For RamStorage"""
                self.index_status = IndexStatus.NEED_TO_UNSTASH  # ###############################
                return self.__create_empty_index()
            else:
                """For FileStorage"""
                if index.exists_in(index_path, indexname=self.index_name):
                    self.index_status = IndexStatus.READ_FROM_DISK
                    logger.info(f'LOAD <{self.index_name}> index from existing files')
                    return index.open_dir(index_path, indexname=self.index_name)
                else:
                    self.index_status = IndexStatus.EMPTY
                    logger.info(f'CREATED EMPTY index, CAUSE files <{self.index_name}_index> not found')
                    return self.__create_empty_index()

    def __failed_unstash_callback(self):
        """Used to handle unstash procedure failure (for any reason) and decide what should I do"""
        pass

    def __parse_input_string(self, query_input: str) -> wq.Query:
        """Parse input query with whoosh's query parser"""
        return self.qp.parse(query_input)

    async def __to_index(self):
        """Main function to launch indexing"""
        common_index_start = timer()
        if self.index_status in [IndexStatus.CREATED, IndexStatus.READ_FROM_DISK]:
            if self.accessible_when_reindex:
                self.spare_index_storage = copy(self.index_storage)
                logger.info('Now there are DUPLICATED indexes!')

        self.final_documents.extend(get_documents_from_hydra())
        logger.debug(f"Parse Hydra Documents finished in {(timer() - common_index_start):.3f} seconds")

        # index commit
        if len(self.final_documents) > 0:
            logger.debug(f"{self.index_name.upper()} index: Committing {len(self.final_documents)} documents")
            index_writer = self.index_storage.writer()
            start = timer()
            logger.debug(f"\"ADD TO INDEX\" operation")

            total_documents_count = len(self.final_documents)
            step_100_percent_divider = 5
            quintile = total_documents_count / step_100_percent_divider
            next_step = total_documents_count - quintile
            percentage_step = float(100 / step_100_percent_divider)
            total_percentage = 0
            while self.final_documents:
                if len(self.final_documents) < next_step:
                    total_percentage += percentage_step
                    next_step = next_step - quintile
                    logger.debug(f"{total_percentage:.2f}% Done. Time {timer() - start:.3f}")

                doc = self.final_documents.popleft()
                self.__add_to_index(doc, top_level=True, writer=index_writer)

            logger.debug(f"\"ADD TO INDEX\" operation finished {timer() - start:.3f}")
            start = timer()

            try:
                self._main_index_lock = True
                logger.debug(f"\"COMMIT TO INDEX\" operation")
                index_writer.commit(optimize=True)  # commit closes a writer
                logger.debug(f"{self.index_name.upper()} index: Index now contains "
                             f"{(doc_count := self.index_storage.doc_count_all())} total documents!")
                self.index_storage.close()
                if doc_count > 0:
                    self.index_status = IndexStatus.CREATED
                if self.accessible_when_reindex and self.spare_index_storage is not None:
                    del self.spare_index_storage
                    self.spare_index_storage = None
                    logger.info('now it\'s only one MAIN index')
                tmr = timer()
                logger.info(
                    f"Index commit time {tmr - start:.3f} seconds. Total indexing time "
                    f"{tmr - common_index_start:.3f} for {type(self.index_storage.storage).__name__}")
            except Exception:
                logger.warning("index commit error")
        else:
            logger.info(f"{self.index_name.upper()} index: There is no new tasks (documents)")

        # await self.__stash_index_to_db()
        self._main_index_lock = False

    async def reindex_hydra(self, start_task_scheduled=False):
        if self.is_reindexing:
            return {'status': 'already indexing, please wait for task finished'}
        self.is_reindexing = True
        logger.info('Started indexing...')
        if start_task_scheduled:
            if self.is_scheduled:
                await self.__to_index()
        else:
            await self.__to_index()
        self.is_reindexing = False
        logger.info('Manager finished indexing...')

        if start_task_scheduled or self.started_schedule:
            self.schedule_reindex()

        self.scheduler.resume()
        return {'status': 'updated_index'}

    def schedule_reindex(self):
        if not self.is_scheduled:
            return

        run_date = str(dt.datetime.now() + dt.timedelta(seconds=300))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            trigger = DateTrigger(run_date=run_date)

        self.scheduler.add_job(self.reindex_hydra,
                               trigger=trigger,
                               args=[True])
        for job in self.scheduler.get_jobs():
            logger.debug(f"Added job {job} with async scheduler")

    # Order is important! Parents first, children after, only way for making groups work properly
    def __add_to_index(self, current_document: dict, top_level=True, writer=None):
        """Processing document in according to schema and nested document logic"""
        current_writer = self.index_storage.writer() if writer is None else writer
        d = {k: v for k, v in current_document.items() if k in self.schema.stored_names()}
        if 'hitable' in self.schema:
            d['hitable'] = 1 if top_level else 0
        if 'nested_documents' in current_document:
            # deletion all children if they have
            q = wq.NestedParent(wq.Term("id", current_document['id']), wq.Every())
            deleted_docs = current_writer.delete_by_query(q)

            current_writer.update_document(**d)
            current_writer.start_group()
            for child in current_document['nested_documents']:
                self.__add_to_index(child, top_level=False, writer=current_writer)
            current_writer.end_group()
        else:
            current_writer.update_document(**d)

    def __close_index(self):  # graceful close
        self.index_storage.close()

    def _get_storage(self):
        if not self._main_index_lock:
            return self.index_storage
        return self.spare_index_storage

    async def perform_search(self, query_user_input, pagenum=None, pagelen=None):
        query = self.qp.parse(query_user_input)
        total_pagelen = self.pagelen if pagelen is None else pagelen
        if total_pagelen > self.pagelen_limit:
            total_pagelen = self.pagelen_limit

        if (storage := self._get_storage()) is None:
            return {'status': 'currently reindexing'}

        with storage.searcher() as searcher:
            pnum = 1 if pagenum is None else pagenum
            search_hits = searcher.search(query, limit=pnum * total_pagelen)
            fragmenter = search_hits.fragmenter
            fragmenter.surround = 80
            fragmenter.maxchars = 300

            results = search_hits if pagenum is None else ResultsPage(search_hits, pnum, total_pagelen)
            return self.prettify_results(results=list(results))

    def prettify_results(self, results: list, highlight: bool = True, total_size: dict = None):
        final_pretty_results = []
        for r in results:
            d = {**r}
            if highlight:
                for f in self.schema.highlightable:
                    if r[f] and isinstance(r[f], str):
                        d[f] = r.highlights(f) or r[f]

            final_pretty_results.append(d)
        return final_pretty_results

    # async def __stash_index_to_db(self):
    #     """Save index filestore files as bytearrays to db"""
    #     logger.debug('try to stash')
    #     conn = None
    #     try:
    #         conn = await asyncpg.connect(HydraSearcher.__dbconnstr)
    #         logger.debug('connected to db')
    #     except Exception:
    #         logger.warning('Cannot connect to db to stash index files')
    #         return
    #     if conn:
    #         try:
    #             async with conn.transaction():
    #                 await conn.execute('''DELETE FROM public."IndexData" WHERE "indexName" = ($1) ''', self.index_name)
    #                 timestamp_utc = datetime.now(pytz.timezone('Etc/GMT-5'))
    #                 await conn.executemany(
    #                     '''INSERT INTO public."IndexData"("indexName", "indexNameFilename", "FileData", "timestamp")
    #                     VALUES ($1, $2, $3, $4)''',
    #                     [(self.index_name, file_name, self.index_storage.storage.files[file_name], timestamp_utc)
    #                      for file_name in self.index_storage.storage.files]
    #                 )
    #                 logger.debug(f"Successfully stashed index {self.index_name}")
    #         except Exception as e:
    #             logger.error(f"Cannot perform db operations {e}")
    #         await conn.close()
    #
    # async def __unstash_index_from_db(self):
    #     """Unstash index data from db to index object (whoosh's filestorage.files as binary files)"""
    #     logger.debug('try to unstash index files from DB')
    #     bytescount = -1
    #     new_files = {}
    #     conn = None
    #     try:
    #         conn = await asyncpg.connect(BaseIndex.__dbconnstr)
    #         logger.debug('connected to db')
    #     except Exception:
    #         logger.warning('Cannot connect to db to stash index files')
    #     if conn:
    #         try:
    #             async with conn.transaction():
    #                 bytescount += 1
    #                 rows = await conn.fetch(
    #                     '''
    #                     SELECT "indexNameFilename", "FileData"
    #                     FROM public."IndexData"
    #                     WHERE "indexName" = ($1)''', self.index_name
    #                 )
    #
    #                 if rows:
    #                     logger.debug(f"Got {len(rows)} index files")
    #                     for row in rows:
    #                         if name := row['indexNameFilename']:
    #                             new_files[name] = (bytedata := row['FileData'])
    #                             bytescount += len(bytedata)
    #                 else:
    #                     logger.info(f'Index {self.index_name} is empty at remote storage, cannot unstash')
    #         except Exception as e:
    #             logger.error(f"Cannot perform db operations {e}")
    #
    #         await conn.close()
    #     return bytescount, new_files
