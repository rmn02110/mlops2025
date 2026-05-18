from dataclasses import dataclass

import yaml


@dataclass
class Config:
    base_url: str
    check_interval: int
    samples: int
    timeout: int
    thresholds: dict
    alerts: dict
    logging: dict
    image_path: str | None


def load_config(path: str) -> Config:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return Config(
        base_url=data["service"]["base_url"],
        check_interval=data["monitoring"]["check_interval_seconds"],
        samples=data["monitoring"]["samples_per_check"],
        timeout=data["monitoring"]["request_timeout_seconds"],
        thresholds=data["thresholds"],
        alerts=data["alerts"],
        logging=data["logging"],
        image_path=(data.get("testing") or {}).get("image_path"),
    )
