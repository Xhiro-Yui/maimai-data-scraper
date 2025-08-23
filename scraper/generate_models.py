import os

from scraper.resources.database_schema import TABLE_LIST, Table, Column

SQL_TO_PY = {
    "INTEGER": "int",
    "TEXT": "str",
    "BOOLEAN": "bool",
}


def python_type(col: Column) -> str:
    base = SQL_TO_PY.get(col.data_type.upper(), "str")
    # autoincrement PK or nullable → Optional
    if col.nullable or (col.primary_key and col.autoincrement):
        return f"Optional[{base}]"
    return base


def class_name_from_table(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))


def generate_dataclass_code(table: Table) -> str:
    class_name = class_name_from_table(table.name)

    # Determine if Optional is required in this class
    requires_optional = any(
        col.nullable or (col.primary_key and col.autoincrement)
        for col in table.columns
    )

    lines = ["from dataclasses import dataclass"]
    if requires_optional:
        lines.append("from typing import Optional")

    lines.extend([
        "",
        "",
        "@dataclass",
        f"class {class_name}:"
    ])

    for col in table.columns:
        lines.append(f"    {col.name}: {python_type(col)} = None")

    return "\n".join(lines)


def main():
    models_dir = "scraper/resources/models"
    os.makedirs(models_dir, exist_ok=True)

    # Clean old files
    for filename in os.listdir(models_dir):
        file_path = os.path.join(models_dir, filename)
        if os.path.isfile(file_path):
            print(f"Deleting {file_path}")
            os.remove(file_path)

    init_lines = []

    for table in TABLE_LIST:
        class_name = class_name_from_table(table.name)
        filename = f"{table.name}.py"
        file_path = os.path.join(models_dir, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(generate_dataclass_code(table))
            f.write("\n")

        init_lines.append(f"from .{table.name} import {class_name}")
        print(f"Generated {file_path}")

    # Write __init__.py
    init_path = os.path.join(models_dir, "__init__.py")
    with open(init_path, "w", encoding="utf-8") as f:
        f.write("\n".join(init_lines) + "\n")

    print(f"Generated {init_path}")


if __name__ == "__main__":
    main()
