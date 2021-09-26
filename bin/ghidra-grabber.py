#!/usr/bin/env python3

import argparse
import glob
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import requests
from pathlib import Path

import plistlib


def getReleases():
    r = requests.get('https://api.github.com/repos/nationalsecurityagency/ghidra/releases')
    releases = r.json()
    releases = sorted(releases, key=lambda x: x["created_at"], reverse=True)
    return releases

def listVersions():
    releases = getReleases()
    for release in releases:
        vers = release["name"].split(" ")[1]
        print(f"\t{vers}")


parser = argparse.ArgumentParser()
parser.add_argument('-u', '--url', help='Ghidra zip URL. Defaults to latest from Github')
parser.add_argument(
        '-p', '--path', help='Path to Ghidra zip or install', type=Path)
parser.add_argument('-v', '--version', dest='version', required=False,
                    help='Set the version for the dmg. Eg: "9.1 BETA"')
parser.add_argument('--extension', type=Path, nargs='*', help='Path to a Ghidra extension zip to install')
parser.add_argument('--list-versions', action='store_true', help='Print available Ghidra versions')

parser.add_argument('OUTPUT', type=Path, help="Path to install Ghidra to")

args = parser.parse_args()

if args.version == 'latest':
    args.version = None

if args.list_versions:
    print("[+] Available Ghidra versions from Github:")
    listVersions()
    exit(0)

if args.OUTPUT.is_dir():
    print(f"[!!] Directory already exists at {args.OUTPUT}.")
    exit(1)

with tempfile.TemporaryDirectory() as tmp_dir:
    ghidra_content = None
    ghidra_zip_name = None
    dest_path = Path(tmp_dir)

    if not args.url and not args.path and not args.version:
        print("[!] No URL or path provided, getting latest from github")
        releases = getReleases()
        release = releases[0] # The latest release
        args.version = release["name"].split(" ")[1]
        args.url = release["assets"][0]["browser_download_url"]
        print(f"[+] Fetching {args.version} from {args.url}")
    elif args.version and not args.url and not args.path:
        # If we have a version and not a path or URL, we'll get that specific release
        releases = getReleases()
        for release in releases:
            if args.version in release["name"]:
                # Found it
                args.url = release["assets"][0]["browser_download_url"]
                print(f"[+] Found version {args.version} on Github @ {args.url}")
        if not args.url:
            print(f"[!] Failed to find version {args.version} on Github. Found:")
            listVersions()
            exit(1)


    if args.path:
        print("[-] Will use Ghidra from {}".format(args.path))
        ghidra_zip_name = Path(args.path).name
    elif args.url:
        print("[+] Downloading {}".format(args.url))
        download = requests.get(args.url)
        ghidra_zip_name = Path(args.url).name

        if download.status_code == 200:
            ghidra_content = download.content
        else:
            print('[!] Failed to download!')
            sys.exit(1)
    else:
        print("[!] Neither path nor url were specified!")
        sys.exit(1)

    # calculate the name from a path
    if ghidra_zip_name:
        version = ghidra_zip_name.split('ghidra_')[1].split('_')[0]
    if args.version:
        version = args.version
    

    if args.url:
       print("[+] Extracting...")
       with tempfile.TemporaryDirectory() as zip_dir:
           zip_path = os.path.join(zip_dir, 'Ghidra.zip')
           with open(zip_path, 'wb') as f:
               f.write(ghidra_content)
           subprocess.run(f'unzip -d "{dest_path}" "{zip_path}"', shell=True)
       print("[+] Extracted to {}".format(dest_path))

    if args.path:
        if args.path.is_file():
            print("[+] Opening {}".format(args.path))
            with open(args.path, 'rb') as f:
                ghidra_content = f.read()
            print("[+] Extracting...")
            with tempfile.TemporaryDirectory() as zip_dir:
                zip_path = os.path.join(zip_dir, 'Ghidra.zip')
                with open(zip_path, 'wb') as f:
                    f.write(ghidra_content)
                subprocess.run(f'unzip -d "{dest_path}" "{zip_path}"', shell=True)
            print("[+] Extracted to {}".format(dest_path))
        elif args.path.is_dir():
            print("[+] Copying...")
            shutil.copytree(args.path, dest_path / args.path.name)
            print("[+] Copied to {}".format(dest_path / args.path.name))

    # Install any extensions
    ghidra_install_dir = None
    try:
        ghidra_install_dir = next(dest_path.glob(f'ghidra_{version}*'))
    except IndexError as e:
        raise Exception(f"Ghidra was not installed into {dest_path}, is the Ghidra zip correctly structured?", e)
    # If we don't have an install dir matching this format, the launch
    # script won't work, so we might as well die here
    extension_dir = ghidra_install_dir.joinpath("Ghidra", "Extensions")
    if args.extension:
        for extension in args.extension:
            print("[+] Installing extension: {extension}")
            subprocess.run(f'unzip -d "{extension_dir}" "{extension}"', shell=True)

    if args.OUTPUT:
        shutil.copytree(ghidra_install_dir, args.OUTPUT)
        print(f"[+] Saved to {args.OUTPUT}")
