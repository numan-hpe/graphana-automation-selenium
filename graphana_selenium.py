from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from config import SERVICES, REGION_DATA, USER_EMAIL, HEADINGS

options = Options()
options.add_argument("--start-maximized")
# options.add_argument("--headless")

driver = webdriver.Chrome(options=options)
region = "ccprodusw2"


def login_user():
    # Perform user login once Grafana login page is opened
    start_time = time.time()  # Record the start time
    login_timeout = 90  # Maximum time to wait for login (in seconds)

    WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//a[@href='login/generic_oauth']"))
    ).click()

    WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@type='email']"))
    ).send_keys(USER_EMAIL)

    driver.find_element(By.XPATH, "//input[@type='submit']").click()
    time.sleep(5)
    WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@type='submit']"))
    ).click()

    login_successful = False
    while time.time() - start_time < login_timeout:
        current_url = driver.current_url
        if "rugby-daily-check-engine-light" in current_url:
            print("Dashboard loaded successfully!")
            login_successful = True
            break
        else:
            time.sleep(2)  # Check every 2 seconds

    if not login_successful:
        print("Login failed")
        raise Exception


def wait_for_widgets_to_load(max_timeout=60):
    start = time.time()
    WebDriverWait(driver, max_timeout).until(
        lambda driver: len(
            driver.find_elements(By.XPATH, "//div[@aria-label='Panel loading bar']")
        )
        == 0
    )
    print("Load time = ", time.time() - start)


def scroll_to_widget(heading):
    widget = driver.find_element(
        By.XPATH, f"//div[@data-panelid]//*[contains(text(), '{heading}')]"
    )
    driver.execute_script("arguments[0].scrollIntoView();", widget)
    time.sleep(1)
    wait_for_widgets_to_load()


def get_value(header):
    return driver.find_element(
        By.XPATH, f"//div[contains(@data-testid,'{header}')]//div[@title]"
    ).text


def get_table_data(heading, two_cols=False, three_cols=False):
    tbody_xpath = f"//div[@data-panelid and .//span[contains(text(), '{heading}')]]/following-sibling::div[2]//tbody"
    col_1 = driver.find_elements(
        By.XPATH,
        f"{tbody_xpath}//td[1]",
    )
    if two_cols or three_cols:
        col_2 = driver.find_elements(
            By.XPATH,
            f"{tbody_xpath}//td[2]",
        )
    if three_cols:
        col_3 = driver.find_elements(
            By.XPATH,
            f"{tbody_xpath}//td[3]",
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


output = {}
try:
    print("Opening Grafana dashboard...")
    driver.get(REGION_DATA[region])

    login_user()
    # Wait for the "rugbyservice" button to be clickable and click it
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "var-rugbyservice"))
    ).click()

    # Wait for the dropdown to be visible
    dropdown = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "options-rugbyservice"))
    )

    # Find all the list items within the dropdown
    options = dropdown.find_elements(By.TAG_NAME, "li")

    for option in options:
        if option.text.split("-", maxsplit=1)[-1] in SERVICES:
            option.click()

    driver.find_element(By.TAG_NAME, "html").click()
    time.sleep(1)

    # SLI
    wait_for_widgets_to_load()
    output["sli"] = get_value(HEADINGS["sli"])
    # Websockets
    scroll_to_widget(HEADINGS["websockets"])
    output["websockets"] = get_value(HEADINGS["websockets"])
    # duration > 500ms
    scroll_to_widget(HEADINGS["duration_over_500ms"])
    output["duration_over_500ms"] = get_table_data(HEADINGS["duration_over_500ms"])
    # duration > 500ms - special cases
    scroll_to_widget(HEADINGS["duration_over_500ms_special"])
    output["duration_over_500ms_special"] = get_table_data(
        HEADINGS["duration_over_500ms_special"]
    )
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

    print(output)
except Exception as e:
    print("Encountered error", e)
    print(e.with_traceback)
finally:
    input()
    driver.close()
    exit()
