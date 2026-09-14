import http.client
import ipaddress
import socket
import ssl
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit


MAX_REDIRECTS = 3
MAX_RESPONSE_BYTES = 1024 * 1024
TIMEOUT_SECONDS = 5
REDIRECT_STATUSES = {301, 302, 303, 307, 308}
INTERNAL_SUFFIXES = (".internal", ".local", ".localhost", ".lan", ".home")


class ScanValidationError(ValueError):
    pass


class ScanResolutionError(ValueError):
    pass


class ScanFetchError(RuntimeError):
    pass


@dataclass(frozen=True)
class FetchResponse:
    status: int
    headers: dict
    body: bytes


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, hostname, pinned_ip, port, timeout):
        super().__init__(hostname, port=port, timeout=timeout, context=ssl.create_default_context())
        self._pinned_ip = pinned_ip

    def connect(self):
        sock = socket.create_connection((self._pinned_ip, self.port), self.timeout, self.source_address)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


def resolve_public_addresses(hostname, port):
    try:
        literal = ipaddress.ip_address(hostname)
        addresses = [literal]
    except ValueError:
        try:
            infos = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
        except socket.gaierror as error:
            raise ScanResolutionError("Website hostname could not be resolved.") from error
        addresses = []
        for info in infos:
            try:
                address = ipaddress.ip_address(info[4][0])
            except ValueError:
                continue
            if address not in addresses:
                addresses.append(address)
    if not addresses:
        raise ScanResolutionError("Website hostname did not resolve to an address.")
    if any(not address.is_global for address in addresses):
        raise ScanValidationError("Website must resolve only to public internet addresses.")
    return [str(address) for address in addresses]


def validate_target(url):
    if not isinstance(url, str) or not url.strip() or len(url) > 2048:
        raise ScanValidationError("URL must be a non-empty string up to 2048 characters.")
    url = url.strip()
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as error:
        raise ScanValidationError("URL contains an invalid port or host.") from error
    if parsed.scheme not in {"http", "https"}:
        raise ScanValidationError("URL must use http or https.")
    if not parsed.hostname or parsed.fragment:
        raise ScanValidationError("URL must include a valid host and must not contain a fragment.")
    if parsed.username is not None or parsed.password is not None:
        raise ScanValidationError("URL credentials are not allowed.")
    hostname = parsed.hostname.rstrip(".").lower()
    if hostname == "localhost" or hostname.endswith(INTERNAL_SUFFIXES) or ("." not in hostname and ":" not in hostname):
        raise ScanValidationError("Internal-only website names are not allowed.")
    resolved_port = port or (443 if parsed.scheme == "https" else 80)
    addresses = resolve_public_addresses(hostname, resolved_port)
    return parsed, addresses


def _fetch_once(url, pinned_ip):
    parsed = urlsplit(url)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    target = parsed.path or "/"
    if parsed.query:
        target += "?" + parsed.query
    host_header = parsed.hostname
    if parsed.port and parsed.port not in {80, 443}:
        host_header = f"{host_header}:{parsed.port}"
    if parsed.scheme == "https":
        connection = _PinnedHTTPSConnection(parsed.hostname, pinned_ip, port, TIMEOUT_SECONDS)
    else:
        connection = http.client.HTTPConnection(pinned_ip, port=port, timeout=TIMEOUT_SECONDS)
    try:
        connection.request(
            "GET",
            target,
            headers={"Host": host_header, "User-Agent": "NitiShield-AI/1.0", "Accept": "text/html,*/*;q=0.8"},
        )
        response = connection.getresponse()
        headers = {key.lower(): value.strip() for key, value in response.getheaders()}
        body = b""
        if response.status not in REDIRECT_STATUSES:
            chunks = []
            total = 0
            while True:
                chunk = response.read(65536)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_RESPONSE_BYTES:
                    raise ScanFetchError("Website response exceeded the 1 MB safety limit.")
                chunks.append(chunk)
            body = b"".join(chunks)
        return FetchResponse(response.status, headers, body)
    except (OSError, ssl.SSLError, http.client.HTTPException) as error:
        raise ScanFetchError("Could not securely fetch the website.") from error
    finally:
        connection.close()


def fetch_with_redirects(url):
    current_url = url
    for redirect_count in range(MAX_REDIRECTS + 1):
        _, addresses = validate_target(current_url)
        try:
            response = _fetch_once(current_url, addresses[0])
        except ScanFetchError:
            raise
        except Exception as error:
            raise ScanFetchError("Could not securely fetch the website.") from error
        if response.status not in REDIRECT_STATUSES:
            if response.status >= 400:
                raise ScanFetchError(f"Website returned HTTP {response.status}.")
            return current_url, response
        location = response.headers.get("location")
        if not location:
            raise ScanFetchError("Website redirect did not include a destination.")
        if redirect_count == MAX_REDIRECTS:
            raise ScanFetchError("Website exceeded the redirect limit.")
        current_url = urljoin(current_url, location)
    raise ScanFetchError("Website exceeded the redirect limit.")


def assess_headers(final_url, headers):
    csp = headers.get("content-security-policy", "")
    checks = (
        (urlsplit(final_url).scheme == "https", "HTTPS is not enforced", "high", "The final website URL does not use HTTPS.", "Serve the website over HTTPS and redirect HTTP traffic to HTTPS."),
        (bool(csp), "Content Security Policy is missing", "high", "The response did not include a Content-Security-Policy header.", "Add a restrictive Content-Security-Policy suited to the site's required resources."),
        (bool(headers.get("strict-transport-security")), "HSTS is missing", "medium", "The response did not include Strict-Transport-Security.", "After HTTPS is working across the site, add an appropriate Strict-Transport-Security header."),
        (headers.get("x-content-type-options", "").lower() == "nosniff", "MIME sniffing protection is missing", "medium", "X-Content-Type-Options was absent or was not set to nosniff.", "Set X-Content-Type-Options: nosniff."),
        (bool(headers.get("x-frame-options")) or "frame-ancestors" in csp.lower(), "Frame embedding protection is missing", "high", "Neither X-Frame-Options nor a CSP frame-ancestors directive was found.", "Restrict frame embedding with CSP frame-ancestors or X-Frame-Options."),
        (bool(headers.get("referrer-policy")), "Referrer Policy is missing", "low", "The response did not include a Referrer-Policy header.", "Set a Referrer-Policy appropriate to the site's navigation needs."),
    )
    findings = [
        {"title": title, "severity": severity, "status": "open", "description": description, "recommendation": recommendation}
        for passed, title, severity, description, recommendation in checks
        if not passed
    ]
    passed_count = len(checks) - len(findings)
    return {
        "score": round(passed_count * 100 / len(checks)),
        "checks_passed": passed_count,
        "checks_total": len(checks),
        "findings": findings,
    }


def scan_website(url):
    final_url, response = fetch_with_redirects(url)
    return assess_headers(final_url, response.headers)
