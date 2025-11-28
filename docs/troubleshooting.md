# Troubleshooting Guide

Common issues and solutions for GrayTera users.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Runtime Issues](#runtime-issues)
3. [Enumeration Problems](#enumeration-problems)
4. [Scanning Issues](#scanning-issues)
5. [Exploitation Problems](#exploitation-problems)
6. [Performance Issues](#performance-issues)
7. [Data & Persistence](#data--persistence)
8. [Getting Help](#getting-help)

## Installation Issues

### Problem: Module Import Errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'dnspython'
ImportError: cannot import name 'Vulnerability' from 'core.target'
```

**Solutions:**

1. Verify virtual environment is activated:
```bash
# Check if venv is active (should show prefix)
echo $VIRTUAL_ENV

# If not active, activate it
source venv/bin/activate
```

2. Reinstall dependencies:
```bash
pip install --upgrade -r requirements.txt
```

3. Check Python version (3.8+ required):
```bash
python --version
```

4. If specific module fails, install directly:
```bash
pip install dnspython requests pyyaml
```

### Problem: SQLMap Not Found

**Symptoms:**
```
[!] Error: SQLMap not found at /usr/bin/sqlmap
[!] Make sure SQLMap is installed
```

**Solutions:**

1. Install SQLMap:
```bash
# Ubuntu/Debian
sudo apt-get install sqlmap

# Or from source
git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git sqlmap-dev
```

2. Set explicit path in `config.yaml`:
```yaml
exploitation:
  sqlmap:
    path: /usr/local/bin/sqlmap/sqlmap.py
```

3. Or use environment variable:
```bash
export SQLMAP_PATH="/path/to/sqlmap/sqlmap.py"
python main.py example.com
```

4. Verify installation:
```bash
sqlmap --version
# Should show version information
```

### Problem: Nikto Installation Issues

**Symptoms:**
```
[!] Error: Nikto not found
[!] XML parsing error
```

**Solutions:**

1. Install Nikto:
```bash
# Ubuntu/Debian
sudo apt-get install nikto

# From source
git clone https://github.com/sullo/nikto
cd nikto/program
sudo perl ./nikto.pl -h 127.0.0.1
```

2. Verify installation:
```bash
nikto -h
# Should show Nikto help
```

3. Check Perl dependency:
```bash
perl -v
# Perl 5.6+ required
```

4. If issues persist, disable Nikto (it's optional):
```yaml
vulnerability_scan:
  nikto:
    enabled: false
```

### Problem: Missing Wordlist File

**Symptoms:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'wordlists/subdomains.txt'
```

**Solutions:**

1. Check file exists:
```bash
ls -la wordlists/subdomains.txt
```

2. Create basic wordlist:
```bash
mkdir -p wordlists
cat > wordlists/subdomains.txt << EOF
www
mail
ftp
admin
api
dev
blog
EOF
```

3. Use custom wordlist in config:
```yaml
subdomain_enum:
  dns:
    wordlist: /path/to/custom_wordlist.txt
```

## Runtime Issues

### Problem: Script Hangs/Freezes

**Symptoms:**
- Script appears to hang indefinitely
- CPU usage drops to zero
- No error messages

**Causes & Solutions:**

1. **Timeout too long** - Scanner waiting for slow target
   ```yaml
   vulnerability_scan:
     timeout: 30  # Reduce from 60
     sqli:
       timeout: 15  # Reduce from 30
   ```

2. **Network connectivity issue** - Target unreachable
   ```bash
   # Test connectivity
   ping example.com
   curl -I http://example.com
   ```

3. **Thread deadlock** - Enable debug mode
   ```bash
   python main.py example.com --debug
   # Check logs/graytera.log for where it's stuck
   ```

4. **Nikto hanging** - Disable it
   ```yaml
   vulnerability_scan:
     nikto:
       enabled: false
   ```

5. **Kill stuck process**:
   ```bash
   # Find process
   ps aux | grep main.py
   
   # Kill gracefully
   kill -15 <pid>
   
   # Force kill if needed
   kill -9 <pid>
   ```

### Problem: Out of Memory

**Symptoms:**
```
MemoryError
Process killed (likely due to OOM)
```

**Solutions:**

1. Reduce concurrent threads:
```yaml
vulnerability_scan:
  threads: 2  # Reduce from 10
```

2. Limit subdomain discovery:
```yaml
subdomain_enum:
  max_subdomains: 100  # Cap at 100
```

3. Disable unnecessary scanners:
```yaml
vulnerability_scan:
  nikto:
    enabled: false
  zap:
    enabled: false
```

4. Monitor memory usage:
```bash
# In another terminal
watch -n 1 'ps aux | grep main.py'
```

### Problem: No Write Permissions

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: 'data/scans/'
```

**Solutions:**

1. Fix directory permissions:
```bash
chmod 755 data/
chmod 755 data/scans/
chmod 755 data/logs/
```

2. Or use different output directory:
```bash
python main.py example.com --output /tmp/graytera_output
```

3. Check directory ownership:
```bash
ls -la data/
# If needed, change ownership
sudo chown -R $USER:$USER data/
```

## Enumeration Problems

### Problem: No Subdomains Found

**Symptoms:**
```
[*] Enumeration complete
[*] Found 0 subdomains
```

**Causes & Solutions:**

1. **Domain doesn't exist** - Verify domain is valid
   ```bash
   dig example.com
   nslookup example.com
   ```

2. **DNS timeout too short** - Increase timeout
   ```yaml
   subdomain_enum:
     timeout: 30  # Increase from 10
     dns:
       threads: 5  # Reduce threads
   ```

3. **All strategies disabled** - Enable at least one
   ```yaml
   subdomain_enum:
     strategies:
       dns: true  # Enable DNS strategy
   ```

4. **Wordlist is empty** - Check wordlist file
   ```bash
   wc -l wordlists/subdomains.txt
   # Should show > 0 lines
   ```

5. **Network filtering** - Target may block queries
   - Test manually: `dig www.example.com`
   - Try fewer threads in config
   - Use different DNS servers

### Problem: Duplicate Subdomains

**Symptoms:**
- Same subdomain listed multiple times
- Result counts don't match actual unique subdomains

**Solution:** This is normal behavior - duplicates are automatically deduplicated in the Target object's set. Check final JSON output.

### Problem: DNS Resolution Slow

**Symptoms:**
- Enumeration stage taking > 5 minutes
- Timeout errors for legitimate subdomains

**Solutions:**

1. Increase timeout:
```yaml
subdomain_enum:
  timeout: 30
```

2. Increase concurrent threads:
```yaml
subdomain_enum:
  dns:
    threads: 20  # More parallel queries
```

3. Reduce wordlist size temporarily:
```bash
head -100 wordlists/subdomains.txt > wordlists/subdomains_small.txt
```

4. Try different DNS server:
```python
# In enums/dns_enum.py
# Change DNS resolver to faster option
```

## Scanning Issues

### Problem: Scanner Skipped

**Symptoms:**
```
[!] SQLiScanner skipped - not found
[!] NiktoScanner not enabled
```

**Solutions:**

1. Verify scanner is enabled in config:
```yaml
vulnerability_scan:
  sqli:
    enabled: true  # Make sure true
```

2. Check scanner dependencies are installed:
```bash
# For SQLMap
python -m sqlmap --version

# For Nikto
nikto -h
```

3. Verify scanner registry:
```python
# In scanners/scanner_registry.py
# Check scanner is registered
print(registry.list_all())
```

### Problem: No Vulnerabilities Found

**Symptoms:**
```
[*] Scanning complete
[*] Found 0 vulnerabilities
```

**Causes & Solutions:**

1. **Target not vulnerable** - This is normal, especially for production sites
   - Try test targets (DVWA, WebGoat)
   - Verify target has testable parameters

2. **Scanner timeout too short**:
   ```yaml
   vulnerability_scan:
     sqli:
       timeout: 60  # Increase from 30
   ```

3. **WAF blocking payloads** - Try encoded payloads:
   ```yaml
   vulnerability_scan:
     sqli:
       detect_waf: true
   ```

4. **No testable parameters** - Check target manually:
   ```bash
   curl "http://example.com/page.php?id=1" -v
   ```

### Problem: XML Parsing Errors

**Symptoms:**
```
xml.etree.ElementTree.ParseError: no element found
```

**Causes:**
- Usually from Nikto scanner outputting malformed XML

**Solutions:**

1. Disable Nikto:
```yaml
vulnerability_scan:
  nikto:
    enabled: false
```

2. Update Nikto:
```bash
sudo apt-get update
sudo apt-get install --only-upgrade nikto
```

3. Check Nikto manually:
```bash
nikto -h example.com -Format xml > output.xml
# Check if XML is valid
```

### Problem: Rate Limited / Blocked

**Symptoms:**
```
[!] 429 Too Many Requests
[!] Connection timeout
```

**Solutions:**

1. Reduce concurrent threads:
```yaml
vulnerability_scan:
  threads: 2  # Reduce from 10
```

2. Increase delays between requests:
```yaml
vulnerability_scan:
  sqli:
    timeout: 60  # Longer timeout = longer delays
```

3. Use proxy to rotate IPs (if authorized):
```bash
export HTTP_PROXY="http://proxy.example.com:8080"
python main.py example.com
```

4. Reduce scanning intensity:
```yaml
vulnerability_scan:
  sqli:
    payloads_file: payloads/sqli_strategies.yaml  # Custom lighter payloads
```

## Exploitation Problems

### Problem: Exploitation Fails

**Symptoms:**
```
[!] Exploitation failed
[!] Payload validation failed
```

**Solutions:**

1. Verify vulnerability is real:
   ```bash
   # Test payload manually
   curl "http://target/page.php?id=1%27"
   ```

2. Enable debug logging:
   ```bash
   python main.py example.com --debug
   ```

3. Check SQLMap configuration:
   ```yaml
   exploitation:
     sqlmap:
       level: 2  # Start with lower level
       risk: 1   # Use safe settings
   ```

4. Manually test with SQLMap:
   ```bash
   sqlmap -u "http://target/page.php?id=1" --batch
   ```

### Problem: SQLMap Integration Issues

**Symptoms:**
```
[!] SQLMap failed
[!] Batch mode not working
```

**Solutions:**

1. Test SQLMap independently:
   ```bash
   sqlmap --version
   sqlmap -u "http://target/page.php?id=1" --batch
   ```

2. Check configuration:
   ```yaml
   exploitation:
     sqlmap:
       path: null  # Auto-detect (recommended)
       batch: true
       threads: 5  # Not all SQLMap versions use this
   ```

3. Verify permissions:
   ```bash
   which sqlmap
   ls -la /usr/bin/sqlmap
   # Should be executable
   ```

### Problem: No Data Extracted

**Symptoms:**
- Exploitation successful but no data in results
- Evidence present but extracted data empty

**Solutions:**

1. Enable data extraction:
   ```yaml
   exploitation:
     sqli:
       extract_tables: true
   ```

2. Increase exploitation timeout:
   ```yaml
   exploitation:
     timeout: 120  # Increase from 60
   ```

3. Check database access:
   - Target database may have limited permissions
   - Some databases restrict information_schema access
   - Manually verify data is extractable with SQLMap

4. Review evidence:
   - Even without data extraction, evidence confirms vulnerability

## Performance Issues

### Problem: Very Slow Scanning

**Symptoms:**
- Single target taking > 5 minutes
- CPU or network at capacity

**Solutions:**

1. Reduce scanner timeout:
```yaml
vulnerability_scan:
  sqli:
    timeout: 10  # Reduce from 30
```

2. Reduce threads:
```yaml
vulnerability_scan:
  threads: 2  # Reduce from 10
```

3. Disable slow scanners:
```yaml
vulnerability_scan:
  nikto:
    enabled: false
  zap:
    enabled: false
```

4. Reduce subdomain count:
```yaml
subdomain_enum:
  max_subdomains: 50  # Limit subdomains to scan
```

5. Check system resources:
```bash
# Monitor while running
htop
# Or in another terminal
watch -n 1 free -h
```

### Problem: High Memory Usage

**Symptoms:**
- Gradual memory increase
- Reaches 500MB+
- System becomes sluggish

**Solutions:**

1. Clear old data:
```bash
python main.py --clear  # Or manually delete data/scans/
```

2. Reduce thread count:
```yaml
vulnerability_scan:
  threads: 2
```

3. Limit subdomains:
```yaml
subdomain_enum:
  max_subdomains: 50
```

4. Split large scans:
```bash
# Scan specific subdomains
python main.py api.example.com
python main.py admin.example.com
# Then merge results manually
```

## Data & Persistence

### Problem: Cannot Resume Scan

**Symptoms:**
```
[!] No previous scan found for domain
```

**Solutions:**

1. Check data directory exists:
```bash
ls -la data/scans/example.com/
```

2. Check pickle file exists:
```bash
ls -la data/scans/example.com/state.pkl
```

3. Fix permissions:
```bash
chmod 755 data/scans/example.com/
chmod 644 data/scans/example.com/*.pkl
```

4. Recreate scan if corrupted:
```bash
# Delete corrupted state
rm -rf data/scans/example.com/state.pkl
# Re-run from start
python main.py example.com
```

### Problem: Corrupted Data Files

**Symptoms:**
```
json.decoder.JSONDecodeError
pickle.UnpicklingError
```

**Solutions:**

1. Check file integrity:
```bash
python -c "import json; json.load(open('data/scans/example.com/report.json'))"
```

2. Restore from backup (if exists):
```bash
cp data/scans/example.com/report.json.bak data/scans/example.com/report.json
```

3. Delete corrupted scan:
```bash
rm -rf data/scans/example.com/
python main.py example.com  # Fresh scan
```

### Problem: Results Not Saved

**Symptoms:**
- Scan completes but data/scans/ is empty
- JSON file not created

**Solutions:**

1. Check output permissions:
```bash
touch data/scans/test.txt
ls -la data/scans/test.txt
rm data/scans/test.txt
```

2. Check free disk space:
```bash
df -h
# If full, free up space
```

3. Verify DataStore initialization:
```bash
python -c "from core.data_store import DataStore; d = DataStore(); print(d.base_path)"
```

4. Check logs for errors:
```bash
tail -50 data/logs/graytera.log
```

## Configuration Issues

### Problem: Invalid Configuration

**Symptoms:**
```
yaml.scanner.ScannerError
yaml.YAMLError
```

**Solutions:**

1. Validate YAML syntax:
```bash
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

2. Check indentation (YAML is strict):
```yaml
# Correct
vulnerability_scan:
  threads: 10
  sqli:
    enabled: true

# WRONG - indentation
vulnerability_scan:
 threads: 10  # Only 1 space - wrong!
```

3. Use default config:
```bash
# Backup current
mv config.yaml config.yaml.bak
# Copy from repo
git checkout config.yaml
python main.py example.com
```

### Problem: Settings Not Taking Effect

**Symptoms:**
- Config changes ignored
- Default values used instead

**Solutions:**

1. Verify config file location:
```bash
python main.py example.com --config config.yaml -v
# Check logs show config loaded
```

2. Check for typos:
```yaml
# Config section names are case-sensitive
subdomain_enum:  # Correct
Subdomain_Enum:  # Wrong!
```

3. Verify config format:
```python
import yaml
with open('config.yaml') as f:
    config = yaml.safe_load(f)
    print(config)  # Check structure
```

## Getting Help

### Before Asking for Help

1. **Check logs**:
   ```bash
   tail -100 data/logs/graytera.log
   ```

2. **Enable debug mode**:
   ```bash
   python main.py example.com --debug
   ```

3. **Search documentation**:
   - [Configuration Reference](configuration.md)
   - [Architecture Overview](architecture.md)
   - [Scanner Reference](scanners.md)

4. **Try minimal example**:
   ```bash
   python main.py google.com --stage enum
   ```

### Getting Support

1. **Check GitHub Issues**:
   - Search for similar problems
   - Check closed issues for solutions

2. **Documentation**:
   - [docs/](.)
   - [README.md](../README.md)

3. **Manual Testing**:
   - Test with public test targets (DVWA, WebGoat)
   - Test components individually
   - Verify prerequisites are installed

### Useful Diagnostic Commands

```bash
# System information
uname -a
python --version
pip list | grep -E "requests|pyyaml|dnspython"

# Network connectivity
ping example.com
dig example.com
curl -I http://example.com

# File system
du -sh data/
ls -la wordlists/
file data/scans/example.com/state.pkl

# Running processes
ps aux | grep main.py
top -b -n 1 | head -20
```

---

**Last Updated**: November 27, 2025  
**Troubleshooting Guide Version**: 1.0
