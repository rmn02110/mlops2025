from lesson4.seminar.step4_monitoring.src.config import load_config
from lesson4.seminar.step4_monitoring.src.monitor import Monitor

if __name__ == "__main__":
    config = load_config("config/monitoring_config.yaml")
    Monitor(config).run()
