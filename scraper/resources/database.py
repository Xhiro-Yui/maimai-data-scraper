import logging
import sqlite3
from dataclasses import asdict
from typing import Optional

from scraper.exception.scraper_exception import ScraperError
from scraper.resources.database_schema import TABLE_LIST
from scraper.resources.models import PlayData
from scraper.utils.path_resolver import resolve_app_file_path

logger = logging.getLogger(__name__)


class Database:
    """
    Manages the SQLite database connection and schema initialization for the MaiMai scraper.
    """

    def __init__(self, db_name: str = "maimai_data.db") -> None:
        """
        Initializes the Database.

        Args:
            db_name (str): The name of the SQLite database file. Defaults to "maimai_data.db".
        """
        self._db_name: str = db_name
        self._db_path: str = resolve_app_file_path(filename=self._db_name)
        self._connection: Optional[sqlite3.Connection] = None  # Persistent connection held by the object

        logging.info(f"Initializing database schemas for {self._db_path}")
        self._initialize_database()

    def _open_connection(self) -> sqlite3.Connection:
        """
        Establishes and stores a persistent connection to the SQLite database
        within the DatabaseManager object. If a connection is already open, it returns it.
        """
        if self._connection is None:
            try:
                self._connection = sqlite3.connect(self._db_path)
                self._connection.row_factory = sqlite3.Row
                logger.info(f"Persistent connection opened to {self._db_path}")
            except sqlite3.Error as e:
                raise ScraperError(f"Failed to open database connection: {e}")
        return self._connection

    def close_connection(self) -> None:
        """
        Closes the persistent database connection if it is open.
        """
        if self._connection:
            try:
                self._connection.close()
                logger.info("Persistent connection closed.")
            except sqlite3.Error as e:
                logger.error(f"Error closing persistent connection: {e}")
            finally:
                self._connection = None

    def _get_active_connection(self) -> sqlite3.Connection:
        """
        Get the currently active (persistent) connection.
        If no persistent connection is open, it will attempt to open one.
        """
        if self._connection is None:
            logger.info("Persistent connection not open. Attempting to open now.")
            self._open_connection()  # Attempt to open if not already.
        return self._connection

    def _object_exists(self, name: str, obj_type: str) -> bool:
        """
        Check if a database object exists in sqlite_master.

        Args:
            name (str): Name of the object (table, index, view, trigger)
            obj_type (str): One of "table", "index", "view", "trigger"

        Returns:
            bool: True if the object exists, False otherwise
        """
        conn = self._get_active_connection()
        query = """
            SELECT 1 
            FROM sqlite_master 
            WHERE type = ? AND name = ?
            LIMIT 1;
        """
        cursor = conn.execute(query, (obj_type, name))
        exists = cursor.fetchone() is not None
        cursor.close()

        logger.debug(f"{obj_type} [{name}] exists: {exists}")
        return exists

    def _initialize_database(self) -> None:
        """
        Initializes the database schema by creating necessary tables and indexes

        See Also
        --------
        database_schema.py
        """
        conn = self._get_active_connection()
        try:
            cursor = conn.cursor()
            logger.info("Initializing database schema from Python definitions...")
            for table in TABLE_LIST:
                # Check if it already exists
                if not self._object_exists(table.name, "table"):
                    create_table_sql = table.generate_create_table_sql()
                    logger.debug(f"Creating [{table.name}] using the following SQL query : \n{create_table_sql}")
                    cursor.execute(create_table_sql)
                    logger.debug(f"[{table.name}] created")

                # Create indexes
                for index in table.indexes:
                    if not self._object_exists(index["name"], "index"):
                        generated_index_sql = table.generate_create_index_sql(index)
                        logger.debug(
                            f"Creating index for [{table.name}] using the following SQL query : {generated_index_sql}")
                        cursor.execute(generated_index_sql)
                        logger.debug(f'[{index["name"]}] created')

            conn.commit()
            logger.info(f"Database schema initialized successfully at: {self._db_path}")
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")

    def insert_new_play_data(self, data: PlayData) -> bool:
        conn = self._get_active_connection()
        try:
            cursor = conn.cursor()

            data_dict = asdict(data)

            columns = ', '.join(data_dict.keys())
            placeholders = ', '.join(['?' for _ in data_dict.values()])
            sql = f"INSERT INTO play_data ({columns}) VALUES ({placeholders})"
            logging.debug(f"Inserting new [play_data] using the following SQL query : \n{sql}")
            cursor.execute(sql, tuple(data_dict.values()))
            conn.commit()
            logger.info(f"Successfully inserted [play_data] with idx: {data_dict.get('idx')}")
            return True
        except sqlite3.IntegrityError as e:
            logger.error(f'Error when inserting data into [play_data] with idx: "{data.idx}" due to {e}')
            return False
        except sqlite3.Error as e:
            logger.error(f"Error inserting play data: {e}")
            return False

    def check_if_play_data_exists(self, idx: str) -> bool:
        """
        Checks if a play data record with the given 'idx' already exists in the 'play_data' table,
        using the persistent connection.

        Args:
            idx (str): The unique identifier for the play data.

        Returns:
            bool: True if the record exists, False otherwise.
        """
        conn = self._get_active_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM play_data WHERE idx = ?", (idx,))
            result = cursor.fetchone()
            return result is not None
        except sqlite3.Error as e:
            logger.error(f"Error checking play data existence: {e}")
            return False

    def get_db_path_string(self) -> str:
        """
        Returns the full absolute path to the database file.

        Returns:
            str: The database file path.
        """
        return self._db_path
