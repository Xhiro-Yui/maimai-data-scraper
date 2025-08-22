import re
import sys
import time
import random

from bs4 import BeautifulSoup
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from scraper.login_session import get_requests_session_from_driver, login
from scraper.setup import get_connection


def browser_scrape(config, driver):
    print("Browser scraping start!")
    start(config, driver)


def start(config, driver):

    try:
        login(driver, config)
    except TimeoutException:
        print("❌ Login timed out — check your credentials and internet connection.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error during login: {e}")
        sys.exit(1)

    session = get_requests_session_from_driver(driver)
    interval = int(config.get("CHECK_INTERVAL_MINUTES", 5))
    while True:
        conn = get_connection()
        scrape_playlogs(driver, session, conn)

        # Only navigate back if not already on the correct page
        current_url = driver.current_url
        target_url = "https://maimaidx-eng.com/maimai-mobile/record/"
        if current_url != target_url:
            driver.get(target_url)
            time.sleep(1)

        # Inject countdown popup
        seconds_remaining = interval * 60

        countdown_script = f'''
        (function() {{
            let countdownBox = document.getElementById('countdown-box');
            if (!countdownBox) {{
                countdownBox = document.createElement('div');
                countdownBox.id = 'countdown-box';
                countdownBox.style.position = 'fixed';
                countdownBox.style.top = '10px';
                countdownBox.style.right = '10px';
                countdownBox.style.padding = '10px 15px';
                countdownBox.style.background = 'rgba(0,0,0,0.7)';
                countdownBox.style.color = 'white';
                countdownBox.style.fontSize = '16px';
                countdownBox.style.borderRadius = '8px';
                countdownBox.style.zIndex = 9999;
                countdownBox.style.cursor = 'move';
                countdownBox.innerText = 'Next check in...';
                document.body.appendChild(countdownBox);

                // Make draggable
                let offsetX = 0, offsetY = 0, isDragging = false;

                countdownBox.addEventListener('mousedown', function(e) {{
                    isDragging = true;
                    offsetX = e.clientX - countdownBox.getBoundingClientRect().left;
                    offsetY = e.clientY - countdownBox.getBoundingClientRect().top;
                    countdownBox.style.transition = 'none';
                }});

                document.addEventListener('mousemove', function(e) {{
                    if (isDragging) {{
                        countdownBox.style.left = (e.clientX - offsetX) + 'px';
                        countdownBox.style.top = (e.clientY - offsetY) + 'px';
                        countdownBox.style.right = 'auto';
                    }}
                }});

                document.addEventListener('mouseup', function() {{
                    isDragging = false;
                }});
            }}

            let seconds = {interval * 60};
            countdownBox.innerText = `Next check in ${'{'}seconds{'}'}s`;
            const intervalId = setInterval(() => {{
                seconds--;
                if (seconds <= 0) {{
                    clearInterval(intervalId);
                    countdownBox.remove();
                }} else {{
                    countdownBox.innerText = `Next check in ${'{'}seconds{'}'}s`;
                }}
            }}, 1000);
        }})();
        '''

        driver.execute_script(countdown_script)

        print(f"⏳ Waiting {interval} minutes before next check...")
        time.sleep(interval * 60)


def scrape_playlogs(driver, session, conn):
    cursor = conn.cursor()

    driver.get("https://maimaidx-eng.com/maimai-mobile/record/")
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Step 1: Extract all idx values from the page
    wrappers = soup.select("div.p_10")
    page_idxs = []
    playlog_wrappers = {}

    for wrapper in wrappers:
        idx_tag = wrapper.select_one("input[name='idx']")
        if not idx_tag:
            continue
        idx = idx_tag["value"]
        page_idxs.append(idx)
        playlog_wrappers[idx] = wrapper

    if not page_idxs:
        print("⚠️ No playlogs found on the page.")
        return

    # Step 2: Check which idx already exist in DB
    placeholders = ",".join(["?"] * len(page_idxs))
    cursor.execute(f"SELECT idx FROM play_data WHERE idx IN ({placeholders})", page_idxs)
    existing_idxs = set(row[0] for row in cursor.fetchall())

    # Step 3: Filter only new playlogs
    new_playlogs = [(idx, playlog_wrappers[idx]) for idx in page_idxs if idx not in existing_idxs]

    for idx, wrapper in new_playlogs:
        title = wrapper.select_one(".basic_block").text.strip()
        date_info = wrapper.select_one(".sub_title span:nth-of-type(2)").text.strip()
        track = wrapper.select_one(".sub_title span:nth-of-type(1)").text.strip()
        place = track if "TRACK" not in track.upper() else None
        if place is None:
            place_tag = wrapper.select_one(".playlog_result_innerblock .playlog_matching_icon")
            if place_tag:
                src = place_tag.get("src", '')
                for p in ["1st", "2nd", "3rd", "4th"]:
                    if p in src:
                        place = p
                        break

        difficulty_img = wrapper.select_one(".playlog_diff")
        difficulty = difficulty_img["src"].split("/")[-1].replace("diff_", "").replace(".png", "")

        music_icon = wrapper.select_one("img.playlog_music_kind_icon")
        if music_icon:
            src = music_icon.get("src", "")
            if "music_dx.png" in src:
                music_type = "dx"
            elif "music_standard.png" in src:
                music_type = "standard"
            else:
                music_type = None
        else:
            music_type = None

        achievement = wrapper.select_one(".playlog_achievement_txt").text.strip()
        score = wrapper.select_one(".white.f_15").text.strip()

        dx_stars = None  # default to None in case scraping fails
        try:
            star_img = wrapper.select_one("img.playlog_deluxscore_star")
            if star_img:
                match = re.search(r"dxstar_(\d)", star_img.get("src", ""))
                if match:
                    dx_stars = int(match.group(1))
                else:
                    dx_stars = 0
            else:
                dx_stars = 0
        except Exception as e:
            print(f"⚠️ Failed to detect dx_stars for idx {idx}: {e}")

        rank_img = wrapper.select_one(".playlog_scorerank")
        rank = rank_img["src"].split("/")[-1].split(".")[0] if rank_img else ""

        fc_status = "error"
        try:
            fc_imgs = wrapper.select("div.playlog_result_innerblock > img[src*='/playlog/']")
            for img in fc_imgs:
                src = img.get("src", "")
                filename = src.split("/")[-1].split("?")[0]  # e.g. 'applus.png'
                if "_dummy" in filename:
                    continue
                if filename.startswith(("fc", "ap")):
                    fc_status = filename.replace(".png", "")
                    break
            else:
                fc_status = "none"
        except Exception as e:
            print(f"❌ Failed to extract fc_status for idx {idx}: {e}")

        sync_status = "error"
        try:
            sync_img = wrapper.select_one("img[src*='playlog/sync']")
            if sync_img:
                src = sync_img["src"]
                filename = src.split("/")[-1].split("?")[0]
                if "dummy" in filename:
                    sync_status = "none"
                else:
                    sync_status = filename.replace(".png", "")
            else:
                sync_status = "none"
        except Exception as e:
            print(f"❌ Failed to extract sync_status for idx {idx}: {e}")

        cursor.execute("""
        INSERT INTO play_data (
            idx, title, difficulty, music_type, track, place, played_at,
            achievement, score, dx_stars, rank, fc_status, sync_status,
            max_combo, max_sync, fast, late,
            tap_detail, hold_detail, slide_detail, touch_detail, break_detail,
            new_achievement, new_dx_score
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?, ?,
            ?, ?
        )
        """, (
            idx, title, difficulty, music_type, track, place, date_info,
            achievement, score, dx_stars, rank, fc_status, sync_status,
            None, None, 0, 0,
            None, None, None, None, None,
            False, False
        ))

        detail_url = f"https://maimaidx-eng.com/maimai-mobile/record/playlogDetail/?idx={idx}"
        try:
            time.sleep(5 + random.randint(5, 30)) # Forcefully waits between songs to not be so bot-like
            driver.get(detail_url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "playlog_notes_detail"))
            )
            detail_soup = BeautifulSoup(driver.page_source, "html.parser")

            max_combo = None
            max_sync = None
            fast = 0
            late = 0

            score_blocks = detail_soup.select(".playlog_score_block")
            for block in score_blocks:
                img = block.select_one("img")
                value = block.select_one(".white")
                if img and value:
                    src = img.get("src", "")
                    text = value.text.strip()
                    if "maxcombo.png" in src:
                        max_combo = text
                    elif "maxsync.png" in src:
                        max_sync = text

            timing_blocks = detail_soup.select(".w_96.f_l.t_r")
            for block in timing_blocks:
                img = block.select_one("img")
                value_div = block.select_one("div")
                if img and value_div:
                    src = img.get("src", "")
                    value = value_div.text.strip()
                    if "fast.png" in src:
                        fast = int(value) if value.isdigit() else 0
                    elif "late.png" in src:
                        late = int(value) if value.isdigit() else 0

            note_details = {"tap": None, "hold": None, "slide": None, "touch": None, "break": None}
            notes_table = detail_soup.select_one("table.playlog_notes_detail")
            if notes_table:
                rows = notes_table.select("tr")[1:]
                for row in rows:
                    img = row.select_one("th img")
                    if not img:
                        continue
                    src = img.get("src", "")
                    label = None
                    for note_type in note_details:
                        if f"{note_type}.png" in src:
                            label = note_type
                            break
                    if not label:
                        continue
                    values = [td.text.strip() for td in row.select("td")]
                    note_details[label] = " / ".join(values)

            new_achievement = bool(detail_soup.select_one("img.playlog_achievement_newrecord"))
            new_dx_score = bool(detail_soup.select_one("img.playlog_deluxscore_newrecord"))

            cursor.execute("""
            UPDATE play_data SET
                max_combo = ?, max_sync = ?, fast = ?, late = ?,
                tap_detail = ?, hold_detail = ?, slide_detail = ?, touch_detail = ?, break_detail = ?,
                new_achievement = ?, new_dx_score = ?
            WHERE idx = ?
            """, (
                max_combo, max_sync, fast, late,
                note_details["tap"], note_details["hold"], note_details["slide"],
                note_details["touch"], note_details["break"],
                new_achievement, new_dx_score,
                idx
            ))
        except Exception as e:
            print(f"❌ Failed to load details for idx {idx}: {e}")

        print(f"✅ Inserted play_data: {idx}")

        conn.commit()
