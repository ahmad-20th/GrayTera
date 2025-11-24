# GrayTera - Quick Start Guide

## TEAM DEVELOPMENT WORKFLOW (7-Day Sprint)
==========================================

### Day 1 (Today) - Foundation
**All Teams Together:**
- [x] Setup project structure & Git repo
- [ ] Create virtual environments
- [ ] Define interfaces & data models
- [ ] Assign team responsibilities

**Team Assignments:**
- **Team 1 (2 devs):** Pipeline + CLI + DataStore
- **Team 2 (2 devs):** Subdomain Enumeration
- **Team 3 (2 devs):** SQLi Scanner
- **Team 4 (2 devs):** SQLi Exploit + Error Handling

---

### Days 2-3 - Core Development
**Team 1 (Pipeline & Core):**
- [ ] Implement Pipeline.run(), pause(), resume()
- [ ] Implement DataStore save/load (JSON + pickle)
- [ ] CLI argument parsing (target, --resume, --stage)
- [ ] Test stage transitions
- [ ] **Deliverable:** Working empty pipeline by EOD Day 3

**Team 2 (Subdomain Enum):**
- [ ] Implement dictionary-based enumeration (priority)
- [ ] DNS resolution checking
- [ ] Add crt.sh API integration (if time)
- [ ] **Deliverable:** Find at least 10 subdomains by EOD Day 3

**Team 3 (SQLi Scanner):**
- [ ] Implement payload injection mechanism
- [ ] Add error-based detection (MySQL, PostgreSQL errors)
- [ ] Test against safe targets
- [ ] **Deliverable:** Detect at least 1 SQLi by EOD Day 3

**Team 4 (SQLi Exploit):**
- [ ] Design exploit interface
- [ ] Implement basic version extraction
- [ ] HTTP client with retry logic
- [ ] **Deliverable:** Extract DB version by EOD Day 3

---

### Days 4-5 - Integration & Enhancement
**Team 1:**
- [ ] Integrate all modules into pipeline
- [ ] Implement observers (console + file logging)
- [ ] Add colored output
- [ ] Handle stage failures gracefully

**Team 2:**
- [ ] Optimize subdomain discovery
- [ ] Add deduplication
- [ ] Handle DNS timeouts
- [ ] Test with multiple domains

**Team 3:**
- [ ] Add boolean-based blind SQLi detection
- [ ] Reduce false positives
- [ ] Add payload variations
- [ ] Test against multiple targets

**Team 4:**
- [ ] Implement UNION-based extraction
- [ ] Add interactive exploit selection
- [ ] Handle common edge cases (WAF, rate limiting)
- [ ] Document exploitation results

**All Teams:**
- [ ] Daily integration testing (30min EOD)
- [ ] Fix blocking bugs immediately
- [ ] Update documentation as you go

---

### Day 6 (Thursday) - Testing & Polish
**Morning (All Teams):**
- [ ] Full integration testing
- [ ] Test complete workflow: enum → scan → exploit
- [ ] Test against all safe targets
- [ ] Verify save/resume works
- [ ] Check error handling

**Afternoon (Split Tasks):**
- [ ] Fix critical bugs
- [ ] Improve console output
- [ ] Add progress indicators
- [ ] Clean up code comments
- [ ] Update README with usage examples

**Evening:**
- [ ] Final test run
- [ ] Prepare demo script
- [ ] Document known limitations

---

### Day 7 (Friday) - Demo Day
**Morning (Before Demo):**
- [ ] Quick smoke test
- [ ] Prepare demo targets
- [ ] Practice demo run (15min)
- [ ] Prepare backup plan if live demo fails

**Demo Checklist:**
- [ ] Show subdomain enumeration (live)
- [ ] Show SQLi detection (live)
- [ ] Show exploitation (pre-recorded if needed)
- [ ] Show saved results
- [ ] Explain architecture

---

## CRITICAL PATH (MUST COMPLETE)
================================

### Absolutely Essential (Cut nothing here):
1. ✅ **Pipeline orchestrator** - runs stages in sequence
2. ✅ **Dictionary-based subdomain enum** - finds subdomains
3. ✅ **Error-based SQLi scanner** - detects vulnerabilities
4. ✅ **Basic SQLi exploit** - extracts DB version
5. ✅ **Data persistence** - saves/loads scan results
6. ✅ **Console output** - shows progress
7. ✅ **Error handling** - doesn't crash on failures

### High Priority (Cut if behind schedule):
8.  ⚠️ Colored console output
9.  ⚠️ Retry logic for network errors
10. ⚠️ Multiple subdomain techniques (crt.sh)
11. ⚠️ Boolean-based SQLi detection
12. ⚠️ File logging

### Nice to Have (Cut these first):
13. ❌ Progress bars
14. ❌ Time-based blind SQLi
15. ❌ Interactive exploit menu
16. ❌ HTML reports
17. ❌ XSS/CSRF scanners
18. ❌ Pause/resume (manual ctrl+c is fine)

---

## DAILY STANDUP (15 min @ 9 AM)
=================================

Each person answers:
1. **What I completed yesterday**
2. **What I'm doing today**
3. **Any blockers** (need help with)

**Example:**
> "I completed the Pipeline.run() method. Today I'm implementing save/load. 
> I'm blocked on understanding how Target objects should be serialized."

---

## MERGE STRATEGY (AVOID CONFLICTS)
===================================

### File Ownership (Who edits what):
- **Team 1:** `core/pipeline.py`, `core/data_store.py`, `main.py`
- **Team 2:** `stages/subdomain_enum.py`, `enums/cert_logs.py`, `enums/cert_logs.py`, `enums/dict_brute_force.py`, `enums/dns_zone.py`, `enums/search_queries.py`
- **Team 3:** `scanners/sqli_scanner.py`, `scanners/scanner_registry.py`
- **Team 4:** `exploits/sqli_exploit.py`, `utils/http_client.py`

### Shared Files (Coordinate before editing):
- `core/target.py` - Data models (Team 1 owns, others request changes)
- `requirements.txt` - Update together
- `config.yaml` - Assign sections to teams

### Git Workflow:
```bash
# Before starting work:
git pull origin main

# Work on your feature:
git checkout -b feature/sqli-scanner
# ... code code code ...

# Commit often:
git add .
git commit -m "Add error-based SQLi detection"

# Before pushing (avoid conflicts):
git pull origin main
# Fix any conflicts
git push origin feature/sqli-scanner

# Create pull request for review
```

---

## RISK MITIGATION
==================

### If Behind Schedule by Day 4:
- [ ] Cut boolean-based SQLi (stick to error-based only)
- [ ] Cut crt.sh integration (dictionary enumeration only)
- [ ] Cut interactive exploit selection (auto-exploit all)
- [ ] Cut colored output (plain text is fine)

### If Behind Schedule by Day 5:
- [ ] Cut UNION-based exploitation (version extraction only)
- [ ] Cut file logging (console only)
- [ ] Cut multiple subdomain techniques (one method only)
- [ ] Simplify demo (pre-recorded video backup)

### Emergency Plan (Day 6):
- [ ] Focus only on 1 working end-to-end demo
- [ ] Pre-generate scan results to show
- [ ] Prepare slides explaining architecture
- [ ] Have team members demo their specific modules

---

## TESTING CHECKLIST
====================

### Daily Tests (5 min):
- [ ] Pipeline runs without crashing
- [ ] Finds at least 1 subdomain
- [ ] Detects at least 1 SQLi
- [ ] Saves results to file

### Pre-Demo Tests (Day 6):
- [ ] Test against testphp.vulnweb.com
- [ ] Test against testaspnet.vulnweb.com
- [ ] Verify subdomain enumeration works
- [ ] Confirm SQLi detection works
- [ ] Test save/resume functionality
- [ ] Check error handling (invalid domain, network timeout)
- [ ] Verify logging works
- [ ] Test with 2-3 different targets
- [ ] Run on fresh machine (simulate grader environment)

---

## COMMON PITFALLS TO AVOID
===========================

1. ⚠️ **Over-engineering** - Build MVP first, add features later
2. ⚠️ **No communication** - Daily standups are mandatory
3. ⚠️ **Testing on last day** - Test daily, fix bugs immediately
4. ⚠️ **Merge conflicts** - Follow file ownership rules
5. ⚠️ **Scope creep** - Say NO to "cool" features
6. ⚠️ **Working in silos** - Integrate early and often
7. ⚠️ **Perfectionism** - Done is better than perfect
8. ⚠️ **No error handling** - Code defensively from day 1

---

## SAFE TESTING TARGETS
=======================

**Always use these (designed for testing):**
- ✅ http://testphp.vulnweb.com (Best for SQLi)
- ✅ http://testaspnet.vulnweb.com (ASP.NET SQLi)
- ✅ http://demo.testfire.net (Banking app simulator)
- ✅ https://portswigger.net/web-security (Various labs)

**⚠️ NEVER test:**
- ❌ Production websites
- ❌ Sites without written permission
- ❌ Government/military sites
- ❌ Financial institutions

---

## DEMO SCRIPT (Practice This)
===============================

**Duration: 10 minutes**

1. **Introduction (1 min)**
   - "GrayTera is an automated DAST tool for pentesting"
   - Show architecture diagram
   - Explain 3-stage pipeline

2. **Live Demo (6 min)**
```bash
   # Show help
   python main.py --help
   
   # Run full scan
   python main.py testphp.vulnweb.com
   
   # Show results
   cat data/scans/testphp.vulnweb.com/scan_data.json
```

3. **Results Walkthrough (2 min)**
   - Show discovered subdomains
   - Show detected vulnerabilities
   - Show exploitation results

4. **Q&A (1 min)**

**Backup Plan:** Pre-recorded video if live demo fails

---

## SUCCESS METRICS
==================

**Minimum Viable Demo:**
- ✅ Finds 5+ subdomains
- ✅ Detects 1+ SQLi vulnerability
- ✅ Extracts database version
- ✅ Saves results to file
- ✅ Runs without crashing

**Good Demo:**
- Above + colored output + error handling

**Great Demo:**
- Above + multiple targets + boolean-based SQLi