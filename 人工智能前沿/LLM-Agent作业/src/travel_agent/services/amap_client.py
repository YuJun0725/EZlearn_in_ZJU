from __future__ import annotations

import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from pathlib import Path
from typing import Any


DEFAULT_ENV_PATH = Path(__file__).resolve().parents[3] / ".env"


class AmapClientError(RuntimeError):
    """Raised when a generic Amap Web Service request fails."""


def _load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def load_amap_api_key(env_path: str | Path = DEFAULT_ENV_PATH) -> str:
    _load_env_file(Path(env_path))
    api_key = os.environ.get("AMAP_API_KEY", "").strip()
    if not api_key or api_key == "replace_with_your_web_service_key":
        raise AmapClientError(
            "AMAP_API_KEY is missing. Fill it in .env before using Amap services."
        )
    return api_key


def _resolve_ca_bundle(explicit_path: Path | None) -> Path | None:
    if explicit_path is not None:
        resolved = explicit_path.expanduser().resolve()
        if not resolved.is_file():
            raise AmapClientError(f"CA bundle does not exist: {resolved}")
        return resolved

    candidates: list[Path] = []
    for environment_name in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE"):
        value = os.environ.get(environment_name, "").strip()
        if value:
            candidates.append(Path(value).expanduser())

    try:
        import certifi  # type: ignore[import-not-found]

        candidates.append(Path(certifi.where()))
    except ImportError:
        pass

    prefix = Path(sys.prefix)
    candidates.extend(
        [
            prefix / "etc" / "ssl" / "cert.pem",
            prefix / "etc" / "ssl" / "certs" / "ca-bundle.crt",
            prefix.parent / "usr" / "ssl" / "cert.pem",
        ]
    )
    program_files = os.environ.get("ProgramFiles", "").strip()
    if program_files:
        candidates.extend(
            [
                Path(program_files)
                / "Git"
                / "mingw64"
                / "etc"
                / "ssl"
                / "certs"
                / "ca-bundle.crt",
                Path(program_files)
                / "Git"
                / "mingw64"
                / "etc"
                / "ssl"
                / "cert.pem",
            ]
        )
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return None


def _create_ssl_context(ca_bundle: Path | None) -> ssl.SSLContext:
    resolved = _resolve_ca_bundle(ca_bundle)
    if resolved is not None:
        return ssl.create_default_context(cafile=str(resolved))
    return ssl.create_default_context()


class AmapWebServiceClient:
    """Small standard-library client for authenticated Amap JSON APIs."""

    def __init__(
        self,
        api_key: str,
        *,
        timeout: float = 15.0,
        max_retries: int = 2,
        ca_bundle: str | Path | None = None,
        user_agent: str = "HangzhouTravelAgent/1.0",
    ) -> None:
        self._api_key = api_key.strip()
        if not self._api_key:
            raise ValueError("Amap API key cannot be empty")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        self._timeout = timeout
        self._max_retries = max_retries
        self._user_agent = user_agent
        self._ssl_context = _create_ssl_context(
            Path(ca_bundle) if ca_bundle is not None else None
        )

    def request_json(
        self,
        endpoint: str,
        params: Mapping[str, str],
    ) -> Mapping[str, Any]:
        authenticated_params = dict(params)
        authenticated_params["key"] = self._api_key
        url = f"{endpoint}?{urllib.parse.urlencode(authenticated_params)}"
        request = urllib.request.Request(
            url,
            headers={"User-Agent": self._user_agent},
        )

        for attempt in range(self._max_retries + 1):
            try:
                with urllib.request.urlopen(
                    request,
                    timeout=self._timeout,
                    context=self._ssl_context,
                ) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                if not isinstance(payload, Mapping):
                    raise AmapClientError("Amap returned a non-object response")
                self.validate_response(payload)
                return payload
            except urllib.error.HTTPError as exc:
                raise AmapClientError(f"Amap HTTP error: status {exc.code}") from exc
            except json.JSONDecodeError as exc:
                raise AmapClientError("Amap returned invalid JSON") from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                reason = getattr(exc, "reason", None)
                if isinstance(reason, ssl.SSLCertVerificationError):
                    raise AmapClientError(
                        "TLS certificate verification failed. Pass a valid PEM "
                        "file with ca_bundle; do not disable SSL verification."
                    ) from exc
                if attempt >= self._max_retries:
                    detail = reason or "network request failed"
                    raise AmapClientError(f"Amap network error: {detail}") from exc
                time.sleep(attempt + 1)
        raise AmapClientError("Amap request failed without a response")

    @staticmethod
    def validate_response(payload: Mapping[str, Any]) -> None:
        if str(payload.get("status")) != "1":
            info = payload.get("info", "unknown API error")
            infocode = payload.get("infocode", "unknown")
            raise AmapClientError(f"Amap API error {infocode}: {info}")

