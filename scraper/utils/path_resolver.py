import os
import sys


def resolve_app_file_path(filename: str, app_data_dir_name: str = "application") -> str:
    """
    Determines the full absolute path to a given application-specific file,
    based on whether the application is frozen (compiled executable) or
    running in development mode.

    Args:
        filename (str): The name of the file to resolve
        app_data_dir_name (str): The name of the directory where application data files
                                 should be stored, relative to the executable or project root.

    Returns:
        str: The absolute path to the specified application file.
    """
    app_folder: str

    if getattr(sys, 'frozen', False):
        # Running as a compiled executable (e.g., PyInstaller)
        # Files are expected to be next to the executable, within the app_data_dir_name folder.
        base_path = os.path.dirname(sys.executable)
        app_folder = os.path.join(base_path, app_data_dir_name)
    else:
        # Running in development mode (e.g., from PyCharm)
        # Assumes the script calling this is run from the project root (maimai-data-scraper/).
        # Files are then expected at ./application/<filename> relative to the project root.
        # sys.modules['__main__'].__file__ reliably gives the path of the main script executed.
        main_script_path = os.path.abspath(sys.modules['__main__'].__file__)
        project_root = os.path.dirname(main_script_path)
        app_folder = os.path.abspath(os.path.join(project_root, app_data_dir_name))

    # Ensure the target directory exists before returning the path
    os.makedirs(app_folder, exist_ok=True)
    return os.path.join(app_folder, filename)
