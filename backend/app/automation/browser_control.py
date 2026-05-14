from typing import Optional
from app.core.logger import logger

_driver = None


def get_driver(headless: bool = False):
    global _driver
    if _driver is None:
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service

            options = Options()
            if headless:
                options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")

            _driver = webdriver.Chrome(options=options)
            logger.info("Chrome WebDriver initialized")
        except Exception as e:
            logger.error(f"WebDriver init error: {e}")
            raise
    return _driver


def close_driver():
    global _driver
    if _driver:
        _driver.quit()
        _driver = None
        logger.info("WebDriver closed")


async def navigate_to(url: str) -> bool:
    try:
        driver = get_driver()
        driver.get(url)
        logger.info(f"Navigated to: {url}")
        return True
    except Exception as e:
        logger.error(f"Navigation error: {e}")
        return False


async def get_page_text() -> str:
    try:
        driver = get_driver()
        return driver.find_element("tag name", "body").text
    except Exception as e:
        logger.error(f"Get page text error: {e}")
        return ""


async def get_page_title() -> str:
    try:
        return get_driver().title
    except Exception:
        return ""


async def click_element_by_text(text: str) -> bool:
    try:
        from selenium.webdriver.common.by import By
        driver = get_driver()
        el = driver.find_element(By.XPATH, f"//*[contains(text(), '{text}')]")
        el.click()
        return True
    except Exception as e:
        logger.error(f"Click element error: {e}")
        return False


async def fill_input(selector: str, value: str, by: str = "css") -> bool:
    try:
        from selenium.webdriver.common.by import By
        driver = get_driver()
        by_map = {"css": By.CSS_SELECTOR, "id": By.ID, "name": By.NAME, "xpath": By.XPATH}
        el = driver.find_element(by_map.get(by, By.CSS_SELECTOR), selector)
        el.clear()
        el.send_keys(value)
        return True
    except Exception as e:
        logger.error(f"Fill input error: {e}")
        return False


async def take_browser_screenshot() -> Optional[bytes]:
    try:
        driver = get_driver()
        return driver.get_screenshot_as_png()
    except Exception as e:
        logger.error(f"Browser screenshot error: {e}")
        return None


async def execute_js(script: str):
    try:
        return get_driver().execute_script(script)
    except Exception as e:
        logger.error(f"JS execution error: {e}")
        return None


async def scrape_page(url: str) -> dict:
    await navigate_to(url)
    import asyncio
    await asyncio.sleep(2)
    return {
        "url": url,
        "title": await get_page_title(),
        "text": await get_page_text(),
    }
