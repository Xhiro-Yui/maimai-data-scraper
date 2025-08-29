import logging
import sqlite3
from dataclasses import asdict, is_dataclass
from typing import Optional, Any, Union

from scraper.exception.scraper_exception import ScraperError
from scraper.resources.database_schema import TABLE_LIST, Table
from scraper.resources.models import PlayData, SongData
from scraper.utils.path_resolver import resolve_app_file_path

logger = logging.getLogger(__name__.split(".")[-1])


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

        logger.info(f"Initializing database schemas for {self._db_path}")
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
            logger.debug(f"Inserting new [play_data] using the following SQL query : \n{sql}")
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

    def insert(self, table: Table, entity: Any) -> bool:
        """
        Generic insert function for any dataclass-based entity.

        Args:
            table (Table): Table definition (with name and columns)
            entity (dataclass): The dataclass instance representing a row

        Returns:
            bool: True if insert succeeded, False otherwise
        """
        if not is_dataclass(entity):
            raise TypeError("Entity must be a dataclass instance")

        conn = self._get_active_connection()
        try:
            cursor = conn.cursor()

            # Convert dataclass -> dict
            data_dict = asdict(entity)

            # Keep only valid table columns
            valid_columns = [col.name for col in table.columns if not col.primary_key or not col.autoincrement]
            filtered_data = {k: v for k, v in data_dict.items() if k in valid_columns}

            # Build SQL
            columns = ', '.join(filtered_data.keys())
            placeholders = ', '.join(['?' for _ in filtered_data])
            sql = f"INSERT INTO {table.name} ({columns}) VALUES ({placeholders})"

            logger.debug(f"Inserting into [{table.name}] using query:\n{sql}\nValues: {tuple(filtered_data.values())}")
            cursor.execute(sql, tuple(filtered_data.values()))
            conn.commit()

            logger.info(f"Successfully inserted into [{table.name}]")
            return True
        except sqlite3.IntegrityError as e:
            logger.error(f"Integrity error inserting into [{table.name}] with {entity} due to {e}")
            return False
        except sqlite3.Error as e:
            logger.error(f"SQLite error inserting into [{table.name}]: {e}")
            return False

    from typing import Optional

    from typing import Any

    def upsert(self, table: Table, entity: Any) -> Any:
        """
        Generic upsert method for any dataclass-based entity.
        Assumes every table has an auto-increment 'id' primary key.
        Automatically merges partial updates with existing data.

        Args:
            table (Table): Table definition
            entity (dataclass): Entity to insert or update (partial fields allowed)

        Returns:
            dataclass: The inserted/updated entity with auto-generated PK updated
        """
        if not is_dataclass(entity):
            raise TypeError("Entity must be a dataclass instance")

        entity_dict = asdict(entity)
        conn = self._get_active_connection()
        cursor = conn.cursor()

        # Check if the entity exists based on the id
        entity_id = entity_dict.get("id")
        if entity_id is not None:
            sql_check = f"SELECT * FROM {table.name} WHERE id=? LIMIT 1"
            cursor.execute(sql_check, (entity_id,))
            row = cursor.fetchone()
            if row:
                # Convert row to dict for merging
                existing_dict = dict(row)
                # Merge: keep existing values for fields that are None in entity
                merged_dict = {k: entity_dict[k] if entity_dict[k] is not None else existing_dict[k]
                               for k in existing_dict.keys()}

                # Update the database with merged_dict
                update_fields = {k: v for k, v in merged_dict.items() if k != "id"}
                if update_fields:
                    set_clause = ', '.join(f"{col}=?" for col in update_fields)
                    sql_update = f"UPDATE {table.name} SET {set_clause} WHERE id=?"
                    values = list(update_fields.values()) + [entity_id]
                    cursor.execute(sql_update, tuple(values))
                    conn.commit()

                # Return merged entity as dataclass
                return type(entity)(**merged_dict)

        # If entity_id is None or row doesn't exist, try to find by natural key (optional)
        # Here we assume id is the only key; for other key strategies, modify accordingly

        # Insert new row
        insert_columns = [k for k in entity_dict.keys() if k != "id"]
        insert_values = [v for k, v in entity_dict.items() if k != "id"]
        columns_str = ', '.join(insert_columns)
        placeholders = ', '.join(['?'] * len(insert_columns))
        sql_insert = f"INSERT INTO {table.name} ({columns_str}) VALUES ({placeholders})"
        cursor.execute(sql_insert, tuple(insert_values))
        conn.commit()

        # Update entity's id with lastrowid
        entity.id = cursor.lastrowid
        return entity

    def update(self, table: Table, entity: Any) -> bool:
        pass
        # if not is_dataclass(entity):
        #     raise TypeError("Entity must be a dataclass instance")
        #
        # entity_dict = asdict(entity)
        # conn = self._get_active_connection()
        # cursor = conn.cursor()
        #
        # # Check if the entity exists based on the id
        # entity_id = entity_dict.get("id")
        # if entity_id is not None:
        #     sql_check = f"SELECT * FROM {table.name} WHERE id=? LIMIT 1"
        #     cursor.execute(sql_check, (entity_id,))
        #     row = cursor.fetchone()
        #     if row:
        #         # Convert row to dict for merging
        #         existing_dict = dict(row)
        #         # Merge: keep existing values for fields that are None in entity
        #         merged_dict = {k: entity_dict[k] if entity_dict[k] is not None else existing_dict[k]
        #                        for k in existing_dict.keys()}
        #
        #         # Update the database with merged_dict
        #         update_fields = {k: v for k, v in merged_dict.items() if k != "id"}
        #         if update_fields:
        #             set_clause = ', '.join(f"{col}=?" for col in update_fields)
        #             sql_update = f"UPDATE {table.name} SET {set_clause} WHERE id=?"
        #             values = list(update_fields.values()) + [entity_id]
        #             cursor.execute(sql_update, tuple(values))
        #             conn.commit()
        #
        #         # Return merged entity as dataclass
        #         return type(entity)(**merged_dict)
        #
        # # If entity_id is None or row doesn't exist, try to find by natural key (optional)
        # # Here we assume id is the only key; for other key strategies, modify accordingly
        #
        # # Insert new row
        # insert_columns = [k for k in entity_dict.keys() if k != "id"]
        # insert_values = [v for k, v in entity_dict.items() if k != "id"]
        # columns_str = ', '.join(insert_columns)
        # placeholders = ', '.join(['?'] * len(insert_columns))
        # sql_insert = f"INSERT INTO {table.name} ({columns_str}) VALUES ({placeholders})"
        # cursor.execute(sql_insert, tuple(insert_values))
        # conn.commit()
        #
        # # Update entity's id with lastrowid
        # entity.id = cursor.lastrowid
        # return entity

    def select(
            self,
            table: Table,
            filters: Optional[Any] = None,
            entity_class: Optional[type] = None,
            limit: Optional[int] = 1,
    ) -> Union[Optional[Any], list[Any]]:
        """
        Run a SELECT query on the given table.

        Args:
            table (Table): Table definition.
            filters (dict or dataclass, optional): Filter conditions. If None, selects all rows.
            entity_class (type, optional): Dataclass to map results into. If None, returns dicts.
            limit (int or None, optional):
                - 1 (default): return a single row or None
                - >1: return a list of up to that many rows
                - None: return all matching rows

        Returns:
            dict or dataclass instance if limit=1,
            otherwise a list of dicts or dataclass instances.
        """
        # Convert dataclass filters to dict
        if filters is None:
            filters = {}
        elif is_dataclass(filters):
            filters = asdict(filters)
        elif not isinstance(filters, dict):
            raise TypeError("filters must be a dataclass, dict, or None")

        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}

        conn = self._get_active_connection()
        try:
            cursor = conn.cursor()

            # Keep only valid table columns
            valid_columns = {col.name for col in table.columns}
            filtered_columns = {k: v for k, v in filters.items() if k in valid_columns}

            # Build SQL and parameters
            if filtered_columns:
                where_clause = ' AND '.join(f"{col}=?" for col in filtered_columns)
                sql = f"SELECT * FROM {table.name} WHERE {where_clause}"
                params = tuple(filtered_columns.values())
            else:
                sql = f"SELECT * FROM {table.name}"
                params = ()

            if isinstance(limit, int) and limit > 0:
                sql += f" LIMIT {limit}"

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            results = []
            for row in rows:
                row_dict = dict(row)
                results.append(
                    entity_class(**row_dict) if entity_class and is_dataclass(entity_class) else row_dict
                )

            # Return based on limit
            if limit == 1:
                return results[0] if results else None
            else:
                return results

        except sqlite3.Error as e:
            logger.error(f"Error fetching row(s) from [{table.name}]: {e}")
            return [] if limit != 1 else None

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

    def get_song_data(self, song_title: str, song_type: str) -> Optional[SongData]:
        """
        Fetch a play data record with the given song_title and song_type.

        Args:
            song_title (str): Song title
            song_type (str): Normal or DX chart

        Returns:
            dict | None: The row as a dict if found, otherwise None.
        """
        conn = self._get_active_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM song_data WHERE song_title = ? AND song_type = ?",
                (song_title, song_type),
            )
            row = cursor.fetchone()
            if row:
                return SongData(**dict(row))  # unpack into dataclass
            return None
        except sqlite3.Error as e:
            logger.error(f"Error fetching song data: {e}")
            return None

    def get_db_path_string(self) -> str:
        """
        Returns the full absolute path to the database file.

        Returns:
            str: The database file path.
        """
        return self._db_path
