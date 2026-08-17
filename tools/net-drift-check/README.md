# net-drift-check

A small, tested network-automation CLI. It compares a **desired** network state (subnets + DNS records) to an **actual** one and exits non-zero on drift — the kind of guardrail you wire into CI so infrastructure can't quietly diverge from its definition.

This is deliberately the same idea as the drift/validation discipline I run in my homelab (pre-build "is this subnet/IP free?" checks, config baselines), but here it's real Python with tests instead of shell one-offs.

## Run it

```bash
python3 -m pip install -r requirements.txt
python3 netdrift.py --desired expected.example.yaml --actual actual.example.yaml
# non-zero exit + a drift report, because actual.example.yaml intentionally drifts
python3 netdrift.py --desired expected.example.yaml --actual expected.example.yaml
# exit 0 — no drift
```

## Test it

```bash
python3 -m pytest -q
```

## Design notes

- CIDRs are **normalized** (`ipaddress`), so `10.30.0.5/24` and `10.30.0.0/24` compare equal by network — cosmetic host-bit differences aren't false-positive drift.
- The comparison is pure and returns a structured `DriftReport`; the CLI is a thin wrapper. That separation is what makes it easy to test and easy to embed in a pipeline.
- `--json` emits machine-readable output for CI consumption.
- Exit codes: `0` no drift, `1` drift, `2` usage/input error.
