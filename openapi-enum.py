#!/usr/bin/env python3

import argparse
import json
import yaml
import re
import os
import subprocess
import requests
from urllib.parse import urljoin

DEFAULT_FUZZ = "FUZZ"


def load_openapi_from_file(path):
    with open(path, "r") as f:
        if path.endswith(".yaml") or path.endswith(".yml"):
            return yaml.safe_load(f)
        return json.load(f)


def load_openapi_from_url(url):
    r = requests.get(url, timeout=30)
    r.raise_for_status()

    try:
        return r.json()
    except Exception:
        return yaml.safe_load(r.text)


def get_base_urls(spec):
    bases = []

    # OpenAPI v3
    if "servers" in spec:
        for s in spec["servers"]:
            url = s.get("url")
            if url:
                bases.append(url)

    # OpenAPI v2 (Swagger)
    elif "host" in spec:
        scheme = "https"
        if "schemes" in spec and len(spec["schemes"]) > 0:
            scheme = spec["schemes"][0]

        base_path = spec.get("basePath", "")
        bases.append(f"{scheme}://{spec['host']}{base_path}")

    return bases


def fuzz_path(path, fuzz_value):
    return re.sub(r"\{.*?\}", fuzz_value, path)


def extract_endpoints(spec, fuzz_value):
    paths = spec.get("paths", {})
    endpoints = []

    for path, methods in paths.items():
        fuzzed = fuzz_path(path, fuzz_value)

        for method in methods.keys():
            endpoints.append((method.upper(), fuzzed))

    return endpoints


def build_urls(bases, endpoints):
    urls = []

    for base in bases:
        for method, path in endpoints:
            full = urljoin(base.rstrip("/") + "/", path.lstrip("/"))
            urls.append((method, full))

    return urls


def ensure_output_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def write_outputs(urls, outdir):
    all_urls = set()
    get_urls = set()
    post_urls = set()

    for method, url in urls:
        all_urls.add(url)

        if method == "GET":
            get_urls.add(url)

        if method == "POST":
            post_urls.add(url)

    all_path = os.path.join(outdir, "endpoints_all.txt")
    get_path = os.path.join(outdir, "endpoints_get.txt")
    post_path = os.path.join(outdir, "endpoints_post.txt")

    with open(all_path, "w") as f:
        f.write("\n".join(sorted(all_urls)))

    with open(get_path, "w") as f:
        f.write("\n".join(sorted(get_urls)))

    with open(post_path, "w") as f:
        f.write("\n".join(sorted(post_urls)))

    return all_path


def run_httpx(input_file, outdir):
    output = os.path.join(outdir, "httpx_alive.txt")

    print("[+] Running httpx to probe endpoints...")

    try:
        subprocess.run(
            [
                "httpx",
                "-l", input_file,
                "-silent",
                "-status-code",
                "-mc", "200",
                "-o", output
            ],
            check=True
        )
    except FileNotFoundError:
        print("[-] httpx not found in PATH. Skipping probing.")
        return

    print(f"[+] httpx results saved to: {output}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract endpoints from OpenAPI specs and probe them with httpx"
    )

    parser.add_argument(
        "-i",
        "--input",
        help="OpenAPI specification file (json/yaml)"
    )

    parser.add_argument(
        "-u",
        "--url",
        help="Remote OpenAPI specification URL"
    )

    parser.add_argument(
        "--fuzz-value",
        default=DEFAULT_FUZZ,
        help="Value used to replace path parameters (default: FUZZ)"
    )

    parser.add_argument(
        "-o",
        "--output",
        default="results",
        help="Output directory"
    )

    args = parser.parse_args()

    if not args.input and not args.url:
        print("[-] You must provide either an input file (-i) or a URL (-u)")
        return

    print("[+] Loading OpenAPI specification...")

    try:
        if args.input:
            spec = load_openapi_from_file(args.input)
        else:
            spec = load_openapi_from_url(args.url)
    except Exception as e:
        print(f"[-] Failed to load specification: {e}")
        return

    bases = get_base_urls(spec)

    if not bases:
        print("[-] No base URLs found in specification")
        return

    print(f"[+] Found {len(bases)} base URL(s)")

    endpoints = extract_endpoints(spec, args.fuzz_value)

    print(f"[+] Extracted {len(endpoints)} endpoints")

    urls = build_urls(bases, endpoints)

    ensure_output_dir(args.output)

    all_file = write_outputs(urls, args.output)

    print("[+] Endpoint lists generated")

    run_httpx(all_file, args.output)

    print("[+] Done.")


if __name__ == "__main__":
    main()
