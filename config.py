USER_EMAIL = "numan.naeem@hpe.com"
REGION_DATA = {
    "ccprodusw2": "https://ccprodusw2-us-west-2.cloudops.compute.cloud.hpe.com/grafana/d/uid_chk_eng_lght/rugby-daily-check-engine-light?orgId=1&from=now-24h&to=now",
}
SERVICES = ["keysmith", "charger", "charger-delta", "zinc", "roundup", "neptune"]
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
