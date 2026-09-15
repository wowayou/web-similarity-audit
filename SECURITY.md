# Security Policy

## Supported version

Only the current 0.2.x release line is supported.

## Report vulnerabilities

Do not open a public issue for a suspected vulnerability. Use a private GitHub
security advisory or contact the maintainers with reproduction steps and impact.

## Network policy

Only HTTP(S) URLs without credentials are accepted. Before each request and
redirect, DNS answers are checked; any non-public answer (private, loopback,
link-local, multicast, unspecified, reserved, or shared space) is rejected.
Environment proxies are disabled. `--allow-private` disables this guard and is
only for trusted intranet or local targets.

Current protection is DNS preflight, not a network sandbox: the connector still
resolves for its connection. Deployments accepting hostile URLs need outbound
firewall rules as defense in depth.

## Resource controls

The default timeout is 10 seconds. Per-host rate limiting serializes request
starts and enforces a fixed minimum interval; it is not a token bucket.
Responses are streamed and limited to 2 MiB. Compressed-response handling is
documented in the README and release notes.
gzip and deflate are decoded incrementally with the same 2 MiB post-decompression
limit. Brotli and other encodings are rejected because they do not provide a
bounded decoder path.

When robots.txt is respected, 4xx responses allow crawling because the host has
not published usable rules. 5xx responses, network failures, HTTP 429, and
redirect responses deny crawling for that host. The 429 and redirect cases are
deliberately stricter than RFC 9309. Crawl-delay is enforced per host;
negative values are ignored and values above 3600 seconds are capped.

The six direct dependencies are beautifulsoup4, certifi, httpx, lxml,
trafilatura, and rich.