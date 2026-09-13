# Deployment Guide

This guide covers deploying web-similarity-audit in various environments.

## Installation Methods

### Method 1: pipx (Recommended for End Users)

```bash
pipx install web-similarity-audit
```

**Advantages:**
- Isolated environment (no dependency conflicts)
- Automatic PATH setup
- Easy upgrades: `pipx upgrade web-similarity-audit`
- Clean uninstall: `pipx uninstall web-similarity-audit`

### Method 2: pip with Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install web-similarity-audit
```

**Advantages:**
- Standard Python workflow
- Can pin specific versions in requirements.txt
- Easy to include in project dependencies

### Method 3: System-wide pip (Not Recommended)

```bash
pip install web-similarity-audit
```

**Warning:** May conflict with system packages. Use only if you understand the implications.

### Method 4: From Source (Development)

```bash
git clone https://github.com/wowayou/web-similarity-audit.git
cd web-similarity-audit
python -m venv venv
source venv/bin/activate
pip install -e .
```

## Platform-Specific Setup

### Linux

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv pipx
pipx ensurepath
pipx install web-similarity-audit
```

**RHEL/CentOS/Fedora:**
```bash
sudo dnf install python3 python3-pip
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install web-similarity-audit
```

**Arch Linux:**
```bash
sudo pacman -S python python-pipx
pipx install web-similarity-audit
```

### macOS

**With Homebrew:**
```bash
brew install python pipx
pipx ensurepath
pipx install web-similarity-audit
```

**With system Python:**
```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install web-similarity-audit
```

### Windows

**With Python from python.org:**
```powershell
# Install pipx
py -m pip install --user pipx
py -m pipx ensurepath

# Restart terminal, then:
pipx install web-similarity-audit
```

**With Windows Store Python:**
```powershell
python -m pip install --user pipx
python -m pipx ensurepath
pipx install web-similarity-audit
```

## Docker Deployment

### Using Pre-built Image (When Available)

```bash
docker pull ghcr.io/wowayou/web-similarity-audit:latest

docker run --rm \
  -v $(pwd)/audit-results:/results \
  ghcr.io/wowayou/web-similarity-audit:latest \
  --crawl https://example.com \
  --max-pages 200 \
  --output /results
```

### Building Custom Image

Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir web-similarity-audit

# Create output directory
RUN mkdir /results

# Run as non-root user
RUN useradd -m -u 1000 auditor
USER auditor

ENTRYPOINT ["web-similarity-audit"]
CMD ["--help"]
```

Build and run:
```bash
docker build -t web-similarity-audit .

docker run --rm \
  -v $(pwd)/urls.csv:/app/urls.csv \
  -v $(pwd)/audit-results:/results \
  web-similarity-audit \
  /app/urls.csv \
  --output /results
```

### Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  audit:
    image: ghcr.io/wowayou/web-similarity-audit:latest
    volumes:
      - ./urls.csv:/app/urls.csv:ro
      - ./audit-results:/results
    command: >
      /app/urls.csv
      --output /results
      --concurrency 4
```

Run:
```bash
docker-compose run --rm audit
```

## CI/CD Integration

### GitHub Actions

Create `.github/workflows/audit.yml`:
```yaml
name: Website Similarity Audit

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  workflow_dispatch:

jobs:
  audit:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'
    
    - name: Install tool
      run: pip install web-similarity-audit
    
    - name: Run audit
      run: |
        web-similarity-audit \
          --crawl ${{ vars.WEBSITE_URL }} \
          --max-pages 200 \
          --output audit-results
    
    - name: Upload results
      uses: actions/upload-artifact@v4
      with:
        name: similarity-audit
        path: audit-results/
    
    - name: Check for P1 issues
      run: |
        P1_COUNT=$(jq '.summary.p1_count' audit-results/pages.json)
        if [ "$P1_COUNT" -gt 0 ]; then
          echo "::error::Found $P1_COUNT high-priority duplicate issues"
          exit 1
        fi
```

### GitLab CI

Create `.gitlab-ci.yml`:
```yaml
similarity-audit:
  image: python:3.10-slim
  
  before_script:
    - pip install web-similarity-audit
  
  script:
    - web-similarity-audit --crawl $WEBSITE_URL --max-pages 200
  
  artifacts:
    paths:
      - audit-results/
    expire_in: 30 days
  
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
    - when: manual
```

### Jenkins

Create `Jenkinsfile`:
```groovy
pipeline {
    agent any
    
    environment {
        WEBSITE_URL = 'https://example.com'
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'pip install web-similarity-audit'
            }
        }
        
        stage('Audit') {
            steps {
                sh """
                    web-similarity-audit \
                        --crawl ${WEBSITE_URL} \
                        --max-pages 200 \
                        --output audit-results
                """
            }
        }
        
        stage('Report') {
            steps {
                archiveArtifacts artifacts: 'audit-results/**'
                
                script {
                    def p1Count = sh(
                        script: "jq '.summary.p1_count' audit-results/pages.json",
                        returnStdout: true
                    ).trim()
                    
                    if (p1Count.toInteger() > 0) {
                        unstable("Found ${p1Count} high-priority duplicates")
                    }
                }
            }
        }
    }
}
```

## Scheduled Audits

### Linux Cron

```bash
# Edit crontab
crontab -e

# Add weekly audit (Sunday at 2 AM)
0 2 * * 0 /home/user/.local/bin/web-similarity-audit --crawl https://example.com --max-pages 200 --output /home/user/audits/$(date +\%Y-\%m-\%d)
```

### Windows Task Scheduler

```powershell
# Create scheduled task
$action = New-ScheduledTaskAction -Execute 'web-similarity-audit' -Argument '--crawl https://example.com --max-pages 200'
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 2am
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "WebSimilarityAudit" -Description "Weekly website similarity audit"
```

### macOS launchd

Create `~/Library/LaunchAgents/com.user.web-similarity-audit.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.web-similarity-audit</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/username/.local/bin/web-similarity-audit</string>
        <string>--crawl</string>
        <string>https://example.com</string>
        <string>--max-pages</string>
        <string>200</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>0</integer>
        <key>Hour</key>
        <integer>2</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/username/audit.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/username/audit.error.log</string>
</dict>
</plist>
```

Load:
```bash
launchctl load ~/Library/LaunchAgents/com.user.web-similarity-audit.plist
```

## Production Considerations

### Resource Limits

**Memory:**
- Baseline: ~100MB
- Per 100 pages: ~250MB
- 200 pages: ~500MB
- Consider setting Docker memory limit: `--memory="1g"`

**CPU:**
- Mostly I/O bound (network requests)
- CPU usage spikes during similarity computation
- Concurrency=4 is usually sufficient

**Disk:**
- Minimal during execution
- Output size: ~1MB per 100 pages
- Consider log rotation for scheduled audits

### Network Configuration

**Firewall Rules:**
- Allow outbound HTTPS (443)
- Allow outbound HTTP (80) if auditing HTTP sites
- Block private IP ranges (already done by tool)

**Proxy Support:**
```bash
# Set environment variables
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
export NO_PROXY=localhost,127.0.0.1

web-similarity-audit --crawl https://example.com
```

**Rate Limiting:**
```bash
# Reduce rate for production sites
web-similarity-audit \
  --crawl https://example.com \
  --per-host-rate 1  # 1 request per second
```

### Monitoring

**Success Metrics:**
- Exit code 0
- audit-results directory created
- pages.json contains expected page count

**Failure Detection:**
```bash
#!/bin/bash
web-similarity-audit --crawl https://example.com
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    # Send alert
    curl -X POST https://alerts.example.com/webhook \
         -d "status=failure&exit_code=$EXIT_CODE"
fi
```

**Integration with Monitoring Tools:**
- Prometheus: Export metrics from pages.json
- Datadog: Parse logs and push custom metrics
- Sentry: Capture errors (if implemented in future versions)

### Logging

**Structured Logging:**
```bash
web-similarity-audit \
  --crawl https://example.com \
  --output audit-results \
  2>&1 | tee -a audit.log
```

**Log Rotation:**
```bash
# logrotate config
/var/log/web-similarity-audit/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 auditor auditor
}
```

## Troubleshooting

### Installation Issues

**Issue:** `command not found: web-similarity-audit`
```bash
# Ensure pipx PATH is set
pipx ensurepath
# Restart terminal
```

**Issue:** Permission denied
```bash
# Use --user flag or virtual environment
pip install --user web-similarity-audit
```

**Issue:** Python version too old
```bash
# Check version
python --version
# Install Python 3.10+ from python.org or your package manager
```

### Runtime Issues

**Issue:** Connection timeout
```bash
# Increase timeout
web-similarity-audit --crawl https://example.com --timeout 30
```

**Issue:** Memory error on large sites
```bash
# Reduce max pages
web-similarity-audit --crawl https://example.com --max-pages 100
```

**Issue:** Rate limited by target site
```bash
# Reduce request rate
web-similarity-audit --crawl https://example.com --per-host-rate 0.5
```

## Upgrade Guide

### Upgrading with pipx

```bash
pipx upgrade web-similarity-audit
```

### Upgrading with pip

```bash
pip install --upgrade web-similarity-audit
```

### Checking for Updates

```bash
pip list --outdated | grep web-similarity-audit
```

### Breaking Changes

Check CHANGELOG.md before upgrading:
```bash
# View changelog for specific version
curl -s https://raw.githubusercontent.com/wowayou/web-similarity-audit/main/CHANGELOG.md
```

## Uninstallation

### With pipx

```bash
pipx uninstall web-similarity-audit
```

### With pip

```bash
pip uninstall web-similarity-audit
```

### Clean up data

```bash
# Remove state files
rm -rf .audit-state.json

# Remove output directories
rm -rf audit-results/
```

## Security Hardening

### Run as Non-Root

```bash
# Create dedicated user
sudo useradd -r -s /bin/false auditor

# Run as that user
sudo -u auditor web-similarity-audit --crawl https://example.com
```

### Restrict Network Access

```bash
# Use Docker with network restrictions
docker run --rm \
  --network audit-net \
  --cap-drop ALL \
  web-similarity-audit \
  --crawl https://example.com
```

### Read-Only Filesystem (Except Output)

```bash
docker run --rm \
  --read-only \
  --tmpfs /tmp \
  -v $(pwd)/audit-results:/results \
  web-similarity-audit \
  --crawl https://example.com \
  --output /results
```

## Support

- GitHub Issues: https://github.com/wowayou/web-similarity-audit/issues
- Discussions: https://github.com/wowayou/web-similarity-audit/discussions
- Security: See SECURITY.md
