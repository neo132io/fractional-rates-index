#!/usr/bin/env python3
"""Foreign-exchange rates for the Fractional Rates Index, locked per release.

One rate per currency is fetched once, written to `fx-lock-YYYYMMDD.json`, and
shipped with the release. Every normalised figure the index publishes can then
be recomputed from the lock file alone - no second call, no drift between the
number on the page and the number in the archive.

Source: frankfurter.app, which serves the European Central Bank's daily
reference rates. Free, no key, and citable. The call is the one the plan
specifies:

    GET https://api.frankfurter.app/latest?from=EUR

That returns EUR -> X for every currency the ECB publishes. USD per unit of X
is then rates[USD] / rates[X], with EUR itself at rates[USD].

There is no fallback rate and there never will be. If the API is unreachable
the module raises and the release stops. A made-up exchange rate is a made-up
price, and the whole point of this index is that every number traces to a
source.

    python tools/fx_rates.py --outdir D:/index-v2/staging/release \
        --currencies USD,GBP,EUR,AUD,SGD,CHF,NZD,SEK,CAD,INR
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

API_URL = "https://api.frankfurter.app/latest?from=EUR"
API_BASE = "EUR"
SOURCE = "European Central Bank reference rates via frankfurter.app"

# frankfurter sits behind Cloudflare and answers 403 to a bare urllib request.
USER_AGENT = "fractional-rates-index/2.1 (+https://saasfractionalcpo.com)"

TIMEOUT_SECONDS = 25


class FxUnavailable(RuntimeError):
    """The rates could not be fetched. Callers must stop, not guess."""


def fetch_ecb_rates(url: str = API_URL, timeout: int = TIMEOUT_SECONDS) -> dict:
    """Raw frankfurter payload: {'amount', 'base', 'date', 'rates': {...}}."""
    req = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.load(resp)
    except (urllib.error.URLError, urllib.error.HTTPError, OSError,
            ValueError, TimeoutError) as exc:
        raise FxUnavailable(
            f"frankfurter.app did not answer ({type(exc).__name__}: {exc}). "
            "Stopping. No fallback rate is invented; re-run when the API is up "
            "or pass --offline with an existing fx-lock file."
        ) from exc

    if not isinstance(payload, dict) or "rates" not in payload:
        raise FxUnavailable(f"unexpected payload shape from {url}: {payload!r}")
    if payload.get("base") != API_BASE:
        raise FxUnavailable(
            f"expected base {API_BASE}, got {payload.get('base')!r}"
        )
    return payload


def usd_per_unit(payload: dict, currencies: list[str]) -> dict[str, str]:
    """USD received for one unit of each requested currency.

    The payload is EUR-based, so USD/X = (USD/EUR) / (X/EUR). USD itself is
    1 by definition and EUR is the payload's USD rate.
    """
    rates = payload["rates"]
    if "USD" not in rates:
        raise FxUnavailable("payload carries no USD rate; cannot normalise")
    usd_per_eur = Decimal(str(rates["USD"]))

    out: dict[str, str] = {}
    missing: list[str] = []
    for cur in currencies:
        c = cur.upper()
        if c == "USD":
            out[c] = "1"
            continue
        if c == API_BASE:
            out[c] = str(usd_per_eur)
            continue
        if c not in rates:
            missing.append(c)
            continue
        out[c] = str(usd_per_eur / Decimal(str(rates[c])))
    if missing:
        raise FxUnavailable(
            "no ECB rate published for: " + ", ".join(missing) +
            ". Rows in those currencies cannot be normalised; either drop them "
            "from the release or add a sourced rate by hand."
        )
    return out


def build_lock(currencies: list[str], url: str = API_URL) -> dict:
    payload = fetch_ecb_rates(url)
    return {
        "fx_lock_version": 1,
        "source": SOURCE,
        "request_url": url,
        "api_base": payload.get("base"),
        "rate_date": payload.get("date"),
        "fetched_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "currencies": [c.upper() for c in currencies],
        "usd_per_unit": usd_per_unit(payload, currencies),
        "ecb_rates_base_eur": {k: str(v) for k, v in payload["rates"].items()},
    }


def lock_filename(lock: dict) -> str:
    stamp = (lock.get("rate_date") or "").replace("-", "")
    if not stamp:
        raise FxUnavailable("lock has no rate_date; refusing to name the file")
    return f"fx-lock-{stamp}.json"


def write_lock(lock: dict, outdir: Path) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / lock_filename(lock)
    path.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    return path


def load_lock(path: Path) -> dict:
    lock = json.loads(Path(path).read_text(encoding="utf-8"))
    for key in ("usd_per_unit", "rate_date", "source"):
        if key not in lock:
            raise FxUnavailable(f"{path} is not an fx lock file: missing {key}")
    return lock


def rate_of(lock: dict, currency: str) -> Decimal:
    """USD per one unit of `currency`, from a locked file. Never fetches."""
    table = lock["usd_per_unit"]
    c = (currency or "").upper()
    if c not in table:
        raise FxUnavailable(
            f"currency {c!r} is not in the fx lock dated {lock.get('rate_date')}. "
            "Re-run fx_rates.py with that currency in --currencies."
        )
    return Decimal(str(table[c]))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--currencies", default="USD,GBP,EUR",
                    help="comma separated ISO codes present in the data")
    args = ap.parse_args(argv)

    currencies = [c.strip().upper() for c in args.currencies.split(",") if c.strip()]
    try:
        lock = build_lock(currencies)
    except FxUnavailable as exc:
        sys.stderr.write(f"FX UNAVAILABLE - release stopped.\n{exc}\n")
        return 2
    path = write_lock(lock, args.outdir)
    json.dump({"lock_file": str(path), "rate_date": lock["rate_date"],
               "usd_per_unit": lock["usd_per_unit"]},
              sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
