USER_EMAIL = "you_email@hpe.com"
PIN = "your_SSO_PIN" # Add your PIN here and uncomment L90-92 in graphana_selenium.py for auto PIN entry 
BOT_TOKEN = "Add token here"
CHANNEL_ID = "C085P82Q4R4"
REGION_DATA = {
    "ccprodusw2": "https://ccprodusw2-us-west-2.cloudops.compute.cloud.hpe.com/grafana/d/uid_chk_eng_lght/rugby-daily-check-engine-light?orgId=1&from=now-24h&to=now",
    "ccprodeuc1": "https://ccprodeuc1-eu-central-1.cloudops.compute.cloud.hpe.com/grafana/d/uid_chk_eng_lght/rugby-daily-check-engine-light?orgId=1&from=now-24h&to=now",
    "ccprodane1": "https://ccprodane1-ap-northeast-1.cloudops.compute.cloud.hpe.com/grafana/d/uid_chk_eng_lght/rugby-daily-check-engine-light?orgId=1&from=now-24h&to=now",
    "pre-prod": "https://ccpreusw2-us-west-2.cloudops.compute.cloud.hpe.com/grafana/d/uid_chk_eng_lght/rugby-daily-check-engine-light?orgId=1&from=now-24h&to=now",
}
HUMIO_DATA = {
    "ccprodusw2": "https://ccprodusw2-us-west-2.cloudops.compute.cloud.hpe.com/logs/computecentral/dashboards/Data%20Ingestion%20to%20Sustainability%20Insight%20Center?dashboardId=OEhGElYomuJaOVTfMuqr49OZgHkiHBOz&fullscreen=false&sharedTime=true&start=1d&updateFrequency=never"
}
SERVICES = ["keysmith", "charger", "charger-delta", "zinc-app", "roundup", "neptune"]
HEADINGS = {
    "sli": "Latency, Error-Rate, Availability Combined",
    "websockets": "Number of --currently connected-- websocket connections",
    "duration_over_500ms": "Durations > 500ms  (Click Data Points for more info)",
    "duration_over_500ms_special": "Durations > 500ms  - Special Cases   (Click Data Points for more info)",
    "http_5x": "HTTP 5x responses",
    "pod_restarts": "Pod Restarts",
    "pod_counts": "Pod Counts over time",
    "memory": "Namespace relative memory utilization",
    "cpu": "Namespace relative CPU utilization",
}
SCREENSHOT_DATA = {
    "websockets": {"type": "small", "heading": "Websocket Connection"},
    "cpu": {"type": "large", "heading": HEADINGS["cpu"]},
    "memory": {"type": "large", "heading": HEADINGS["memory"]},
}
HUMIO_HEADINGS = {
    "files_failures": "Files failed to upload",
    "unknown_errors": "Unknown Error during server_metric_data message processing",
    "bisbee_errors": "Exception while uploading file to bisbee",
}
