"""Tests for netdrift. Run with: python3 -m pytest -q"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

import netdrift


def test_normalize_cidr_canonicalizes_host_bits():
    # A host address inside a /24 normalizes to the network address.
    assert netdrift.normalize_cidr("10.30.0.5/24") == "10.30.0.0/24"


def test_normalize_cidr_rejects_garbage():
    with pytest.raises(ValueError):
        netdrift.normalize_cidr("not-a-cidr")


def test_no_drift_when_identical():
    state = {
        "subnets": ["10.30.0.0/24", "10.30.10.0/24"],
        "dns_records": {"gw.lab": "10.30.0.1"},
    }
    report = netdrift.compare(state, dict(state))
    assert not report.has_drift


def test_detects_missing_and_unexpected_subnets():
    desired = {"subnets": ["10.30.0.0/24", "10.30.1.0/24"]}
    actual = {"subnets": ["10.30.0.0/24", "10.30.99.0/24"]}
    report = netdrift.compare(desired, actual)
    assert report.missing_subnets == ["10.30.1.0/24"]
    assert report.unexpected_subnets == ["10.30.99.0/24"]
    assert report.has_drift


def test_host_bit_difference_is_not_drift():
    # Same network, cosmetic host-bit difference — must NOT be flagged.
    desired = {"subnets": ["10.30.0.0/24"]}
    actual = {"subnets": ["10.30.0.7/24"]}
    assert not netdrift.compare(desired, actual).has_drift


def test_detects_changed_and_missing_dns():
    desired = {"dns_records": {"gw.lab": "10.30.0.1", "dns.lab": "10.30.0.2"}}
    actual = {"dns_records": {"gw.lab": "10.30.0.254"}}
    report = netdrift.compare(desired, actual)
    assert report.changed_dns == ["gw.lab"]
    assert report.missing_dns == ["dns.lab"]
    assert report.has_drift


def test_invalid_dns_records_type_raises():
    with pytest.raises(ValueError):
        netdrift.compare({"dns_records": ["not", "a", "map"]}, {})


def _write(tmp_path: Path, name: str, body: str) -> str:
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return str(path)


def test_cli_exit_zero_on_match(tmp_path: Path):
    desired = _write(tmp_path, "d.yaml", "subnets: ['10.30.0.0/24']\n")
    actual = _write(tmp_path, "a.yaml", "subnets: ['10.30.0.0/24']\n")
    rc = netdrift.main(["--desired", desired, "--actual", actual])
    assert rc == 0


def test_cli_exit_one_on_drift_with_json(tmp_path: Path, capsys):
    desired = _write(tmp_path, "d.yaml", "subnets: ['10.30.0.0/24']\n")
    actual = _write(tmp_path, "a.yaml", "subnets: ['10.30.1.0/24']\n")
    rc = netdrift.main(["--desired", desired, "--actual", actual, "--json"])
    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["missing_subnets"] == ["10.30.0.0/24"]


def test_cli_usage_error_on_missing_file(tmp_path: Path):
    rc = netdrift.main(["--desired", str(tmp_path / "nope.yaml"), "--actual", str(tmp_path / "nope2.yaml")])
    assert rc == 2
