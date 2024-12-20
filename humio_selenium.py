from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pywinauto import Desktop
import os
import json
import pyautogui
import time
from pdf_generator import generate_pdf
from PIL import Image
from config import SERVICES, HUMIO_DATA, USER_EMAIL, HUMIO_HEADINGS, PIN


logged_in = False
driver = None

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


def handle_certificate_selection():
    try:
        pyautogui.press("enter")
        print("Certificate selected successfully.")
    except Exception as e:
        print("Error handling certificate dialog:", e)


def handle_pin_entry():
    """Handles the Windows Security PIN entry dialog."""
    try:
        window = wait_for_window("Windows Security")
        window.set_focus()
        time.sleep(0.5)  # Ensure the window is ready

        # Enter PIN
        window.child_window(control_type="Edit").type_keys(PIN, with_spaces=True)
        print("PIN entered successfully.")

        # Press OK
        window.child_window(title="OK", control_type="Button").click()
        print("Clicked OK on PIN entry dialog.")
    except Exception as e:
        print(f"Error handling PIN entry: {e}")
        raise


def login_user():
    global logged_in
    # Perform user login once Grafana login page is opened
    start_time = time.time()  # Record the start time
    login_timeout = 180  # Maximum time to wait for login (in seconds)

    if not logged_in:
        WebDriverWait(driver, login_timeout).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='email']"))
        ).send_keys(USER_EMAIL)

        driver.find_element(By.XPATH, "//input[@type='submit']").click()
        time.sleep(5)
        handle_certificate_selection()
        handle_pin_entry()
        WebDriverWait(driver, login_timeout).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))
        ).click()

        while time.time() - start_time < login_timeout:
            current_url = driver.current_url
            if "computecentral/dashboards" in current_url:
                print("Dashboard loaded successfully!")
                logged_in = True
                break
            else:
                time.sleep(2)  # Check every 2 seconds

        if not logged_in:
            print("Login failed")
            raise Exception


def load_widgets(max_timeout=120):
    WebDriverWait(driver, max_timeout).until(
        lambda driver: len(
            driver.find_elements(
                By.XPATH,
                "//div[@data-e2e-id='status-message' and contains(text(), 'Loading')]",
            )
        )
        == 0
        and len(
            driver.find_elements(
                By.XPATH, "//div[contains(@class,'result-view__progress-bar')]"
            )
        )
        == len(
            driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'result-view__progress-bar')]//div[contains(@class,'opacity-0')]",
            )
        )
    )


def get_value(heading):
    return driver.find_element(
        By.XPATH, f"//div[@data-e2e-id='widget-title-{heading}']/following-sibling::div"
    ).text


def scroll_to_widget(heading):
    widget = driver.find_element(
        By.XPATH, f"//div[@data-e2e-id='widget-title-{heading}']"
    )
    driver.execute_script("arguments[0].scrollIntoView();", widget)
    time.sleep(1)
    load_widgets()

def get_humio_data(web_driver):
    global driver
    driver = web_driver
    output = {}

    for region, url in HUMIO_DATA.items():
        try:
            driver.get(url)
            # login_user()
            time.sleep(10)

            scroll_to_widget(HUMIO_HEADINGS["files_failures"])
            output["files_failures"] = get_value(HUMIO_HEADINGS["files_failures"])

            scroll_to_widget(HUMIO_HEADINGS["unknown_errors"])
            output["unknown_errors"] = get_value(HUMIO_HEADINGS["unknown_errors"])

            scroll_to_widget(HUMIO_HEADINGS["bisbee_errors"])
            output["bisbee_errors"] = get_value(HUMIO_HEADINGS["bisbee_errors"])

            with open(os.path.join(region, "humio.json"), "w") as json_file:
                json.dump(output, json_file, indent=4)
        except Exception as e:
            raise e
