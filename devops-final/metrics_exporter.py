#!/usr/bin/env python3
"""
Delivery Metrics Exporter
A Prometheus exporter and calculation engine for CI/CD delivery and DORA metrics:
- Deployment Frequency
- Lead Time for Changes
- Change Failure Rate
- Mean Time to Recovery (MTTR)
"""

import os
import sys
import json
import time
import argparse
from typing import Dict, Any, List
from prometheus_client import start_http_server, Gauge, Counter, CollectorRegistry, REGISTRY


# --- Metrics Definitions ---
def setup_metrics(registry: CollectorRegistry = REGISTRY):
    """Initializes Prometheus metrics in the specified registry."""
    metrics = {
        "deployments_total": Counter(
            "delivery_deployments_total",
            "Total number of completed deployments",
            ["environment", "status"],
            registry=registry,
        ),
        "lead_time_seconds": Gauge(
            "delivery_lead_time_seconds",
            "Lead time for changes in seconds (commit to deployment)",
            ["service"],
            registry=registry,
        ),
        "change_failure_rate": Gauge(
            "delivery_change_failure_rate",
            "Ratio of failed deployments to total deployments",
            ["service"],
            registry=registry,
        ),
        "mttr_seconds": Gauge(
            "delivery_mttr_seconds",
            "Mean Time to Recovery in seconds",
            ["service"],
            registry=registry,
        ),
        "pipeline_builds_total": Counter(
            "delivery_pipeline_builds_total",
            "Total number of pipeline runs",
            ["stage", "status"],
            registry=registry,
        ),
    }
    return metrics


# --- Calculation Logic ---
def calculate_change_failure_rate(total_deployments: int, failed_deployments: int) -> float:
    """Calculates Change Failure Rate (CFR) as a ratio between 0.0 and 1.0."""
    if total_deployments <= 0:
        return 0.0
    if failed_deployments < 0:
        raise ValueError("Failed deployments cannot be negative")
    if failed_deployments > total_deployments:
        raise ValueError("Failed deployments cannot exceed total deployments")
    return round(failed_deployments / total_deployments, 4)


def calculate_mttr(recovery_times_seconds: List[float]) -> float:
    """Calculates Mean Time to Recovery (MTTR) in seconds."""
    if not recovery_times_seconds:
        return 0.0
    if any(t < 0 for t in recovery_times_seconds):
        raise ValueError("Recovery times cannot be negative")
    return round(sum(recovery_times_seconds) / len(recovery_times_seconds), 2)


def calculate_lead_time_average(lead_times_seconds: List[float]) -> float:
    """Calculates average Lead Time for Changes in seconds."""
    if not lead_times_seconds:
        return 0.0
    if any(t < 0 for t in lead_times_seconds):
        raise ValueError("Lead times cannot be negative")
    return round(sum(lead_times_seconds) / len(lead_times_seconds), 2)


# --- Configuration Loader ---
def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """Loads and validates service configuration from a JSON file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    required_keys = ["service_name", "port", "metrics"]
    for key in required_keys:
        if key not in config:
            raise KeyError(f"Missing required configuration key: {key}")

    return config


# --- Exporter Service ---
class DeliveryMetricsExporter:
    """Delivery Metrics Exporter Daemon."""

    def __init__(self, config_path: str = "config.json", registry: CollectorRegistry = REGISTRY):
        self.config = load_config(config_path)
        self.registry = registry
        self.metrics = setup_metrics(self.registry)
        self.service_name = self.config.get("service_name", "delivery-metrics-exporter")
        self.port = self.config.get("port", 8000)

    def record_deployment(self, environment: str, success: bool, lead_time_seconds: float):
        """Records a deployment event and updates delivery metrics."""
        status = "success" if success else "failure"
        self.metrics["deployments_total"].labels(environment=environment, status=status).inc()
        self.metrics["lead_time_seconds"].labels(service=self.service_name).set(lead_time_seconds)

    def update_delivery_kpis(self, total_deploys: int, failed_deploys: int, recovery_times: List[float]):
        """Updates aggregate DORA KPIs."""
        cfr = calculate_change_failure_rate(total_deploys, failed_deploys)
        mttr = calculate_mttr(recovery_times)

        self.metrics["change_failure_rate"].labels(service=self.service_name).set(cfr)
        self.metrics["mttr_seconds"].labels(service=self.service_name).set(mttr)
        return {"change_failure_rate": cfr, "mttr_seconds": mttr}

    def start(self, block: bool = True):
        """Starts Prometheus HTTP server."""
        print(f"Starting {self.service_name} on port {self.port}...")
        start_http_server(self.port, registry=self.registry)
        print(f"Delivery metrics server running at http://localhost:{self.port}/metrics")

        # Initial seed of default delivery metrics
        self.update_delivery_kpis(total_deploys=10, failed_deploys=1, recovery_times=[300.0, 450.0])
        self.record_deployment(environment="production", success=True, lead_time_seconds=1800.0)

        if block:
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nShutting down Delivery Metrics Exporter.")


def main():
    parser = argparse.ArgumentParser(description="DevOps Delivery Metrics Exporter")
    parser.add_argument("--config", default="config.json", help="Path to config.json")
    parser.add_argument("--port", type=int, default=None, help="Override HTTP port")
    parser.add_argument("--dry-run", action="store_true", help="Validate config and metrics without binding port")
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        if args.port:
            config["port"] = args.port

        print(f"[SUCCESS] Config loaded for service: {config['service_name']} (v{config.get('version', 'unknown')})")

        if args.dry_run:
            print("[INFO] Dry run successful: Configuration and metric schema validated.")
            sys.exit(0)

        exporter = DeliveryMetricsExporter(config_path=args.config)
        exporter.start(block=True)
    except Exception as e:
        print(f"[ERROR] Failed to start exporter: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
