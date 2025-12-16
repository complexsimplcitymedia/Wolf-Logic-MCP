# Bug Bounty Rules of Engagement - 2025

**Date:** 2025-12-05
**Purpose:** Legal and technical guidelines for authorized vulnerability research

---

## FORBIDDEN TECHNIQUES (Universal - DO NOT USE)

### Strictly Prohibited Actions:
1. **Denial of Service (DoS/DDoS)** - Never crash services, flood networks, or impact availability
2. **Credential Brute Forcing** - No password spraying, brute force, or credential stuffing
3. **Subdomain Takeover as PoC** - Don't actually take over subdomains to prove vulnerability
4. **Out-of-Scope Testing** - Only test explicitly authorized domains/assets listed in program scope
5. **Social Engineering** - No phishing, pretexting, or non-technical attacks against employees
6. **Data Exfiltration** - Never steal, access, or modify user data beyond minimal PoC
7. **Automated Scanning Without Validation** - Don't blindly run automated vulnerability scanners
8. **Physical Security Testing** - No physical intrusion, tailgating, or facility access attempts
9. **Third-Party Testing** - Don't test vendors, partners, or services not explicitly in-scope

---

## ALLOWED TESTING METHODS

### Approved Techniques:
- **Manual Web Application Testing** (XSS, CSRF, SQLi, IDOR, authentication bypasses)
- **Passive Subdomain Enumeration** (DNS queries, certificate transparency logs)
- **API Endpoint Testing** (within rate limits, respecting terms of service)
- **Security Misconfigurations** (exposed admin panels, open S3 buckets, .git disclosure)
- **Authentication/Authorization Flaws** (privilege escalation, broken access control)
- **Information Disclosure** (sensitive data exposure, verbose errors)
- **Business Logic Vulnerabilities** (race conditions, improper workflow)

### Testing Best Practices:
- Use **rate limiting** (delays between requests to avoid detection as attack)
- **Document everything** (screenshots, HTTP requests/responses, exact reproduction steps)
- **Test on staging/dev environments** when available
- **Minimize impact** (test with test accounts, avoid production data)

---

## LEGAL PROTECTION REQUIREMENTS

### Before Testing Any Program:
1. **Safe Harbor Policy** - Verify program has legal protection clause (shields from CFAA prosecution)
2. **Scope Documentation** - Read ENTIRE scope document (in-scope AND out-of-scope sections)
3. **Responsible Disclosure** - Never publicly disclose vulnerability before company patches
4. **Terms of Service** - Comply with all platform ToS and program-specific rules
5. **Authorization** - Only test when explicitly authorized by program owner

### During Testing:
- Respect **rate limits** and server resources
- Stop testing if you trigger alerts or get blocked
- Report immediately upon discovery (don't continue exploiting)
- Maintain confidentiality of discovered vulnerabilities

---

## VULNERABILITY SEVERITY LEVELS

### Critical (Typically $5,000 - $50,000+):
- Remote Code Execution (RCE)
- SQL Injection leading to data breach
- Authentication bypass affecting all users
- Full account takeover (admin/privileged accounts)

### High (Typically $1,000 - $10,000):
- Stored/Reflected XSS on sensitive pages
- IDOR exposing PII
- CSRF on critical functions
- Authorization bypass

### Medium (Typically $500 - $3,000):
- Subdomain takeover (without execution)
- Open redirects on authentication flows
- Information disclosure (internal IPs, stack traces)

### Low (Typically $100 - $500):
- Minor information disclosure
- Self-XSS
- Missing security headers (CSP, HSTS)

### Informational (Usually no reward):
- Descriptive error messages
- Missing rate limiting on non-critical endpoints
- Outdated software without known vulnerabilities

---

## REPORTING REQUIREMENTS

### Every Report Must Include:
1. **Vulnerability Summary** (1-2 sentences describing the issue)
2. **Severity Assessment** (Critical/High/Medium/Low with justification)
3. **Steps to Reproduce** (detailed, numbered steps)
4. **Proof of Concept** (screenshots, video, or code)
5. **Impact Analysis** (what attacker could achieve)
6. **Affected URLs/Endpoints** (exact targets)
7. **Suggested Remediation** (optional but valued)

### Report Quality Tips:
- One vulnerability per report (don't bundle multiple issues)
- Clear, professional language
- Assume reader has no context about your testing
- Include HTTP requests/responses where relevant
- Redact any real user data in screenshots

---

## PLATFORM-SPECIFIC NOTES

### HackerOne:
- Reputation system (0-100+ points)
- Private invitations unlock at higher reputation
- Bounty ranges publicly visible per program
- Median response time: 24-72 hours

### Bugcrowd:
- Application required for private programs
- VRT (Vulnerability Rating Taxonomy) for standardized severity
- CrowdMatch AI matches researchers to programs
- Focus on quality over quantity

### Intigriti:
- European focus (GDPR compliance important)
- Clear ROE documentation required
- Faster payouts than competitors
- Community-driven researcher support

---

## COMMON MISTAKES TO AVOID

1. **Testing Out-of-Scope Assets** - Most common reason for report rejection
2. **Duplicate Reports** - Check disclosed reports before submitting
3. **Low-Quality PoC** - "Here's a vulnerability, figure it out" won't get paid
4. **Ignoring Program Rules** - Some programs exclude certain vuln types
5. **Public Disclosure** - Never tweet/blog about vuln before resolution
6. **Automated Tool Output** - Don't submit raw Burp/Nessus scan results
7. **Spamming Reports** - Quality > Quantity, build reputation carefully

---

## RECOMMENDED TESTING WORKFLOW

### Phase 1: Reconnaissance (Passive)
- Review program scope and rules
- Enumerate subdomains (certificate transparency, DNS)
- Identify technology stack (Wappalyzer, BuiltWith)
- Map application architecture

### Phase 2: Active Discovery
- Manual browsing of application
- Proxy all traffic through Burp Suite
- Identify input points, parameters, endpoints
- Test authentication flows

### Phase 3: Vulnerability Testing
- Manual testing for common vulnerabilities
- Parameter tampering, injection attacks
- Authorization testing (horizontal/vertical privilege escalation)
- Business logic testing

### Phase 4: Documentation
- Reproduce vulnerability 3+ times
- Capture all evidence (screenshots, requests)
- Write clear reproduction steps
- Assess impact and severity

### Phase 5: Reporting
- Submit through platform with all required details
- Monitor for triage/questions
- Respond to any clarification requests
- Wait for resolution before further testing

---

## KALI LINUX TOOL RECOMMENDATIONS

### Essential (Must Have):
- **Burp Suite Community/Pro** - Web proxy, primary testing tool
- **Firefox/Chrome with Extensions** - Wappalyzer, FoxyProxy
- **Notepad/CherryTree** - Documentation and note-taking
- **Subfinder/Amass** - Passive subdomain enumeration

### Advanced (Use With Caution):
- **SQLmap** - SQL injection (only on confirmed injectable parameters)
- **ffuf/gobuster** - Directory brute forcing (watch rate limits)
- **Nuclei** - Vulnerability scanning (validate all findings manually)

### Forbidden (Do Not Use):
- ❌ Metasploit (unless explicitly authorized for PoC)
- ❌ DDoS tools (hping3, LOIC, slowloris)
- ❌ Credential stuffing tools
- ❌ Exploits without understanding impact

---

## SOURCES & REFERENCES

- HackerOne Bug Bounty Programs: https://www.hackerone.com/bug-bounty-programs
- Bugcrowd Program List: https://www.bugcrowd.com/bug-bounty-list/
- Intigriti Rules of Engagement: https://kb.intigriti.com/en/articles/5317169-rules-of-engagement-testing-requirements
- Bug Bounty Beginners Guide (2025): https://www.stationx.net/bug-bounty-programs-for-beginners/
- OWASP Testing Guide: https://owasp.org/www-project-web-security-testing-guide/

---

**Last Updated:** 2025-12-05
**Review Frequency:** Monthly or upon major platform policy changes
