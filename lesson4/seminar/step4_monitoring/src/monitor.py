import json
import mimetypes
import os
import time
from datetime import datetime
from statistics import quantiles

import requests

from .logger import Logger

_ONE_PIXEL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0cIDAT\x08\x1d"
    b"\x01\x01\x00\xfe\xff\x00\xff\xff\xff\xff\xa0\x8d\xf7\xde\x00\x00"
    b"\x00\x00IEND\xaeB`\x82"
)


class Monitor:
    def __init__(self, config):
        self.config = config
        self.logger = Logger(
            config.logging["log_file"], config.logging.get("console_colors", True)
        )
        self.consecutive_failures = 0
        self.last_alert = 0
        os.makedirs(os.path.dirname(config.logging["metrics_file"]), exist_ok=True)

    def request(self, method: str, endpoint: str, **kwargs):
        started = time.perf_counter()
        try:
            response = requests.request(
                method,
                self.config.base_url + endpoint,
                timeout=self.config.timeout,
                **kwargs,
            )
            latency = (time.perf_counter() - started) * 1000
            try:
                body = response.json()
            except ValueError:
                body = response.text[:200]
            return response.ok, latency, body
        except Exception as exc:
            latency = (time.perf_counter() - started) * 1000
            return False, latency, {"error": str(exc)}

    def check_health(self):
        return self.request("GET", "/health")

    def check_predict(self):
        if self.config.image_path and os.path.exists(self.config.image_path):
            mime = mimetypes.guess_type(self.config.image_path)[0] or "image/jpeg"
            with open(self.config.image_path, "rb") as f:
                files = {"file": (os.path.basename(self.config.image_path), f, mime)}
                return self.request("POST", "/predict", files=files)
        return self.request(
            "POST",
            "/predict",
            files={"file": ("image.png", _ONE_PIXEL_PNG, "image/png")},
        )

    def status(self, response_time, p95_latency, error_rate):
        t = self.config.thresholds
        if (
            response_time >= t["response_time_ms"]["critical"]
            or p95_latency >= t["p95_latency_ms"]["critical"]
            or error_rate >= t["error_rate_percent"]["critical"]
            or self.consecutive_failures >= t["consecutive_failures"]["critical"]
        ):
            return "red"
        if (
            response_time >= t["response_time_ms"]["warning"]
            or p95_latency >= t["p95_latency_ms"]["warning"]
            or error_rate >= t["error_rate_percent"]["warning"]
            or self.consecutive_failures >= t["consecutive_failures"]["warning"]
        ):
            return "yellow"
        return "green"

    def write_metrics(self, metrics):
        with open(self.config.logging["metrics_file"], "a", encoding="utf-8") as f:
            f.write(json.dumps(metrics, ensure_ascii=False) + "\n")

    def run_once(self):
        latencies = []
        errors = 0
        total = 0

        for _ in range(self.config.samples):
            for name, check in [
                ("health", self.check_health),
                ("predict", self.check_predict),
            ]:
                ok, latency, body = check()
                total += 1
                errors += int(not ok)
                latencies.append(latency)
                if ok:
                    self.consecutive_failures = 0
                else:
                    self.consecutive_failures += 1
                self.logger.log(
                    "green" if ok else "red",
                    name,
                    ok=ok,
                    response_time_ms=round(latency, 2),
                    response=body,
                )

        p95_latency = (
            quantiles(latencies, n=20)[18] if len(latencies) > 1 else latencies[0]
        )
        response_time = max(latencies)
        error_rate = errors / total * 100
        status = self.status(response_time, p95_latency, error_rate)
        metrics = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "response_time_ms": round(response_time, 2),
            "p95_latency_ms": round(p95_latency, 2),
            "error_rate_percent": round(error_rate, 2),
            "health_status": errors == 0,
            "consecutive_failures": self.consecutive_failures,
            "status": status,
        }
        self.write_metrics(metrics)

        now = time.time()
        cooldown = self.config.alerts["cooldown_minutes"] * 60
        if (
            status != "green"
            and self.config.alerts["enabled"]
            and now - self.last_alert >= cooldown
        ):
            self.last_alert = now
            self.logger.log(status, "alert", **metrics)
        else:
            self.logger.log(status, "metrics", **metrics)

    def run(self):
        while True:
            self.run_once()
            time.sleep(self.config.check_interval)
