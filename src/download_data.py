import io
import zipfile
from pathlib import Path

import requests

BASE = "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action"
PACKAGE = "311-service-requests-customer-initiated"
RESOURCE_NAME = "311 Service Requests 2025"
DEST = Path("data/raw")

# 1. Ask the API which files exist, and pick the one we want
meta = requests.get(f"{BASE}/package_show", params={"id": PACKAGE}, timeout=30)
meta.raise_for_status()
resources = meta.json()["result"]["resources"]
resource = next(r for r in resources if r["name"] == RESOURCE_NAME)

# 2. Download the ZIP from the address the API gave us
print("Downloading:", resource["url"])
file_response = requests.get(resource["url"], timeout=120)
file_response.raise_for_status()

# 3. Unzip it into data/raw
DEST.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(io.BytesIO(file_response.content)) as zf:
    zf.extractall(DEST)
    print("Files in zip:", zf.namelist())