import time

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def get_requests_session_from_driver(driver):
    session = requests.Session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie['name'], cookie['value'])
    session.headers.update({
        "User-Agent": driver.execute_script("return navigator.userAgent;")
    })
    return session


def login(driver, config):
    driver.get("https://maimaidx-eng.com/maimai-mobile/login/")
    wait_delay = config.get("UI_WAIT_DELAY", 10)
    wait_timeout = config.get("UI_WAIT_TIMEOUT", 60)
    print(f"Wait delay : {wait_delay} | wait timeout : {wait_timeout}")

    print("Clicking the TOS checkbox...")
    # Check the TOS checkbox
    tos_checkbox = WebDriverWait(driver, wait_timeout).until(
        EC.element_to_be_clickable((By.ID, "agree-maimaidxex"))
    )
    tos_checkbox.click()
    time.sleep(wait_delay / 4)

    print("Clicking the SEGA ID login button...")
    # Click the SEGA ID login button
    segaid_button = WebDriverWait(driver, wait_timeout).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "c-button--openid--segaId"))
    )
    segaid_button.click()
    time.sleep(wait_delay)

    print("Looking for the login id and password area...")
    # Wait for hidden form to show
    WebDriverWait(driver, wait_timeout).until(
        EC.visibility_of_element_located((By.ID, "sid"))
    )
    time.sleep(wait_delay)
    WebDriverWait(driver, wait_timeout).until(
        EC.visibility_of_element_located((By.ID, "password"))
    )

    print("Inputting login id and password ...")
    driver.find_element(By.ID, "sid").clear()
    driver.find_element(By.ID, "sid").send_keys(config.get("USERNAME", ""))
    time.sleep(wait_delay / 4)
    driver.find_element(By.ID, "password").clear()
    driver.find_element(By.ID, "password").send_keys(config.get("PASSWORD", ""))
    time.sleep(wait_delay / 4)

    driver.find_element(By.ID, "btnSubmit").click()

    # Wait for successful login (redirect to home)
    WebDriverWait(driver, wait_timeout).until(
        EC.url_contains("/maimai-mobile/home/")
    )
    print("Login successful!")
