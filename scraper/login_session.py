import requests


def get_requests_session_from_driver(driver):
    session = requests.Session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie['name'], cookie['value'])
    session.headers.update({
        "User-Agent": driver.execute_script("return navigator.userAgent;")
    })
    return session
