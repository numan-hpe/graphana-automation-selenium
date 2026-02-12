from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from pywinauto import Desktop
import time
import io
from PIL import Image
from config import USER_EMAIL, HEADINGS, SCREENSHOT_DATA

logged_in = False


def wait_for_window(title_pattern, timeout=30):
    """
    Wait for a window matching the title pattern to appear within a timeout.
    """
    print(f"Waiting for window: '{title_pattern}'")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Check for the window on the desktop
            window = Desktop(backend="uia").window(title_re=title_pattern)
            if window.exists():
                return window
        except Exception:
            pass
    raise Exception(f"Timeout: Window '{title_pattern}' did not appear.")


def login_user(driver):
    global logged_in
    login_timeout = 180  # Maximum time to wait for login (in seconds)

    WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//a[@href='login/azuread']"))
    ).click()

    if not logged_in:
        try:
            WebDriverWait(driver, login_timeout).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@type='email']"))
            ).send_keys(USER_EMAIL)

            driver.find_element(By.XPATH, "//input[@type='submit']").click()
            time.sleep(3)
            WebDriverWait(driver, login_timeout).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))
            ).click()

            WebDriverWait(driver, login_timeout).until(
                lambda driver: "rugby-daily-check-engine-light" in driver.current_url
            )
            logged_in = True
            print("Login successful!")
        except Exception as e:
            print("Login failed: ", e)
            raise e


def wait_for_widgets_to_load(driver, max_timeout=180):
    # expand_all_tabs(driver)
    WebDriverWait(driver, max_timeout).until(
        lambda driver: len(
            driver.find_elements(By.XPATH, "//div[@aria-label='Panel loading bar']")
        )
        == 0
    )


def scroll_to_widget(driver, heading=None, xpath=None):
    print(f"Scrolling to widget: '{heading or xpath}'")
    xpath = xpath or f"//*[contains(text(), '{heading}')]"
    attempts = 0
    try:
        page = driver.find_element(By.ID, "page-scrollbar")
    except NoSuchElementException:
        page = None

    try:
        while attempts < 20:
            elements = driver.find_elements(By.XPATH, xpath)
            if elements:
                print(f"Found widget: '{heading or xpath}'")
                break
            if page:
                driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollTop + 300", page
                )
            else:
                driver.execute_script("window.scrollBy(0, 300)")
            time.sleep(0.5)
            attempts += 1
        widget = driver.find_element(By.XPATH, xpath)
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", widget)
        if page:
            driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollTop - 100", page
            )
        else:
            driver.execute_script("window.scrollBy(0, -100)")
        time.sleep(0.5)
        wait_for_widgets_to_load(driver)
    except Exception as e:
        print(f"\033[91mCould not scroll to widget {heading or xpath}: {e}\033[0m")


def get_value(driver, header, region=None):
    xpath = f"//section[contains(@data-testid,'{header}')]//div[@title]"
    if header == HEADINGS["websockets"] and region == "pre-prod":
        xpath = f"(//section[contains(@data-testid,'{header}')]//span)[1]"
    try:
        widget = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return widget.text
    except Exception as e:
        print(f"\033[91mCould not fetch value for {header}: {e}\033[0m")
        return "--"


def take_screenshots(driver, region):
    paths = []

    for name, data in SCREENSHOT_DATA.items():
        xpath = (
            f"//section[contains(@data-testid,'{data['heading']}')]"
            if data["type"] == "small"
            else f"//div[(@data-griditem-key or @data-panelid) and .//span[contains(text(), '{data['heading']}')]]/following-sibling::div[2]"
        )
        scroll_to_widget(driver, xpath=xpath)
        img_binary = driver.find_element(By.XPATH, xpath).screenshot_as_png
        img = Image.open(io.BytesIO(img_binary))
        filename = f"{region}/{name}"
        paths.append(filename)
        img.save(f"{filename}.png")

    return paths


def get_table_data(driver, region, heading, two_cols=False, three_cols=False):
    table_xpath = f"//div[(@data-griditem-key or @data-panelid) and .//span[contains(text(), '{heading}')]]/following-sibling::div[2]//table"
    try:
        name_header = driver.find_element(By.XPATH, f"{table_xpath}//th[@title='name']")
        name_header.click()
        name_header.click()
    except NoSuchElementException:
        pass

    try:
        col_1 = driver.find_elements(
            By.XPATH,
            f"{table_xpath}//td[1]",
        )
        if two_cols or three_cols:
            col_2 = driver.find_elements(
                By.XPATH,
                f"{table_xpath}//td[2]",
            )
        if three_cols:
            col_3 = driver.find_elements(
                By.XPATH,
                f"{table_xpath}//td[3]",
            )
        if len(col_1) == 0:
            return "No data"
        else:
            data = (
                [
                    {"name": el1.text.replace(f"{region}-", ""), "value": el2.text}
                    for el1, el2 in zip(col_1, col_2)
                ]
                if two_cols
                else (
                    [
                        {
                            "name": el1.text.replace(f"{region}-", ""),
                            "value": el2.text,
                            "max": el3.text,
                        }
                        for el1, el2, el3 in zip(col_1, col_2, col_3)
                    ]
                    if three_cols
                    else [el.text.replace(f"{region}-", "") for el in col_1]
                )
            )
            return data
    except Exception as e:
        print(f"\033[91mCould not fetch table data for {heading}: {e}\033[0m")
        return "--"


def close_menu(driver):
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "dock-menu-button"))
        ).click()
    except Exception as e:
        print(f"Could not close side menu: {e}")
        pass


def expand_all_tabs(driver):
    try:
        tabs = driver.find_elements(By.XPATH, "//*[@aria-label='Expand row']")
        for tab in tabs:
            print("Expanding tab: " + tab.text)
            tab.click()
            time.sleep(1)
    except Exception:
        pass
