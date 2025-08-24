class Messages:
    class Error:
        SERVER_UNDER_MAINTENANCE = "server_under_maintenance"
        UNEXPECTED_ERROR = "unexpected_error"
        CHROME_NOT_FOUND = "chrome_not_found"
        NO_DATA = "no_data"

    class Client:
        WELCOME = "welcome"
        GOODBYE = "goodbye"

    # Translations
    class EN:
        server_under_maintenance = "Server under maintenance"
        unexpected_error = "Unexpected error occurred"
        chrome_not_found = "Chrome not found on this machine."
        no_data = "No data found"
        welcome = "Welcome!"
        goodbye = "Goodbye!"

    class JA:
        server_under_maintenance = "メンテナンス中です"
        chrome_not_found = "このマシンにChromeが見つかりません。"
        no_data = "データが見つかりません"
        welcome = "スクレイパーへようこそ！"
        goodbye = "さようなら！"
