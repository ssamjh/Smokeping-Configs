#!/usr/bin/env python3
"""
check_endpoints.py - Validate all host endpoints in Smokeping .conf files

Usage:
    python check_endpoints.py                     # check all .conf files
    python check_endpoints.py vultr.conf           # check one file
    python check_endpoints.py vultr.conf dns.conf  # check multiple files
    python check_endpoints.py --resolve-only       # DNS only (fast)
    python check_endpoints.py --ping-only          # ping only
    python check_endpoints.py --timeout 5          # custom timeout
"""

import argparse
import glob
import os
import platform
import re
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# Colors (disabled if not a TTY)
if sys.stdout.isatty():
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[0;33m"
    BOLD = "\033[1m"
    NC = "\033[0m"
else:
    RED = GREEN = YELLOW = BOLD = NC = ""

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def parse_hosts(filepath):
    """Extract all host values from a .conf file."""
    hosts = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            match = re.match(r"^\s*host\s*=\s*(.+)$", line)
            if match:
                host = match.group(1).strip()
                if host:
                    hosts.append(host)
    return hosts


def is_ip(host):
    """Check if host is an IP address (v4 or v6)."""
    try:
        socket.inet_pton(socket.AF_INET, host)
        return True
    except OSError:
        pass
    try:
        socket.inet_pton(socket.AF_INET6, host)
        return True
    except OSError:
        return False


def check_dns(host):
    """Resolve a hostname via DNS. Returns (success, detail)."""
    if is_ip(host):
        return True, "ip"
    try:
        results = socket.getaddrinfo(host, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        ip = results[0][4][0] if results else None
        return True, ip
    except socket.gaierror as e:
        return False, str(e)


def check_ping(host, timeout):
    """Ping a host once. Returns True if reachable."""
    is_windows = platform.system().lower() == "windows"
    count_flag = "-n" if is_windows else "-c"
    timeout_flag = "-w" if is_windows else "-W"
    timeout_val = str(timeout * 1000) if is_windows else str(timeout)

    cmd = ["ping", count_flag, "1", timeout_flag, timeout_val, host]
    try:
        result = subprocess.run(
            cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout + 5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_endpoint(file, host, mode, timeout):
    """Run all checks for a single endpoint. Returns a result dict."""
    label = f"{file}: {host}"
    result = {"label": label, "file": file, "host": host}

    if mode in ("resolve", "both"):
        if is_ip(host):
            result["dns"] = "skip"
        else:
            ok, detail = check_dns(host)
            result["dns"] = "pass" if ok else "fail"
            result["dns_detail"] = detail

    if mode in ("ping", "both"):
        result["ping"] = "pass" if check_ping(host, timeout) else "fail"

    return result


def main():
    parser = argparse.ArgumentParser(description="Validate Smokeping .conf endpoints")
    parser.add_argument("files", nargs="*", help="Config files to check (default: all *.conf)")
    parser.add_argument("--resolve-only", action="store_true", help="Only check DNS resolution")
    parser.add_argument("--ping-only", action="store_true", help="Only check ping reachability")
    parser.add_argument("--timeout", type=int, default=3, help="Ping timeout in seconds (default: 3)")
    parser.add_argument("--workers", type=int, default=20, help="Parallel workers (default: 20)")
    args = parser.parse_args()

    mode = "both"
    if args.resolve_only:
        mode = "resolve"
    elif args.ping_only:
        mode = "ping"

    # Resolve file paths
    if args.files:
        files = []
        for f in args.files:
            path = f if os.path.isabs(f) else os.path.join(os.getcwd(), f)
            if not os.path.isfile(path):
                print(f"Error: file not found: {f}")
                sys.exit(1)
            files.append(path)
    else:
        files = sorted(glob.glob(os.path.join(SCRIPT_DIR, "*.conf")))
        if not files:
            print("No .conf files found.")
            sys.exit(1)

    # Collect endpoints
    entries = []
    for filepath in files:
        filename = os.path.basename(filepath)
        for host in parse_hosts(filepath):
            entries.append((filename, host))

    total = len(entries)
    print(f"{BOLD}Smokeping Endpoint Validator{NC}")
    print(f"{BOLD}============================{NC}")
    print()
    print(f"Found {BOLD}{total}{NC} endpoints across {BOLD}{len(files)}{NC} config file(s).")
    print()

    # Run checks in parallel
    results = []
    checked = 0

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(check_endpoint, f, h, mode, args.timeout): (f, h)
            for f, h in entries
        }
        for future in as_completed(futures):
            checked += 1
            print(f"\r  Checking... [{checked}/{total}]", end="", flush=True)
            results.append(future.result())

    # Sort results back into original order
    order = {(f, h): i for i, (f, h) in enumerate(entries)}
    results.sort(key=lambda r: order[(r["file"], r["host"])])

    print(f"\r{' ' * 40}\r", end="")

    # Categorize
    dns_passed, dns_failed, dns_skipped = [], [], []
    ping_passed, ping_failed = [], []

    for r in results:
        if "dns" in r:
            if r["dns"] == "pass":
                dns_passed.append(r)
            elif r["dns"] == "fail":
                dns_failed.append(r)
            else:
                dns_skipped.append(r)
        if "ping" in r:
            if r["ping"] == "pass":
                ping_passed.append(r)
            else:
                ping_failed.append(r)

    # Print result lists
    if mode in ("resolve", "both"):
        if dns_passed:
            print(f"{GREEN}{BOLD}DNS Resolved ({len(dns_passed)}):{NC}")
            for r in dns_passed:
                detail = r.get("dns_detail", "")
                print(f"  {GREEN}+{NC} {r['label']}  ->  {detail}")
            print()

        if dns_failed:
            print(f"{RED}{BOLD}DNS Failed ({len(dns_failed)}):{NC}")
            for r in dns_failed:
                detail = r.get("dns_detail", "")
                print(f"  {RED}x{NC} {r['label']}  ({detail})")
            print()

        if dns_skipped:
            print(f"{YELLOW}{BOLD}DNS Skipped - IP address ({len(dns_skipped)}):{NC}")
            for r in dns_skipped:
                print(f"  {YELLOW}-{NC} {r['label']}")
            print()

    if mode in ("ping", "both"):
        if ping_passed:
            print(f"{GREEN}{BOLD}Ping Reachable ({len(ping_passed)}):{NC}")
            for r in ping_passed:
                print(f"  {GREEN}+{NC} {r['label']}")
            print()

        if ping_failed:
            print(f"{RED}{BOLD}Ping Unreachable ({len(ping_failed)}):{NC}")
            for r in ping_failed:
                print(f"  {RED}x{NC} {r['label']}")
            print()

    # Summary
    print(f"{BOLD}============================{NC}")
    print(f"{BOLD}Summary{NC}")
    print(f"{BOLD}============================{NC}")
    print(f"Total endpoints: {BOLD}{total}{NC}")

    if mode in ("resolve", "both"):
        print(
            f"DNS:  {GREEN}{len(dns_passed)} passed{NC}  "
            f"{RED}{len(dns_failed)} failed{NC}  "
            f"{YELLOW}{len(dns_skipped)} skipped{NC}"
        )
    if mode in ("ping", "both"):
        print(
            f"Ping: {GREEN}{len(ping_passed)} passed{NC}  "
            f"{RED}{len(ping_failed)} failed{NC}"
        )

    if dns_failed or ping_failed:
        print()
        print(f"{RED}{BOLD}Some endpoints failed validation.{NC}")
        sys.exit(1)
    else:
        print()
        print(f"{GREEN}{BOLD}All endpoints passed validation.{NC}")


if __name__ == "__main__":
    main()
