# cloud-netlab

> **At a glance**
> - **Problem:** translate the network segmentation I run on-prem (VLANs, subnets, firewall policy) into reviewable, tested AWS infrastructure-as-code.
> - **Architecture:** a reusable `network` module (VPC, public/private subnets across AZs, IGW, routing, baseline security group) consumed by a `dev` environment; remote-state intent stubbed.
> - **Tech:** OpenTofu/Terraform (HCL), Python, pytest, GitHub Actions.
> - **Testing:** 101 pytest cases on the drift tool (pure logic + CLI, including security-group rule drift); `tofu validate` on the IaC.
> - **CI:** every push/PR runs `tofu fmt -check` + `validate` and `pytest` (green).
> - **Security:** no credentials/state/tfvars committed (`*.example` only); baseline SG is deny-inbound/allow-egress.
> - **What was actually run:** Locally, `tofu fmt`, `init -backend=false`, `validate`, and the full pytest suite pass. CI runs formatting/validation checks and the pytest suite on every push and pull request. No cloud resources were applied.
> - **Limitations (honest):** this is a **lab**. It demonstrates AWS IaC authoring, module design, and CI-gated testing; it does **not** represent production/enterprise AWS operations, multi-account architecture, or IAM/governance at scale.

AWS **networking-as-code** with a real CI gate and a small, tested Python network-automation tool. Built to close two specific, honestly-identified gaps between my homelab work and a Software Engineer II (platform / network automation) role:

1. **AWS + Terraform hands-on.** My existing IaC (OpenTofu against Proxmox) proves lifecycle design and blast-radius discipline, but it isn't AWS. This repo is AWS, targeted.
2. **Tested application code.** My other automation is Bash/utility scripting; this repo ships Python with `pytest` tests and CI, not just scripts.

I picked *networking* on AWS on purpose: VPCs, subnets, routing, security groups. It's the same mental model I already run by hand at home (VLANs, subnets, firewall rules, HA DNS), expressed as reviewable code against a cloud provider.

## What's here

```
iac/
  modules/network/      reusable VPC/subnets/routing/SG module (not copy-pasted HCL)
  environments/dev/     consumes the module; one place to plan/apply
tools/
  net-drift-check/      tested Python CLI: compares desired vs actual network state, exits non-zero on drift
scripts/
  ci-local.sh           the same checks CI runs, runnable locally
.github/workflows/
  ci.yml                fmt + validate (IaC) and pytest (tool) on every push/PR
docs/
  why-this-exists.md    the honest gap-to-evidence mapping
```

## The IaC

A reusable `network` module (VPC, public + private subnets across AZs, internet gateway, route table, baseline deny-inbound/allow-egress security group) consumed by an `environments/dev` root. Terraform and OpenTofu both run this: `terraform` and `tofu` are drop-in for these files.

```bash
cd iac/environments/dev
tofu fmt -recursive          # or terraform fmt
tofu init -backend=false     # no AWS creds needed to validate
tofu validate
# tofu plan                  # needs AWS creds; free-tier friendly
```

`fmt`, `init -backend=false`, and `validate` need **no** AWS account, so the whole thing is CI-checkable and reviewable without ever spending a cent. `plan`/`apply` are the only steps that touch AWS.

## The tool: net-drift-check

A small network-automation CLI that reads a **desired** network state (subnets, CIDRs, DNS records, and optional security-group rules in YAML) and an **actual** state, reports drift, and exits non-zero when they disagree. It's the kind of guardrail you'd wire into CI so infrastructure can't silently diverge from its definition.

```bash
cd tools/net-drift-check
python3 -m pip install -r requirements.txt
python3 netdrift.py --desired expected.example.yaml --actual actual.example.yaml
python3 -m pytest -q          # tests
```

## CI

`.github/workflows/ci.yml` runs on every push/PR: `tofu fmt -check` + `validate`, and `pytest` for the tool. `scripts/ci-local.sh` runs the identical checks locally (and a pre-commit hook can call it). If GitHub-hosted runners aren't available in a given org, the local script is the enforcement path, the same pattern I use at work.

## Evidence still needed

Unlike the on-prem repos, this one has no screenshots yet, because it's more
CLI/IaC-native. Before writing it up publicly, capture: a passing GitHub
Actions CI run, `net-drift-check` CLI output showing detected drift, and
the AWS console VPC view.

## Honesty

This is a lab, and it says so. It demonstrates AWS IaC authoring, reusable module design, remote-state intent, CI-gated infrastructure, and tested Python automation. It does **not** claim production AWS operations at scale. It's the bridge artifact between "I understand this" and "here's me doing it," and it's paired with a real homelab that already operates the on-prem equivalents.

No credentials, account IDs, or state files are committed (`*.tfvars`, `*.tfstate`, `.env` are gitignored; only `*.example` is tracked).
