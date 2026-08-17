#!/usr/bin/env python3
"""net-drift-check — compare a desired network state to an actual one.

Reads two YAML documents describing subnets and DNS records, reports any
drift between them, and exits non-zero when they disagree. The point is a
CI-friendly guardrail: infrastructure should not silently diverge from the
definition that is supposed to describe it.

Usage:
    netdrift.py --desired desired.yaml --actual actual.yaml [--json]

Exit codes:
    0  no drift
    1  drift detected
    2  usage / input error
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import sys
from dataclasses import dataclass, field
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only without pyyaml installed
    print("error: pyyaml is required (pip install -r requirements.txt)", file=sys.stderr)
    sys.exit(2)


@dataclass
class DriftReport:
    """Structured result of a desired-vs-actual comparison."""

    missing_subnets: list[str] = field(default_factory=list)
    unexpected_subnets: list[str] = field(default_factory=list)
    missing_dns: list[str] = field(default_factory=list)
    unexpected_dns: list[str] = field(default_factory=list)
    changed_dns: list[str] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return any(
            [
                self.missing_subnets,
                self.unexpected_subnets,
                self.missing_dns,
                self.unexpected_dns,
                self.changed_dns,
            ]
        )

    def as_dict(self) -> dict[str, list[str]]:
        return {
            "missing_subnets": self.missing_subnets,
            "unexpected_subnets": self.unexpected_subnets,
            "missing_dns": self.missing_dns,
            "unexpected_dns": self.unexpected_dns,
            "changed_dns": self.changed_dns,
        }


def normalize_cidr(cidr: str) -> str:
    """Return a canonical CIDR string, raising ValueError on bad input.

    Normalizing means 10.30.0.0/24 and 10.30.0.5/24 compare equal by network,
    so cosmetic host-bit differences are not reported as drift.
    """
    return str(ipaddress.ip_network(cidr, strict=False))


def _subnet_set(state: dict[str, Any]) -> set[str]:
    return {normalize_cidr(c) for c in state.get("subnets", []) or []}


def _dns_map(state: dict[str, Any]) -> dict[str, str]:
    records = state.get("dns_records", {}) or {}
    if not isinstance(records, dict):
        raise ValueError("dns_records must be a mapping of name -> value")
    return {str(k): str(v) for k, v in records.items()}


def compare(desired: dict[str, Any], actual: dict[str, Any]) -> DriftReport:
    """Compare desired and actual network state and return a DriftReport."""
    report = DriftReport()

    desired_subnets = _subnet_set(desired)
    actual_subnets = _subnet_set(actual)
    report.missing_subnets = sorted(desired_subnets - actual_subnets)
    report.unexpected_subnets = sorted(actual_subnets - desired_subnets)

    desired_dns = _dns_map(desired)
    actual_dns = _dns_map(actual)
    report.missing_dns = sorted(set(desired_dns) - set(actual_dns))
    report.unexpected_dns = sorted(set(actual_dns) - set(desired_dns))
    report.changed_dns = sorted(
        name
        for name in set(desired_dns) & set(actual_dns)
        if desired_dns[name] != actual_dns[name]
    )
    return report


def _load(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level YAML must be a mapping")
    return data


def render_text(report: DriftReport) -> str:
    if not report.has_drift:
        return "OK: no drift between desired and actual network state."
    lines = ["DRIFT DETECTED:"]
    labels = [
        ("missing_subnets", "Subnets in desired but not actual"),
        ("unexpected_subnets", "Subnets in actual but not desired"),
        ("missing_dns", "DNS records missing from actual"),
        ("unexpected_dns", "DNS records present but not desired"),
        ("changed_dns", "DNS records whose value differs"),
    ]
    data = report.as_dict()
    for key, label in labels:
        if data[key]:
            lines.append(f"  {label}:")
            lines.extend(f"    - {item}" for item in data[key])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare desired vs actual network state.")
    parser.add_argument("--desired", required=True, help="Path to desired-state YAML.")
    parser.add_argument("--actual", required=True, help="Path to actual-state YAML.")
    parser.add_argument("--json", action="store_true", help="Emit the report as JSON.")
    args = parser.parse_args(argv)

    try:
        desired = _load(args.desired)
        actual = _load(args.actual)
        report = compare(desired, actual)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print(render_text(report))
    return 1 if report.has_drift else 0


if __name__ == "__main__":
    raise SystemExit(main())
