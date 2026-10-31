#!/usr/bin/env python3
import urllib.request
import urllib.error
import json
import http.cookiejar
import time
import os
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ZIP_PATH = BASE_DIR / "memoryquarantine_submission.zip"
OUT_PDF = BASE_DIR / "paper_revised.pdf"
MQ_PDF = BASE_DIR / "memoryquarantine.pdf"
REPORT_PATH = BASE_DIR / "ieee_latexqc_report_memoryquarantine.json"
PUB_ID = "491"

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

print("1. Initializing session and generating token...")
req_token = urllib.request.Request(
    "https://latexqc.ieee.org/api/conversion/make-token",
    data=b"{}",
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json",
        "Referer": "https://latexqc.ieee.org/upload",
    },
)
resp_token = opener.open(req_token)
token_data = json.loads(resp_token.read().decode())
token = token_data["token"]
print(f"   Token: {token[:30]}...")

cookie_token = http.cookiejar.Cookie(
    version=0,
    name="token",
    value=token,
    port=None,
    port_specified=False,
    domain="latexqc.ieee.org",
    domain_specified=True,
    domain_initial_dot=False,
    path="/",
    path_specified=True,
    secure=True,
    expires=None,
    discard=False,
    comment=None,
    comment_url=None,
    rest={"HttpOnly": None},
    rfc2109=False,
)
cookie_pub = http.cookiejar.Cookie(
    version=0,
    name="pubId",
    value=PUB_ID,
    port=None,
    port_specified=False,
    domain="latexqc.ieee.org",
    domain_specified=True,
    domain_initial_dot=False,
    path="/",
    path_specified=True,
    secure=True,
    expires=None,
    discard=False,
    comment=None,
    comment_url=None,
    rest={"HttpOnly": None},
    rfc2109=False,
)
cj.set_cookie(cookie_token)
cj.set_cookie(cookie_pub)

print("2. Requesting signed S3 upload URL...")
req_sign = urllib.request.Request(
    "https://latexqc.ieee.org/api/aws/sign-s3",
    data=json.dumps({"fileType": "application/x-zip-compressed"}).encode(),
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Referer": "https://latexqc.ieee.org/upload",
    },
)
resp_sign = opener.open(req_sign)
sign_data = json.loads(resp_sign.read().decode())
s3_url = sign_data["signedResponse"]

print(f"3. Uploading {ZIP_PATH.name} ({ZIP_PATH.stat().st_size / 1024:.1f} KB) to S3...")
with open(ZIP_PATH, "rb") as f:
    zip_bytes = f.read()

req_put = urllib.request.Request(
    s3_url,
    data=zip_bytes,
    headers={"Content-Type": "application/x-zip-compressed"},
    method="PUT",
)
resp_put = urllib.request.urlopen(req_put)
print(f"   Upload status: {resp_put.status}")

print("4. Triggering IEEE LaTeX Analyzer conversion...")
req_send = urllib.request.Request(
    "https://latexqc.ieee.org/api/conversion/send-zip",
    data=b"{}",
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Referer": "https://latexqc.ieee.org/upload",
    },
)
resp_send = opener.open(req_send)
print(f"   Conversion triggered: {resp_send.status}")

print("5. Polling conversion report...")
report_data = None
for i in range(60):
    time.sleep(2)
    req_rep = urllib.request.Request(
        "https://latexqc.ieee.org/api/conversion/get-report",
        data=b"{}",
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Referer": "https://latexqc.ieee.org/upload",
        },
    )
    resp_rep = opener.open(req_rep)
    report_data = json.loads(resp_rep.read().decode())
    overview = report_data.get("overview", {}).get("data", {})
    delivered_at = overview.get("deliveredAt")
    status = overview.get("status")
    err_count = overview.get("errorsCount", 0)
    warn_count = overview.get("warningsCount", 0)
    print(
        f"   [Poll {i+1}] status={status}, deliveredAt={delivered_at}, errors={err_count}, warnings={warn_count}"
    )
    if delivered_at is not None:
        break

with open(REPORT_PATH, "w", encoding="utf-8") as f:
    json.dump(report_data, f, indent=2)
print(f"Saved verification report to {REPORT_PATH.name}")

pdf_uri = report_data.get("pdf", {}).get("data", {}).get("pdfUri")
if pdf_uri:
    print(f"6. Downloading compiled PDF from {pdf_uri[:60]}...")
    urllib.request.urlretrieve(pdf_uri, OUT_PDF)
    print(f"   SUCCESS! Downloaded {OUT_PDF.name} ({OUT_PDF.stat().st_size / (1024*1024):.2f} MB)")
    shutil.copy2(OUT_PDF, MQ_PDF)
    print(f"   SUCCESS! Copied to {MQ_PDF.name}")
else:
    print("Failed to get PDF URI. Report details:")
    print(json.dumps(report_data, indent=2))
