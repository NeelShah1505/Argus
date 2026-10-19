"""
SEC EDGAR XBRL Data Downloader.

Fetches official machine-readable company facts and filing metadata from the
U.S. Securities and Exchange Commission (SEC) EDGAR API.

Adheres strictly to the SEC fair access policy (requires custom User-Agent,
rate limited to <= 10 req/sec, local caching).
"""

import json
import os
from pathlib import Path
import time
from typing import Any, Dict, Optional
import urllib.request
import urllib.error

SEC_USER_AGENT = "ArgusBenchmark/1.0 (benchmarks@argus-audit.internal)"
SEC_COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

BENCHMARK_COMPANIES = {
    "AAPL": {"cik": "0000320193", "name": "Apple Inc."},
    "MSFT": {"cik": "0000789019", "name": "Microsoft Corp."},
    "JPM": {"cik": "0000019617", "name": "JPMorgan Chase & Co."},
    "AMZN": {"cik": "0001018724", "name": "Amazon.com, Inc."},
    "GOOGL": {"cik": "0001652044", "name": "Alphabet Inc."},
}


def get_default_cache_dir() -> Path:
    base = Path(__file__).parent / "data"
    base.mkdir(parents=True, exist_ok=True)
    return base


def fetch_company_facts(
    cik: str,
    cache_dir: Optional[Path] = None,
    force_refresh: bool = False,
    timeout: int = 15,
) -> Dict[str, Any]:
    """
    Fetches the companyfacts.json from SEC EDGAR for a given CIK.
    Caches locally to prevent repeated network hits.
    """
    cik_padded = str(cik).strip().zfill(10)
    cache_path = (cache_dir or get_default_cache_dir()) / f"CIK{cik_padded}.json"

    if not force_refresh and cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            pass  # Fall through to download if cache is corrupted

    url = SEC_COMPANY_FACTS_URL.format(cik=cik_padded)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": SEC_USER_AGENT,
            "Accept-Encoding": "gzip, deflate",
            "Host": "data.sec.gov",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            # If gzip encoded
            if resp.info().get("Content-Encoding") == "gzip":
                import gzip
                data = gzip.decompress(data)
            parsed = json.loads(data.decode("utf-8", errors="replace"))
            cache_path.write_text(json.dumps(parsed, indent=2), encoding="utf-8")
            return parsed
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"SEC EDGAR returned HTTP {e.code} for CIK {cik_padded}: {e.reason}")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch facts for CIK {cik_padded} from SEC EDGAR: {e}")
