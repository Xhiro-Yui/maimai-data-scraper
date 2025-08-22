import os
import sys


def get_driver_path_folder():
    if getattr(sys, 'frozen', False):
        # Compiled exe → stay next to exe
        base_path = os.path.dirname(sys.executable)
        app_folder = os.path.join(base_path, "application")
    else:
        # Dev mode → one folder up
        base_path = os.path.dirname(os.path.abspath(__file__))
        app_folder = os.path.abspath(os.path.join(base_path, "../../application"))

    os.makedirs(app_folder, exist_ok=True)
    return app_folder
