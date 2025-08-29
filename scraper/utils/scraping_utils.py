import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

logger = logging.getLogger(__name__.split(".")[-1])

COMBO_MAP = {
    "fc_dummy.png": None,
    "fc.png": "FC",
    "fcplus.png": "FC+",
    "ap.png": "AP",
    "applus.png": "AP+",
}

SYNC_MAP = {
    "sync_dummy.png": None,
    "sync.png": "Sync",
    "fs.png": "FS",
    "fsplus.png": "FS+",
    "fd.png": "FD",  # placeholder (unknown actual filename)
    "fdplus.png": "FD+",  # placeholder (unknown actual filename)
}

RANK_MAP = {
    "d.png": "D",
    "c.png": "C",
    "b.png": "B",
    "a.png": "A",
    "aa.png": "AA",
    "aaa.png": "AAA",
    "s.png": "S",
    "splus.png": "S+",
    "ss.png": "SS",
    "ssplus.png": "SS+",
    "sss.png": "SSS",
    "sssplus.png": "SSS+",
}


def identify_song_type(song_icon_src: str) -> str:
    if song_icon_src.__contains__("music_dx.png"):
        return "dx"
    elif song_icon_src.__contains__("music_standard.png"):
        return "standard"
    else:
        return "unknown"


def find_element_attribute(container, by, selector, attr="text", index: int = 0) -> str | None:
    """Safely find an element and return an attribute or text, with logging.

    Args:
        container: The Selenium element to search within.
        by: The Selenium locator strategy (By.CSS_SELECTOR, By.XPATH, etc.).
        selector: The selector string.
        attr: "text" for .text, or an attribute name for .get_attribute(attr).
        index: Which element in the list to pick (default=0, supports negative indices).

    Returns:
        The attribute value, text, or None if not found.
    """
    try:
        elements = container.find_elements(by, selector)
    except Exception as e:
        logger.debug("find_element_attribute :: Error finding elements (by=%s, selector=%s): %s", by, selector, e)
        return None

    if not elements:
        logger.debug("find_element_attribute :: No elements found (by=%s, selector=%s)", by, selector)
        return None

    # Handle index safely
    try:
        el = elements[index]
    except IndexError:
        logger.debug("find_element_attribute :: Index %s out of range for elements (found=%s, by=%s, selector=%s)",
                     index, len(elements), by, selector)
        return None

    try:
        if attr == "text":
            value = el.text.strip()
        else:
            value = el.get_attribute(attr)

        if value is None or value == "":
            logger.debug("find_element_attribute :: Empty value for attr='%s' (by=%s, selector=%s, index=%s)",
                         attr, by, selector, index)
        else:
            logger.debug("find_element_attribute :: Found attr='%s' value='%s' (by=%s, selector=%s, index=%s)",
                         attr, value, by, selector, index)

        return value
    except Exception as e:
        logger.debug(
            "find_element_attribute :: Error getting attr='%s' from element (by=%s, selector=%s, index=%s): %s",
            attr, by, selector, index, e)
        return None


def parse_song_title(element: WebElement) -> str:
    full_text = element.text.strip()
    children_text = " ".join([child.text for child in element.find_elements(By.XPATH, "./*")])
    return full_text.replace(children_text, "").strip()


def parse_chart_type(chart_type_image: str) -> str:
    if "music_dx.png" in chart_type_image:
        return "dx"
    elif "music_standard.png" in chart_type_image:
        return "standard"
    else:
        return "unknown"


def parse_placement(placement_dom: list[WebElement]) -> str | None:
    if placement_dom:
        icon_src = placement_dom[0].get_attribute("src")
        return icon_src.split("/")[-1].replace(".png", "")
    else:
        return None


def parse_dx_stars(dx_stars_image: str) -> int:
    if not dx_stars_image:  # covers None or empty string
        return 0
    elif "dxstar_1.png" in dx_stars_image:
        return 1
    elif "dxstar_2.png" in dx_stars_image:
        return 2
    elif "dxstar_3.png" in dx_stars_image:
        return 3
    elif "dxstar_4.png" in dx_stars_image:
        return 4
    elif "dxstar_5.png" in dx_stars_image:
        return 5
    else:
        return 0


def parse_rank(rank_image: str) -> str:
    filename = rank_image.split("/")[-1].split("?")[0]
    return RANK_MAP.get(filename.lower())


def parse_combo(combo_image: str) -> str | None:
    if not combo_image:
        return None
    filename = combo_image.split("/")[-1].split("?")[0]
    return COMBO_MAP.get(filename.lower())


def parse_sync(sync_image: str) -> str | None:
    if not sync_image:
        return None
    filename = sync_image.split("/")[-1].split("?")[0]
    return SYNC_MAP.get(filename.lower())
