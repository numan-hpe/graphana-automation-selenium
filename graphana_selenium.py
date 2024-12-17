from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time

options = Options()
options.add_argument("--start-maximized")
# options.add_argument("--headless")

driver = webdriver.Chrome(options=options)  # Change to webdriver.Firefox() if using Firefox
region = "ccprodusw2"
services = ["keysmith", "charger", "charger-delta", "zinc", "roundup", "neptune"]

def wait_for_widgets_to_load(max_timeout=120):
    start = time.time()
    WebDriverWait(driver, max_timeout).until(
        lambda driver: len(driver.find_elements(By.XPATH, "//div[@aria-label='Panel loading bar']")) == 0
    )
    print("Load time = ", time.time() - start)
    

def scroll_to_widget(heading):
    # widget = WebDriverWait(driver, 10).until(
    #     EC.presence_of_element_located((By.XPATH,f"//div[@data-panelid]//*[contains(text(), '{heading}')]"))
    # )
    widget = driver.find_element(By.XPATH, f"//div[@data-panelid]//*[contains(text(), '{heading}')]")
    driver.execute_script("arguments[0].scrollIntoView();", widget)
    time.sleep(1)
    wait_for_widgets_to_load()

def get_value(header):
    return driver.find_element(By.XPATH, f"//div[contains(@data-testid,'{header}')]//div[@title]").text

def get_table_data(heading):
    table_elements = driver.find_elements(By.XPATH, f"//div[@data-panelid and .//span[contains(text(), '{heading}')]]/following-sibling::div[2]//table//button")
    if len(table_elements) == 0:
        return "No data"
    else:
        data = [element.text.replace(f"{region}-", '') for element in table_elements]
        return data
output = {}
try:
    print("Opening Grafana dashboard...")
    driver.get("https://ccprodusw2-us-west-2.cloudops.compute.cloud.hpe.com/grafana/d/uid_chk_eng_lght/rugby-daily-check-engine-light?orgId=1&from=now-24h&to=now")

    start_time = time.time()  # Record the start time
    login_timeout = 120  # Maximum time to wait for login (in seconds)
    loading_timeout = 100  
    
    driver.find_element(By.XPATH,"//a[@href='login/generic_oauth']").click()
    
    email = WebDriverWait(driver, 10).until(lambda x: x.find_element(By.XPATH,"//input[@type='email']"))
    email.send_keys("numan.naeem@hpe.com")
    driver.find_element(By.XPATH,"//input[@type='submit']").click()
    time.sleep(5)
    WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH,"//input[@type='submit']"))).click()
    
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
        if option.text.split('-', maxsplit=1)[-1] in services:
            option.click()

    driver.find_element(By.TAG_NAME, 'html').click()
    time.sleep(1)

    # SLI
    wait_for_widgets_to_load()
    output["sli"] = get_value("Latency, Error-Rate, Availability Combined")
    # Websockets
    scroll_to_widget("Number of --currently connected-- websocket connections")
    output["websockets"] = get_value("Number of --currently connected-- websocket connections")
    # duration > 500ms
    scroll_to_widget("Durations > 500ms  (Click Data Points for more info)")
    output["duration_over_500ms"] = get_table_data("Durations > 500ms  (Click Data Points for more info)")
    # duration > 500ms - special cases
    scroll_to_widget("Durations > 500ms  - Special Cases   (Click Data Points for more info)")
    output["duration_over_500ms"] = get_table_data("Durations > 500ms  - Special Cases   (Click Data Points for more info)")
    # HTTP 5x
    scroll_to_widget("HTTP 5x responses  (Click Data Points for more info)")
    output["duration_over_500ms_special"] = get_table_data("HTTP 5x responses  (Click Data Points for more info)")
    # Pod restarts
    scroll_to_widget("Pod Restarts")
    output["http_5x"] = get_table_data("Pod Restarts")
    
    
    print(output)
except Exception as e:
    print("Encountered error", e)
    print(e.with_traceback)
finally:
    input()
    driver.close()
    exit()
