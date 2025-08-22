import os
import sys
import sqlite3

DEFAULT_CONFIG = """USERNAME=
PASSWORD=
CHECK_INTERVAL_MINUTES=5
BROWSER=

### Do not touch the section below unless you know what you are doing

UI_WAIT_DELAY=10
UI_WAIT_TIMEOUT=60

# These credentials are stored locally only.
# They are never sent anywhere except to log in to maimaidx-eng.com via your own browser.
# BROWSER should be one of the following: chrome, firefox, headless
"""

VALID_BROWSERS = {"chrome", "firefox", "headless"}


def get_app_folder():
    if getattr(sys, 'frozen', False):
        # Compiled exe → stay next to exe
        base_path = os.path.dirname(sys.executable)
        app_folder = os.path.join(base_path, "application")
    else:
        # Dev mode → one folder up
        base_path = os.path.dirname(os.path.abspath(__file__))
        app_folder = os.path.abspath(os.path.join(base_path, "../application"))

    os.makedirs(app_folder, exist_ok=True)
    return app_folder


CONFIG_FILE = os.path.join(get_app_folder(), "config.env")


def ensure_config_exists():
    print("Checking if existing config exists...")
    if not os.path.exists(CONFIG_FILE):
        print("No existing config found. Creating default config file.")
        with open(CONFIG_FILE, "w") as f:
            f.write(DEFAULT_CONFIG)
        print(f"First-time setup: '{os.path.abspath(CONFIG_FILE)}' has been created.")
        print("Please open it and fill in your USERNAME, PASSWORD, and BROWSER.")
        input("Press Enter to exit...")
        sys.exit(0)


def load_config():
    print("Loading config file...")
    config = {}
    with open(CONFIG_FILE, "r") as f:
        for line in f:
            if line.strip().startswith("#") or "=" not in line:
                continue
            key, value = line.strip().split("=", 1)
            config[key.strip().upper()] = value.strip()
    return config
