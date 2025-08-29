from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class Column:
    """Represents a database column with its properties."""
    name: str
    data_type: str
    primary_key: bool = False
    unique: bool = False
    autoincrement: bool = False
    nullable: bool = True  # True = NULL, False = NOT NULL

    def to_sql_definition(self) -> str:
        """Generates the SQL definition for the column."""
        parts = [self.name, self.data_type.upper()]
        if self.primary_key:
            parts.append("PRIMARY KEY")
        if self.autoincrement:
            parts.append("AUTOINCREMENT")
        if self.unique and not self.primary_key:
            parts.append("UNIQUE")
        if not self.nullable and not self.primary_key:
            parts.append("NOT NULL")
        return " ".join(parts)


@dataclass
class Table:
    """Represents a database table with its columns and indexes."""
    name: str
    columns: list[Column]
    # Indexes are defined as a list of dictionaries for flexibility
    # Each dict can contain 'name' (str), 'columns' (List[str]), 'unique' (bool)
    indexes: list[Dict[str, Any]] = field(default_factory=list)

    def generate_create_table_sql(self) -> str:
        """Generates the CREATE TABLE SQL statement for this table."""
        column_definitions = [col.to_sql_definition() for col in self.columns]
        return f"CREATE TABLE IF NOT EXISTS {self.name} (\n    " + \
            ",\n    ".join(column_definitions) + "\n);"

    def generate_create_index_sql(self, index_def: dict) -> str:
        """Generates CREATE INDEX SQL statements for given index object on this table."""
        index_name = index_def["name"]
        index_columns = ", ".join(index_def["columns"])
        unique_keyword = "UNIQUE " if index_def.get("unique", False) else ""
        return f"CREATE {unique_keyword}INDEX IF NOT EXISTS {index_name} ON {self.name}({index_columns});"


# === Tables ===

PLAY_DATA_TABLE = Table(
    name="play_data",
    columns=[
        # Creating an ID anyway cause IDX sorting is unusable due to its format
        Column("id", "INTEGER", primary_key=True, autoincrement=True),
        Column("idx", "TEXT", unique=True, nullable=False),
        Column("title", "TEXT", nullable=False),
        Column("difficulty", "TEXT", nullable=False),
        Column("track", "TEXT"),
        Column("music_type", "TEXT"),
        Column("new_achievement", "BOOLEAN"),
        Column("achievement", "TEXT"),
        Column("rank", "TEXT"),
        Column("new_dx_score", "BOOLEAN"),
        Column("dx_score", "TEXT"),
        Column("dx_stars", "INTEGER"),
        Column("combo_status", "TEXT"),
        Column("sync_status", "TEXT"),
        Column("place", "TEXT"),
        Column("played_at", "TEXT"),
        Column("fast", "INTEGER"),
        Column("late", "INTEGER"),
        Column("tap_detail", "TEXT"),
        Column("hold_detail", "TEXT"),
        Column("slide_detail", "TEXT"),
        Column("touch_detail", "TEXT"),
        Column("break_detail", "TEXT"),
        Column("max_combo", "TEXT"),
        Column("max_sync", "TEXT"),
        Column("play_data_version", "TEXT")  # Internal scraper use to handle website changes
    ],
    indexes=[
        {"name": "idx_play_data_idx", "columns": ["idx"], "unique": True}  # Explicit unique index
    ]
)

PLAYER_DATA_TABLE = Table(
    name="player_data",
    columns=[
        Column("id", "INTEGER", primary_key=True, autoincrement=True),
        Column("total_plays", "INTEGER", nullable=False),
    ]
)

SONG_DATA_TABLE = Table(
    name="song_data",
    columns=[
        Column("id", "INTEGER", primary_key=True, autoincrement=True),
        Column("song_title", "TEXT", nullable=False),
        Column("song_type", "TEXT", nullable=False),
        Column("score_basic", "TEXT"),
        Column("dx_score_basic", "TEXT"),
        Column("score_advanced", "TEXT"),
        Column("dx_score_advanced", "TEXT"),
        Column("score_expert", "TEXT"),
        Column("dx_score_expert", "TEXT"),
        Column("score_master", "TEXT"),
        Column("dx_score_master", "TEXT"),
        Column("score_remaster", "TEXT"),
        Column("dx_score_remaster", "TEXT"),
    ]
)

METADATA_TABLE = Table(
    name="metadata",
    columns=[
        Column("id", "INTEGER", primary_key=True),
        Column("scraper_version", "TEXT", nullable=False),
        Column("database_version", "TEXT", nullable=False),
        Column("play_data_version", "TEXT", nullable=False),
    ]
)

TABLE_LIST: list[Table] = [PLAY_DATA_TABLE, PLAYER_DATA_TABLE, SONG_DATA_TABLE, METADATA_TABLE]
