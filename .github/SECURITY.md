# Security Policy

## Supported Versions

We currently support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| 0.1.x   | :white_check_mark: |
| < 0.1.0 | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability in web-similarity-audit, please send an email to:

**[Your Security Email Address]** (Update this before production release)

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### What to expect

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 7 days
- **Fix timeline**: Depends on severity
  - Critical: Within 7 days
  - High: Within 14 days
  - Medium: Within 30 days
  - Low: Next scheduled release

### Disclosure Policy

- We follow coordinated disclosure
- Security advisories will be published on GitHub Security Advisories
- Credit will be given to reporters (unless you prefer to remain anonymous)

## Security Considerations

### SSRF Protection

The tool includes SSRF (Server-Side Request Forgery) protection:
- Blocks requests to private IP ranges (RFC 1918, RFC 4193)
- Blocks localhost and link-local addresses
- DNS resolution happens before IP validation

However, users should:
- Run audits in isolated environments when crawling untrusted sites
- Use `--max-pages` to limit resource consumption
- Be cautious with redirect chains

### Rate Limiting

The tool respects per-host rate limits to avoid:
- Overwhelming target servers
- Being blocked as abusive traffic
- Violating Terms of Service

Default: 2 requests/second per host (configurable)

### Data Handling

The tool:
- Does NOT transmit data to external services
- Stores results locally only
- Does NOT log sensitive information (passwords, tokens)
- Uses deterministic hashing (SHA-256) for content comparison

Users should:
- Review output files before sharing
- Redact sensitive URLs if needed
- Be aware that URLs may contain query parameters with PII

### HTTP Security

- Uses HTTPS by default
- Validates SSL certificates (can be disabled with caution)
- Supports HTTP/2 and Brotli compression
- Sets timeouts to prevent hanging requests
- Limits response size to prevent memory exhaustion

### Input Validation

- URL validation prevents command injection
- CSV parsing uses safe methods
- Path traversal protection for output directories
- HTML parsing uses well-tested libraries (BeautifulSoup4, lxml)

## Known Security Limitations

1. **No JavaScript execution**: Static HTML only (unless `--render-js` is used)
2. **No authentication**: Cannot audit pages behind login
3. **Limited redirect handling**: May not follow all redirect types
4. **DNS rebinding**: Not fully protected against time-of-check-time-of-use

## Best Practices

When using this tool:

1. **Network Isolation**
   - Run in a VM or container when auditing untrusted sites
   - Use firewall rules to limit outbound connections

2. **Resource Limits**
   - Set `--max-pages` appropriately
   - Monitor disk space (output can be large)
   - Use `--concurrency` to limit parallel requests

3. **Data Handling**
   - Review output before committing to version control
   - Use `.gitignore` for `audit-results/`
   - Redact sensitive URLs in reports

4. **Dependencies**
   - Keep dependencies updated
   - Review `requirements.txt` for known vulnerabilities
   - Use `pip-audit` or similar tools

## Security Updates

We use GitHub's Dependabot to:
- Monitor dependency vulnerabilities
- Automatically create PRs for security updates
- Track security advisories

Subscribe to releases to get notified of security updates.

## Acknowledgments

We appreciate security researchers who responsibly disclose vulnerabilities.

Thank you for helping keep web-similarity-audit secure!
