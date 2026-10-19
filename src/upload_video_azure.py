#!/usr/bin/env python3
"""Upload a rendered Reel to Azure Blob Storage and print a time-limited read URL.

Required environment:
  AZURE_STORAGE_CONNECTION_STRING
  AZURE_STORAGE_CONTAINER
Optional:
  AZURE_BLOB_NAME (defaults to output filename)
  AZURE_SAS_HOURS (default 48; bounded to 1..168)
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas
from azure.core.exceptions import AzureError


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "output/best-phone-ringtones-reel.mp4")
    if not path.is_file() or path.stat().st_size < 1024:
        raise RuntimeError(f"Rendered MP4 is missing or too small: {path}")

    connection = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "").strip()
    container = os.getenv("AZURE_STORAGE_CONTAINER", "").strip()
    if not connection or not container:
        raise RuntimeError("Set AZURE_STORAGE_CONNECTION_STRING and AZURE_STORAGE_CONTAINER as GitHub Actions secrets/variables.")

    hours = int(os.getenv("AZURE_SAS_HOURS", "48"))
    if not 1 <= hours <= 168:
        raise ValueError("AZURE_SAS_HOURS must be between 1 and 168.")

    service = BlobServiceClient.from_connection_string(connection)
    account_name = service.account_name
    account_key = None
    for part in connection.split(";"):
        if part.startswith("AccountKey="):
            account_key = part.split("=", 1)[1]
            break
    if not account_name or not account_key:
        raise RuntimeError("Azure connection string must include AccountName and AccountKey.")

    blob_name = os.getenv("AZURE_BLOB_NAME", f"reels/{datetime.now(timezone.utc):%Y/%m/%d}/{path.name}")
    blob = service.get_blob_client(container=container, blob=blob_name)
    with path.open("rb") as data:
        blob.upload_blob(data, overwrite=True, content_settings=__import__("azure.storage.blob", fromlist=["ContentSettings"]).ContentSettings(content_type="video/mp4", cache_control="public, max-age=3600"))

    now = datetime.now(timezone.utc)
    sas = generate_blob_sas(
        account_name=account_name,
        container_name=container,
        blob_name=blob_name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        start=now - timedelta(minutes=5),
        expiry=now + timedelta(hours=hours),
        protocol="https",
    )
    url = f"{blob.url}?{sas}"
    print(f"PUBLIC_VIDEO_URL={url}")
    print(f"Uploaded {path.stat().st_size} bytes to Azure Blob Storage.")
    print(f"Read SAS expires in {hours} hours.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AzureError, ValueError, RuntimeError) as exc:
        print(f"Azure video upload failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
