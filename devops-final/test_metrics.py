"""
Automated Test and Validation Suite for Delivery Metrics Exporter
Tests calculation algorithms, configuration integrity, and metric exposition.
"""

import os
import json
import pytest
from prometheus_client import CollectorRegistry
from metrics_exporter import (
    calculate_change_failure_rate,
    calculate_mttr,
    calculate_lead_time_average,
    load_config,
    DeliveryMetricsExporter,
)


# --- Unit Tests: Metric Calculations ---

def test_calculate_change_failure_rate_standard():
    """Verify normal change failure rate calculation."""
    # 2 failures out of 10 deployments -> 0.2 (20%)
    cfr = calculate_change_failure_rate(total_deployments=10, failed_deployments=2)
    assert cfr == 0.2


def test_calculate_change_failure_rate_zero():
    """Verify CFR when zero deployments have occurred."""
    assert calculate_change_failure_rate(total_deployments=0, failed_deployments=0) == 0.0


def test_calculate_change_failure_rate_invalid():
    """Verify CFR validation errors for negative or out-of-bound values."""
    with pytest.raises(ValueError):
        calculate_change_failure_rate(total_deployments=5, failed_deployments=-1)

    with pytest.raises(ValueError):
        calculate_change_failure_rate(total_deployments=5, failed_deployments=10)


def test_calculate_mttr():
    """Verify Mean Time to Recovery (MTTR) calculation."""
    recovery_times = [100.0, 200.0, 300.0]
    assert calculate_mttr(recovery_times) == 200.0
    assert calculate_mttr([]) == 0.0

    with pytest.raises(ValueError):
        calculate_mttr([100.0, -50.0])


def test_calculate_lead_time_average():
    """Verify average Lead Time for Changes calculation."""
    lead_times = [3600.0, 1800.0, 7200.0]
    assert calculate_lead_time_average(lead_times) == 4200.0
    assert calculate_lead_time_average([]) == 0.0

    with pytest.raises(ValueError):
        calculate_lead_time_average([-10.0])


# --- Configuration Integrity Tests ---

def test_load_valid_config(tmp_path):
    """Verify loading of a valid configuration file."""
    valid_data = {
        "service_name": "test-exporter",
        "port": 9090,
        "metrics": {"interval": 10}
    }
    cfg_file = tmp_path / "valid_config.json"
    cfg_file.write_text(json.dumps(valid_data))

    cfg = load_config(str(cfg_file))
    assert cfg["service_name"] == "test-exporter"
    assert cfg["port"] == 9090


def test_load_config_missing_keys(tmp_path):
    """Verify KeyError when required configuration keys are missing."""
    incomplete_data = {"service_name": "incomplete-app"}
    cfg_file = tmp_path / "incomplete_config.json"
    cfg_file.write_text(json.dumps(incomplete_data))

    with pytest.raises(KeyError):
        load_config(str(cfg_file))


def test_load_config_file_not_found():
    """Verify FileNotFoundError when configuration file does not exist."""
    with pytest.raises(FileNotFoundError):
        load_config("non_existent_config.json")


# --- Exporter Integration Tests ---

def test_exporter_initialization_and_record():
    """Verify DeliveryMetricsExporter initializes properly and updates metric values."""
    custom_registry = CollectorRegistry()
    exporter = DeliveryMetricsExporter(config_path="config.json", registry=custom_registry)

    # Record a deployment
    exporter.record_deployment(environment="staging", success=True, lead_time_seconds=900.0)

    # Update KPIs
    kpis = exporter.update_delivery_kpis(total_deploys=20, failed_deploys=2, recovery_times=[600.0, 1200.0])
    assert kpis["change_failure_rate"] == 0.1
    assert kpis["mttr_seconds"] == 900.0


# --- Controlled Test Failure Demonstration (Mandatory Step 5) ---

# In devops-final/test_metrics.py
def test_delivery_metrics_validation_gate():
    # Controlled failure for the assignment
    assert False, "Controlled failure: Delivery metric validation failed"
