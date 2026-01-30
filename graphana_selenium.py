from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from humio_selenium import get_humio_data
from datetime import date
from pywinauto import Desktop
import pyautogui
import time
import io
import os
import json
import stat
from pdf_generator import generate_pdf
from PIL import Image
from config import SERVICES, REGION_DATA, USER_EMAIL, HEADINGS, PIN, SCREENSHOT_DATA
from file_uploader import file_uploader

options = Options()
options.add_argument("--start-maximized")
# options.add_argument("--headless")

driver = webdriver.Chrome(options=options)
driver.set_page_load_timeout(240)
driver.command_executor._client_config.timeout = 300
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


def handle_certificate_selection():
    try:
        time.sleep(5)
        pyautogui.press("tab", presses=2)
        pyautogui.press("enter")
        print("Certificate selected successfully.")
    except Exception as e:
        print("Error handling certificate dialog:", e)


def handle_pin_entry():
    """Handles the Windows Security PIN entry dialog."""
    try:
        window = wait_for_window("Windows Security")
        window.set_focus()
        time.sleep(1)  # Ensure the window is ready

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

    WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//a[@href='login/azuread']"))
    ).click()

    if not logged_in:
        WebDriverWait(driver, login_timeout).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='email']"))
        ).send_keys(USER_EMAIL)

        driver.find_element(By.XPATH, "//input[@type='submit']").click()
        time.sleep(3)
        # handle_certificate_selection()
        # time.sleep(3)
        # handle_pin_entry()
        WebDriverWait(driver, login_timeout).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))
        ).click()

        while time.time() - start_time < login_timeout:
            current_url = driver.current_url
            if "rugby-daily-check-engine-light" in current_url:
                print("Dashboard loaded successfully!")
                logged_in = True
                break
            else:
                time.sleep(2)  # Check every 2 seconds

        if not logged_in:
            print("Login failed")
            raise Exception


def safe_get(url, attempts=2):
    """Navigate to a URL with one retry and driver restart if needed."""
    global driver, logged_in
    for i in range(attempts):
        try:
            driver.get(url)
            return
        except Exception as e:
            print(f"Navigation attempt {i + 1} failed: {e}")
            if i == attempts - 1:
                raise
            try:
                driver.quit()
            except Exception:
                pass
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(240)
            driver.command_executor._client_config.timeout = 300
            logged_in = False


def wait_for_widgets_to_load(max_timeout=60):
    expand_all_tabs()
    WebDriverWait(driver, max_timeout).until(
        lambda driver: len(
            driver.find_elements(By.XPATH, "//div[@aria-label='Panel loading bar']")
        )
        == 0
    )


def scroll_to_widget(heading=None, xpath=None):
    xpath = xpath or f"//*[contains(text(), '{heading}')]"
    attempts = 0
    try:
        page = driver.find_element(By.ID, "page-scrollbar")
    except NoSuchElementException:
        page = None
    while attempts < 20:
        elements = driver.find_elements(
            By.XPATH, xpath
        )
        if elements:
            break
        if page:
            driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollTop + 300", page
            )
        else:
            driver.execute_script("window.scrollBy(0, 300)")
        expand_all_tabs()    
        time.sleep(1)
        attempts += 1
    widget = driver.find_element(
        By.XPATH, xpath
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", widget)
    if page:
        driver.execute_script(
            "arguments[0].scrollTop = arguments[0].scrollTop - 100", page
        )
    else:
        driver.execute_script("window.scrollBy(0, -100)")
    time.sleep(1)
    wait_for_widgets_to_load()


def get_value(header):
    try:
        widget = WebDriverWait(driver, 60).until(
            EC.visibility_of_element_located(
                (By.XPATH, f"//section[contains(@data-testid,'{header}')]//div[@title]")
            )
        )
        return widget.text
    except Exception as e:
        print(f"Could not get value for {header}: {e}")
        return "N/A"


def take_screenshots():
    paths = []

    for name, data in SCREENSHOT_DATA.items():
        # Scroll to widget first
        scroll_to_widget(data["heading"])
        time.sleep(1)  # Wait for graph to fully render
        
        xpath = (
            f"//section[contains(@data-testid,'{data['heading']}')]"
            if data["type"] == "small"
            else f"//div[(@data-griditem-key or @data-panelid) and .//span[contains(text(), '{data['heading']}')]]/following-sibling::div[2]"
        )
        
        # Find the element and ensure it's fully visible
        element = driver.find_element(By.XPATH, xpath)
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
        time.sleep(0.5)  # Additional wait after scroll
        
        img_binary = element.screenshot_as_png
        img = Image.open(io.BytesIO(img_binary))
        filename = f"{region}/{name}"
        paths.append(filename)
        img.save(f"{filename}.png")

    return paths


def get_table_data(heading, two_cols=False, three_cols=False):
    table_xpath = f"//div[(@data-griditem-key or @data-panelid) and .//span[contains(text(), '{heading}')]]/following-sibling::div[2]//table"
    try:
        try:
            name_header = driver.find_element(By.XPATH, f"{table_xpath}//th[@title='name']")
            name_header.click()
            name_header.click()
        except NoSuchElementException:
            pass
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
        print(f"Error getting table data for {heading}: {e}")
        return "No data"


def close_menu():
    try:
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.ID, "dock-menu-button"))
        ).click()
    except NoSuchElementException:
        pass

def expand_all_tabs():
    try:
        tabs = driver.find_elements(By.XPATH, "//*[@aria-label='Expand row']")
        for tab in tabs:
            print("Expanding tab: " + tab.text)
            tab.click()
            time.sleep(1)
    except Exception:
        pass


output = {}
REGION_OUTPUTS = {}
try:
    for region, url in REGION_DATA.items():
        # Clear folder contents
        if os.path.exists(region):
            for root, dirs, files in os.walk(region, topdown=False):
                for name in files:
                    filename = os.path.join(root, name)
                    os.chmod(filename, stat.S_IWRITE)
                    os.remove(filename)
        else:
            os.makedirs(region, exist_ok=True)
        print(f"Opening {region} Grafana dashboard...")
        safe_get(url)

        login_user()
        time.sleep(5)

        close_menu()

        # SLI
        wait_for_widgets_to_load()
        output["sli"] = get_value(HEADINGS["sli"])
        # Websockets
        scroll_to_widget(HEADINGS["websockets"])
        output["websockets"] = get_value(HEADINGS["websockets"], region)
        # duration > 500ms
        scroll_to_widget(HEADINGS["duration_over_500ms"])
        output["duration_over_500ms"] = get_table_data(HEADINGS["duration_over_500ms"])
        # HTTP 5x
        scroll_to_widget(HEADINGS["http_5x"])
        output["http_5x"] = get_table_data(HEADINGS["http_5x"])
        # Pod restarts
        scroll_to_widget(HEADINGS["pod_restarts"])
        output["pod_restarts"] = get_table_data(HEADINGS["pod_restarts"], two_cols=True)
        # Pod counts
        scroll_to_widget(HEADINGS["pod_counts"])
        output["pod_counts"] = get_table_data(HEADINGS["pod_counts"], three_cols=True)
        # Memory utilization
        scroll_to_widget(HEADINGS["memory"])
        output["memory"] = get_table_data(HEADINGS["memory"], two_cols=True)
        # CPU utilization
        scroll_to_widget(HEADINGS["cpu"])
        output["cpu"] = get_table_data(HEADINGS["cpu"], two_cols=True)

        # Screenshots
        screenshots = take_screenshots()
        with open(os.path.join(region, "data.json"), "w") as json_file:
            json.dump(output, json_file, indent=4)

        REGION_OUTPUTS[region] = output
        print(f"Data collected for {region}")

    formatted_datetime = (
        date.today().strftime("%Y-%m-%d") + "_" + time.strftime("%H-%M")
    )
    os.makedirs("reports", exist_ok=True)
    try:
        generate_pdf("reports", f"service_monitoring_{formatted_datetime}.pdf")
        print("Report generated successfully!")
    except Exception as pdf_error:
        print(f"Error generating PDF: {pdf_error}")
        import traceback
        traceback.print_exc()

except Exception as e:
    print("Encountered error", e)
finally:
    driver.close()
