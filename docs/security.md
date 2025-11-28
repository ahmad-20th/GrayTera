# Security Best Practices

Guidelines for safe, legal, and effective use of GrayTera.

## Table of Contents

1. [Legal and Authorization](#legal-and-authorization)
2. [Data Security](#data-security)
3. [Safe Configuration](#safe-configuration)
4. [Operational Security](#operational-security)
5. [Tool Safety](#tool-safety)
6. [Incident Response](#incident-response)
7. [Compliance](#compliance)
8. [Documentation and Auditing](#documentation-and-auditing)

## Legal and Authorization

### Legal Framework

**Critical Rule**: Only test systems you own or have explicit written authorization to test.

**Never Test Without Permission:**
- Systems you don't own
- Systems you're not authorized to test
- Systems on networks you don't own

**Potential Legal Consequences:**
- Criminal charges under Computer Fraud and Abuse Act (CFAA) - up to 10 years imprisonment
- Civil liability - damages can reach millions
- Professional consequences - loss of credentials, employment

### Authorization Requirements

Before running GrayTera on any target:

1. **Obtain Written Authorization**
   - Email or contract explicitly authorizing security testing
   - Keep authorization documentation
   - Include scope: what domains/IPs are in scope
   - Include timeline: start/end dates
   - Include rules of engagement: times, intensity, data handling

2. **Verify Scope**
   - Test only explicitly authorized domains/IPs
   - Do not test associated systems not in scope
   - Use scope filtering in GrayTera to enforce boundaries

3. **Document Everything**
   ```
   Authorization Records:
   - Date authorization obtained
   - Who authorized testing
   - Scope of authorization
   - Approval documentation (email/contract)
   - Test dates and times
   - Summary of findings
   ```

### Authorization Checklist

- [ ] Written authorization obtained
- [ ] Authorization covers all targets being tested
- [ ] Timeline approved (test dates/times)
- [ ] Rules of engagement agreed upon
- [ ] Contact person identified for issues
- [ ] Data handling requirements documented
- [ ] Scope includes all subdomains/URLs
- [ ] Scope excludes systems not to be tested
- [ ] Authorization reviewed immediately before testing

## Data Security

### Sensitive Data Handling

**GrayTera may extract or discover:**
- Database usernames and password hashes
- API keys and tokens
- Customer data and PII
- Business secrets
- Configuration details

**Protection Requirements:**

1. **At Rest**
   ```bash
   # Encrypt data directory
   sudo encrypted_drive encrypt data/
   
   # Or use file permissions (minimum)
   chmod 700 data/
   chmod 600 data/scans/*/report.json
   ```

2. **In Transit**
   - Always use HTTPS/TLS for connections
   - Never send data over unencrypted channels
   - Verify certificates properly

3. **Retention Policy**
   ```
   - Keep findings only as long as needed
   - Delete sensitive data after reporting
   - Securely wipe deleted files
   ```

4. **Secure Deletion**
   ```bash
   # Securely delete sensitive files
   shred -vfz -n 3 data/scans/*/report.json
   
   # Or use encrypted container
   rm -rf data/scans/sensitive_target/
   ```

### Data Minimization

```yaml
# Disable features that extract sensitive data
exploitation:
  sqli:
    extract_tables: false      # Don't extract table contents
    extract_users: false       # Don't extract user data
    max_rows: 0                # Extract 0 rows (discovery only)

# Limit what's logged
logging:
  include_payloads: false      # Don't log actual payloads
  include_evidence: false      # Don't log evidence with data
```

### Access Control

```bash
# Restrict data access
chmod 700 data/                    # Owner only
chmod 600 data/scans/*/report.json # Owner read/write only

# Verify permissions
ls -la data/
ls -la data/scans/

# Check who can access
getfacl data/scans/
```

## Safe Configuration

### Safe Defaults

```yaml
# Conservative configuration for production targets
subdomain_enum:
  timeout: 10               # Short timeout
  strategies:
    dns: true
    ct: true
    dork: false            # Google dorking disabled

vulnerability_scan:
  threads: 2               # Low concurrency
  timeout: 30              # Short timeout
  nikto:
    enabled: false         # Intrusive scanner disabled
  zap:
    enabled: false         # Enterprise scanner disabled
  sqli:
    timeout: 15

exploitation:
  auto_exploit: false      # Require manual approval
  timeout: 30
  sqli:
    extract_tables: false  # Don't extract data
    extract_users: false
```

### Progressive Intensity

**Start Conservative, Increase Carefully:**

```yaml
# Phase 1: Discovery only (safe)
vulnerability_scan:
  threads: 2
  sqli:
    enabled: true
    timeout: 10
  nikto:
    enabled: false
  zap:
    enabled: false

exploitation:
  auto_exploit: false

# Phase 2: More thorough (after approval)
vulnerability_scan:
  threads: 5
  sqli:
    timeout: 30
  nikto:
    enabled: true

# Phase 3: Comprehensive (full engagement)
vulnerability_scan:
  threads: 10
  timeout: 60
  sqli:
    timeout: 60
  nikto:
    enabled: true
  zap:
    enabled: true
```

### WAF and IDS Evasion

**Respect Security Controls:**

Instead of evading, inform client:
```
[!] WAF Detected
    Some payloads may be blocked
    Recommendations:
    1. Whitelist scanner IP
    2. Reduce request rate
    3. Use approved scanner IPs
    4. Coordinate testing window
```

**Safe Configuration:**
```yaml
vulnerability_scan:
  sqli:
    detect_waf: true       # Detect WAF presence
    # Don't enable payload obfuscation
    # Work with client on WAF rules
  threads: 2               # Slow down to avoid IDS
```

## Operational Security

### Execution Environment

**Secure Testing Environment:**

```bash
# 1. Use dedicated system or VM
# 2. Disconnect from production network
# 3. Don't run as root (security principle)
python main.py example.com

# 4. Monitor system during testing
watch -n 1 'ps aux | grep main'

# 5. Isolate logs
chmod 600 data/logs/*
```

### Network Considerations

```bash
# Test from authorized networks only
# Example: from office/VPN, not home network

# Verify your IP is authorized
curl https://api.ipify.org
# Verify against authorization scope

# If using proxies, ensure authorized
# Never use residential proxies without explicit approval
```

### Timing

**Coordinate with Target:**

```yaml
# Schedule testing during approved windows
# Example: 9 AM - 5 PM EST weekdays only

# Configure timeouts to respect SLA
vulnerability_scan:
  threads: 2          # Low impact
  timeout: 30         # Quick completion
  sqli:
    timeout: 10       # Per-target timeout
```

**Load Considerations:**
- Test during low-traffic periods if possible
- Monitor target system during testing
- Be ready to stop if issues arise

### Incident Response Plan

Before testing:

1. **Establish Contact**
   ```
   Primary Contact: [name, phone, email]
   Backup Contact: [name, phone, email]
   Emergency Stop: [procedure]
   
   Example:
   Primary: John Smith, john@example.com, 555-0100
   Backup: Jane Doe, jane@example.com, 555-0101
   Emergency: Call ops center at 555-0102
   ```

2. **Define Stopping Criteria**
   - System unavailable (stop immediately)
   - Error rate > 5% (investigate)
   - Performance degradation > 25% (stop)
   - Alerts triggered (notify and stop)

3. **Stop Procedure**
   ```bash
   # Stop GrayTera immediately
   pkill -TERM main.py
   
   # Wait for graceful shutdown
   sleep 5
   
   # Force kill if needed
   pkill -9 main.py
   ```

## Tool Safety

### Input Validation

GrayTera validates all inputs:

```python
# Domain validation
is_valid_domain('example.com')      # OK
is_valid_domain('../etc/passwd')    # BLOCKED
is_valid_domain('invalid..domain')  # BLOCKED

# URL validation
is_valid_url('http://example.com')  # OK
is_valid_url('file:///etc/passwd')  # BLOCKED
is_valid_url('javascript:alert()') # BLOCKED
```

### Payload Safety

**SQL Injection Payloads:**
- Detection only (no data destruction)
- Read-only techniques
- No DROP, DELETE, TRUNCATE
- No privilege escalation attempts

**Configuration:**
```yaml
exploitation:
  sqli:
    # Safe by default
    # Only extracts data doesn't modify
    extract_tables: true  # Read-only
    extract_users: true   # Read-only
    
    # Disabled by default
    # Would modify data
    drop_tables: false     # Not implemented
    delete_rows: false     # Not implemented
```

### Timeout Protection

Prevents tool from:
- Running indefinitely
- Consuming resources indefinitely
- Hanging on slow targets

```yaml
subdomain_enum:
  timeout: 10          # Max 10 seconds

vulnerability_scan:
  timeout: 60          # Max 60 seconds per target
  sqli:
    timeout: 30        # Max 30 seconds per scan

exploitation:
  timeout: 60          # Max 60 seconds per attempt
  sqlmap:
    timeout: 600       # SQLMap subprocess timeout
```

## Incident Response

### What to Do If Something Goes Wrong

**System Unavailable During Testing:**

1. **Immediate Actions**
   ```bash
   # 1. Stop GrayTera immediately
   pkill -TERM main.py
   sleep 5
   pkill -9 main.py
   
   # 2. Document what happened
   tail -100 data/logs/graytera.log > incident_log.txt
   
   # 3. Contact target immediately
   # Call primary contact number
   ```

2. **Investigation**
   - Gather logs
   - Note exact time issue occurred
   - Note what was running when it happened
   - Prepare timeline of events

3. **Communication**
   - Inform target immediately
   - Provide initial status
   - Commit to investigation
   - Provide updates regularly

4. **Documentation**
   ```
   Incident Report:
   - Date/time of incident
   - Duration of unavailability
   - What was running
   - Symptoms observed
   - Root cause (if known)
   - Actions taken
   - Preventive measures
   ```

### False Positive Vulnerability

If you suspect finding is false positive:

1. **Don't Report Yet**
   - Manually verify
   - Use multiple techniques
   - Test with other tools

2. **Manual Verification**
   ```bash
   # Test vulnerability manually
   curl "http://target/page?id=1 AND 1=1"
   curl "http://target/page?id=1 AND 1=2"
   # Compare responses
   ```

3. **Secondary Confirmation**
   - Verify with SQLMap
   - Verify with OWASP ZAP
   - Check against CVSS criteria

4. **Report Accurately**
   - Note it was automatically detected
   - Document verification process
   - Be clear about confidence level

## Compliance

### Standards Alignment

**OWASP Testing Guide:**
- Follow OWASP guidelines for scope
- Use approved testing methodologies
- Document findings per OWASP framework

**PCI DSS (if applicable):**
```yaml
# Compliance settings for payment systems
vulnerability_scan:
  threads: 2          # Conservative
  timeout: 60         # Sufficient time
  
# Document all testing
# Maintain audit trail
# Report to assessor
```

**HIPAA (if applicable):**
```yaml
# Extra caution with healthcare data
exploitation:
  sqli:
    extract_tables: false  # Don't extract patient data
    extract_users: false   # Don't extract credentials
```

### Audit Trail

**Maintain Complete Records:**

```bash
# Log everything
├── data/logs/graytera.log          # Execution logs
├── data/scans/example.com/
│   ├── report.json                 # Findings
│   └── metadata.json               # Scan metadata
├── authorization.pdf               # Written approval
├── scope.json                       # Scope definition
├── incident_reports.md             # Any incidents
└── findings_report.pdf             # Final report
```

**Retention Period:**
- Keep for duration of engagement + 1 year
- Comply with client's data retention policy
- Securely destroy after retention period

## Documentation and Auditing

### Test Documentation

```markdown
# Penetration Test Report

## Executive Summary
- Target: example.com
- Test Date: 2025-11-27
- Authorization: See attached
- Overall Risk: [High/Medium/Low]

## Scope
In Scope:
- api.example.com
- admin.example.com

Out of Scope:
- staging.example.com (not included in authorization)

## Methodology
1. Subdomain enumeration
2. Vulnerability scanning (SQLi, Web server)
3. Exploitation (authorized only)

## Findings
[Detailed findings with verification evidence]

## Recommendations
[Specific remediation guidance]
```

### Logging Best Practices

```bash
# Enable detailed logging
python main.py example.com --debug

# Monitor logs in real-time
tail -f data/logs/graytera.log

# Archive logs for compliance
gzip data/logs/graytera.log
mv data/logs/graytera.log.gz data/logs/graytera-2025-11-27.log.gz
```

### Evidence Preservation

For each finding, preserve:
```json
{
  "vulnerability_id": "sqli_001",
  "type": "SQL Injection",
  "url": "http://example.com/page.php?id=1",
  "parameter": "id",
  "payload": "' OR '1'='1",
  "evidence": "Error-based SQL injection detected",
  "severity": "high",
  "timestamp": "2025-11-27T10:30:00Z",
  "verification_method": "Automated detection + manual confirmation",
  "exploitation_result": "Database name extracted: myapp_prod"
}
```

## Quick Reference Checklist

Before Testing:
- [ ] Written authorization obtained and reviewed
- [ ] Scope clearly defined and understood
- [ ] Contact information verified
- [ ] Rules of engagement agreed
- [ ] Data handling requirements documented
- [ ] Incident response plan established
- [ ] Safe configuration prepared
- [ ] Test schedule approved

During Testing:
- [ ] Monitor system performance
- [ ] Watch for errors or issues
- [ ] Be ready to stop if needed
- [ ] Keep incident contact handy
- [ ] Log all activities
- [ ] Document findings with evidence

After Testing:
- [ ] Compile findings report
- [ ] Verify all findings before reporting
- [ ] Securely delete sensitive data not needed
- [ ] Archive test records
- [ ] Provide recommendations
- [ ] Conduct exit meeting with client

## Additional Resources

- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [EC-Council Certified Ethical Hacker (CEH)](https://www.eccouncil.org/programs/certified-ethical-hacker-ceh/)
- [PTES - Penetration Testing Execution Standard](http://www.pentest-standard.org/)

---

**Last Updated**: November 27, 2025  
**Security Guidelines Version**: 1.0

**Disclaimer**: This guide provides security best practices. Users are responsible for ensuring their activities comply with all applicable laws and regulations. Unauthorized access to computer systems is illegal.
