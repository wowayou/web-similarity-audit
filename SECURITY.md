# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it privately:

1. **Do NOT open a public issue**
2. Email: security@eigentime.org (or open a private security advisory on GitHub)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

- **Initial response**: Within 48 hours
- **Status update**: Within 7 days
- **Fix timeline**: Depends on severity
  - Critical: 1-7 days
  - High: 7-14 days
  - Medium: 14-30 days
  - Low: Next minor release

## Security Features

### SSRF Protection

The tool implements SSRF (Server-Side Request Forgery) protection:

```python
# Blocks private IP ranges
- RFC 1918: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
- RFC 4193: fc00::/7
- Localhost: 127.0.0.0/8, ::1
- Link-local: 169.254.0.0/16, fe80::/10
- Multicast addresses
```

**How it works:**
1. DNS resolution happens before connection
2. Resolved IP is checked against blocked ranges
3. Connection is blocked if IP is private

**Bypass attempts blocked:**
- DNS rebinding (check happens after resolution)
- IPv6 tunneling
- Localhost aliases (127.0.0.1, localhost, etc.)

### Rate Limiting

Per-host rate limiting prevents accidental DoS:

```python
# Default: 2 requests per second per host
# Configurable: --per-host-rate N
```

Token bucket algorithm ensures smooth rate limiting without bursts.

### Input Validation

All URLs are validated before fetching:

```python
# Allowed schemes: http, https only
# Blocked: file://, ftp://, javascript:, data:
# No credentials in URLs: user:pass@host rejected
```

### No Authentication Handling

The tool intentionally does NOT handle:
- Cookies
- Session tokens
- API keys
- Basic auth credentials
- OAuth tokens

**Rationale:** Authentication should be handled by the user's browser or specialized tools. This tool audits public web pages only.

### Output Sanitization

- CSV output uses proper escaping
- Markdown output escapes pipe characters
- JSON output is properly encoded
- No eval() or exec() of user input

## Known Limitations

### Not Protected Against

1. **Malicious HTML content**
   - The tool parses HTML from arbitrary URLs
   - Use in trusted environments or with URL filtering
   - Consider sandboxing in Docker

2. **Zip bombs in compressed responses**
   - Large compressed responses could consume memory
   - Mitigated by response size limits (10MB default)

3. **Slow loris attacks**
   - Tool has request timeout (15s default)
   - But attacker-controlled server could slow responses

4. **Certificate validation bypass**
   - Tool enforces HTTPS certificate validation
   - Cannot be disabled (by design)

### Memory Safety

- Python's memory management is used
- No C extensions with potential buffer overflows
- Dependencies are vetted (httpx, beautifulsoup4, trafilatura)

## Dependency Security

### Automated Scanning

- Dependabot monitors dependencies
- CodeQL scans for common vulnerabilities
- GitHub Security Advisories are monitored

### Minimal Dependencies

By design, the tool has only 4 direct dependencies:
- httpx (HTTP client)
- beautifulsoup4 (HTML parsing)
- lxml (XML parsing)
- trafilatura (content extraction)

All are well-maintained, popular libraries with security track records.

## Best Practices for Users

### Run with Least Privilege

```bash
# Create dedicated user
sudo useradd -r -s /bin/false auditor
sudo -u auditor web-similarity-audit --crawl https://example.com
```

### Use Docker for Isolation

```bash
docker run --rm \
  --read-only \
  --cap-drop ALL \
  --network audit-net \
  -v $(pwd)/audit-results:/results \
  web-similarity-audit \
  --crawl https://example.com \
  --output /results
```

### Network Isolation

```bash
# Restrict outbound connections with firewall
iptables -A OUTPUT -m owner --uid-owner auditor -p tcp --dport 80 -j ACCEPT
iptables -A OUTPUT -m owner --uid-owner auditor -p tcp --dport 443 -j ACCEPT
iptables -A OUTPUT -m owner --uid-owner auditor -j REJECT
```

### Validate Input URLs

```bash
# Use URL allowlist
cat trusted-domains.txt | while read domain; do
  web-similarity-audit --crawl "https://$domain" --max-pages 200
done
```

### Monitor Resource Usage

```bash
# Set memory limit
ulimit -v 1048576  # 1GB virtual memory
web-similarity-audit --crawl https://example.com
```

### Regular Updates

```bash
# Check for updates regularly
pipx upgrade web-similarity-audit

# Or with pip
pip install --upgrade web-similarity-audit
```

## Threat Model

### In Scope

- SSRF attacks via malicious URLs
- DoS via rate limiting bypass
- Code injection via malicious HTML
- Information disclosure via error messages
- Path traversal in output files

### Out of Scope

- Physical security
- Social engineering
- Attacks on dependencies (report to them)
- Vulnerabilities in Python itself
- Operating system vulnerabilities

## Security Considerations by Use Case

### Public Website Auditing

**Risk: Low**
- Auditing public sites you control
- Standard usage, minimal risk

**Recommendations:**
- Use default settings
- Review output before sharing

### Third-Party Site Auditing

**Risk: Medium**
- Auditing sites you don't control
- Could encounter malicious content

**Recommendations:**
- Use Docker for isolation
- Set conservative rate limits
- Review output carefully

### Automated/CI Pipeline

**Risk: Medium**
- Runs unattended
- Could be targeted if CI is compromised

**Recommendations:**
- Use URL allowlist
- Set resource limits
- Monitor for anomalies
- Use secrets management (not environment variables)

### Untrusted URL Input

**Risk: High**
- Auditing user-provided URLs
- High risk of malicious input

**Recommendations:**
- Run in sandboxed environment (Docker/VM)
- Use strict URL validation
- Set aggressive rate and size limits
- Monitor system resources
- Log all activity

## Security Checklist

Before deploying in production:

- [ ] URLs are validated/allowlisted
- [ ] Tool runs with minimal privileges
- [ ] Network egress is restricted
- [ ] Resource limits are set
- [ ] Logs are monitored
- [ ] Dependencies are up to date
- [ ] Output is reviewed before sharing
- [ ] Backups exist if needed

## Incident Response

If you suspect a security incident:

1. **Isolate**: Stop the audit process
2. **Preserve**: Save logs and state files
3. **Report**: Email security@eigentime.org
4. **Document**: Record timeline and symptoms
5. **Update**: Apply patches when available

## Changelog

### 2025-01-15 - Initial Security Policy
- Documented SSRF protection
- Documented rate limiting
- Added security best practices
- Created threat model

## Credits

Security research and responsible disclosure appreciated. Contributors will be credited unless they prefer to remain anonymous.

## Questions?

For security questions, email: security@eigentime.org

For general questions, use: https://github.com/wowayou/web-similarity-audit/discussions
