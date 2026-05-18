#!/usr/bin/env python3
"""
update_oraclecloud.py - Update oraclecloud.conf host IPs from Oracle's IP ranges data.

Fetches https://docs.oracle.com/en-us/iaas/tools/public_ip_ranges.json, pings each
candidate IP twice to verify reachability, and uses the first responding IP
per region. OBJECT_STORAGE-tagged CIDRs are tried first (matching the object
storage endpoints the conf currently targets), then OCI-tagged CIDRs as
fallback. If no IP responds, the first OBJECT_STORAGE candidate is used.

Usage:
    python update_oraclecloud.py
    python update_oraclecloud.py --conf path/to/oraclecloud.conf
    python update_oraclecloud.py --dry-run
    python update_oraclecloud.py --timeout 2 --workers 30
"""

import argparse
import ipaddress
import json
import os
import platform
import re
import subprocess
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONF = os.path.join(SCRIPT_DIR, "oraclecloud.conf")
JSON_URL = "https://docs.oracle.com/en-us/iaas/tools/public_ip_ranges.json"
IS_WINDOWS = platform.system().lower() == "windows"


def cidr_to_ip(cidr):
    """Return the network address of a CIDR as a string."""
    return str(ipaddress.ip_network(cidr, strict=False).network_address)


def fetch_region_candidates(url):
    """Fetch JSON and return {region: [ip, ...]} ordered OBJECT_STORAGE first, then OCI."""
    print(f"Fetching {url} ...")
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"Error fetching JSON: {e}")
        sys.exit(1)

    region_candidates = {}
    for entry in data.get("regions", []):
        region = entry["region"]
        cidrs = entry.get("cidrs", [])

        object_storage = [cidr_to_ip(c["cidr"]) for c in cidrs if "OBJECT_STORAGE" in c.get("tags", [])]
        oci = [cidr_to_ip(c["cidr"]) for c in cidrs if "OCI" in c.get("tags", [])]

        candidates = object_storage + oci
        if candidates:
            region_candidates[region] = candidates

    print(f"  Got candidates for {len(region_candidates)} regions.")
    return region_candidates


def ping_twice(ip, timeout):
    """Return True if ip responds to both of two consecutive pings."""
    count_flag = "-n" if IS_WINDOWS else "-c"
    timeout_flag = "-w" if IS_WINDOWS else "-W"
    timeout_val = str(timeout * 1000) if IS_WINDOWS else str(timeout)
    cmd = ["ping", count_flag, "1", timeout_flag, timeout_val, ip]

    for _ in range(2):
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=timeout + 2,
            )
            if result.returncode != 0:
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    return True


def find_best_ip(region, candidates, timeout):
    """Return (region, chosen_ip, reachable) — first IP that passes ping_twice, else candidates[0]."""
    for ip in candidates:
        if ping_twice(ip, timeout):
            return region, ip, True
    return region, candidates[0], False


def resolve_region_ips(region_candidates, timeout, workers):
    """Probe all regions in parallel and return {region: ip}."""
    total = len(region_candidates)
    print(f"Pinging IPs for {total} regions (up to {workers} parallel, {timeout}s timeout) ...")

    region_ips = {}
    fallbacks = []
    done = 0

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(find_best_ip, region, ips, timeout): region
            for region, ips in region_candidates.items()
        }
        for future in as_completed(futures):
            region, ip, reachable = future.result()
            region_ips[region] = ip
            if not reachable:
                fallbacks.append((region, ip))
            done += 1
            print(f"\r  Probed {done}/{total} regions ...", end="", flush=True)

    print(f"\r  Probed {total}/{total} regions.        ")

    if fallbacks:
        print(f"  Fallback to first IP (no response) for {len(fallbacks)} region(s):")
        for region, ip in sorted(fallbacks):
            print(f"    {region:<28} {ip}")

    return region_ips


def update_conf(conf_path, region_ips, dry_run=False):
    """Rewrite conf_path replacing each host line using region from its title."""
    with open(conf_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    updated = []
    current_region = None
    changes = []
    conf_regions = set()

    for i, line in enumerate(lines):
        # Extract region from title lines like: title = Some Place - us-ashburn-1
        title_match = re.match(r"^(title\s*=\s*.+?-\s*)([a-z]{2}[-a-z0-9]+)\s*$", line)
        if title_match:
            current_region = title_match.group(2)
            conf_regions.add(current_region)
            updated.append(line)
            continue

        # Replace host lines when we have a known region
        host_match = re.match(r"^(host\s*=\s*)(.+)$", line)
        if host_match and current_region:
            if current_region in region_ips:
                new_ip = region_ips[current_region]
                old_val = host_match.group(2).strip()
                new_line = f"{host_match.group(1)}{new_ip}\n"
                if old_val != new_ip:
                    changes.append((i + 1, current_region, old_val, new_ip))
                updated.append(new_line)
            else:
                print(f"  Warning: no IP found for region '{current_region}', keeping existing host.")
                updated.append(line)
            current_region = None
            continue

        # Reset region tracking when we leave a +++ block
        if re.match(r"^\+{1,3}\s", line):
            current_region = None

        updated.append(line)

    remote_regions = set(region_ips.keys())
    stale = sorted(conf_regions - remote_regions)
    missing = sorted(remote_regions - conf_regions)

    if stale:
        print(f"\n  Stale regions in conf (no longer in OCI data) — consider removing ({len(stale)}):")
        for r in stale:
            print(f"    {r}")

    if missing:
        print(f"\n  New regions in OCI data not yet in conf — consider adding ({len(missing)}):")
        for r in missing:
            ip = region_ips[r]
            print(f"    {r}  ({ip})")
            print(f"      +++ <slug>")
            print(f"      menu = <Human Name>")
            print(f"      title = <Human Name> - {r}")
            print(f"      host = {ip}")
            print()

    if not changes:
        print("No changes needed — all hosts are already up to date.")
        return

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Changes ({len(changes)}):")
    for lineno, region, old, new in changes:
        print(f"  line {lineno:3d}  {region:<28}  {old}  ->  {new}")

    if not dry_run:
        with open(conf_path, "w", encoding="utf-8") as f:
            f.writelines(updated)
        print(f"\nUpdated {conf_path}")


def main():
    parser = argparse.ArgumentParser(description="Update oraclecloud.conf with latest reachable OCI IPs")
    parser.add_argument("--conf", default=DEFAULT_CONF, help="Path to oraclecloud.conf")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    parser.add_argument("--timeout", type=int, default=2, help="Ping timeout in seconds (default: 2)")
    parser.add_argument("--workers", type=int, default=20, help="Parallel workers (default: 20)")
    args = parser.parse_args()

    if not os.path.isfile(args.conf):
        print(f"Error: config file not found: {args.conf}")
        sys.exit(1)

    region_candidates = fetch_region_candidates(JSON_URL)
    region_ips = resolve_region_ips(region_candidates, args.timeout, args.workers)
    update_conf(args.conf, region_ips, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
