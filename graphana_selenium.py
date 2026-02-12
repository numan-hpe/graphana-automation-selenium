from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import traceback
from datetime import date
import time
import os
import json
import stat
from pdf_generator import generate_pdf
from config import REGION_DATA, HEADINGS
from selenium_utils import (
    login_user,
    close_menu,
    scroll_to_widget,
    get_value,
    get_table_data,
    take_screenshots,
)

options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-device-discovery")
options.add_argument("--disable-popup-blocking")
options.add_argument("--disable-windows-filtering-platform")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--allow-running-insecure-content")
options.add_argument("--disable-web-resources")

driver = webdriver.Chrome(options=options)

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
        driver.get(url)

        login_user(driver)
        time.sleep(5)

        close_menu(driver)

        # SLI
        scroll_to_widget(driver, HEADINGS["sli"])
        output["sli"] = get_value(driver, HEADINGS["sli"])
        # Websockets
        scroll_to_widget(driver, HEADINGS["websockets"])
        output["websockets"] = get_value(driver, HEADINGS["websockets"], region)
        # duration > 500ms
        scroll_to_widget(driver, HEADINGS["duration_over_500ms"])
        output["duration_over_500ms"] = get_table_data(
            driver, region, HEADINGS["duration_over_500ms"]
        )
        # HTTP 5x
        scroll_to_widget(driver, HEADINGS["http_5x"])
        output["http_5x"] = get_table_data(driver, region, HEADINGS["http_5x"])
        # Pod restarts
        scroll_to_widget(driver, HEADINGS["pod_restarts"])
        output["pod_restarts"] = get_table_data(
            driver, region, HEADINGS["pod_restarts"], two_cols=True
        )
        # Pod counts
        scroll_to_widget(driver, HEADINGS["pod_counts"])
        output["pod_counts"] = get_table_data(
            driver, region, HEADINGS["pod_counts"], three_cols=True
        )
        # Memory utilization
        scroll_to_widget(driver, HEADINGS["memory"])
        output["memory"] = get_table_data(
            driver, region, HEADINGS["memory"], two_cols=True
        )
        # CPU utilization
        scroll_to_widget(driver, HEADINGS["cpu"])
        output["cpu"] = get_table_data(driver, region, HEADINGS["cpu"], two_cols=True)

        # Screenshots
        screenshots = take_screenshots(driver, region)
        with open(os.path.join(region, "data.json"), "w") as json_file:
            json.dump(output, json_file, indent=4)

        REGION_OUTPUTS[region] = output
        print(f"Data collected for {region}")

    formatted_datetime = (
        date.today().strftime("%Y-%m-%d") + "_" + time.strftime("%H-%M")
    )
    os.makedirs("reports", exist_ok=True)
    generate_pdf("reports", f"service_monitoring_{formatted_datetime}.pdf")

except Exception as e:
    print("Error occurred: ")
    print(traceback.format_exc())
finally:
    driver.close()
