# Kali VM Configuration for Google AI VRP

**Date:** 2025-12-05
**Target:** Google AI Vulnerability Reward Program
**Purpose:** AI security testing platform

---

## VM SPECIFICATIONS

### Hardware Allocation:
- **vCPUs:** 6 (half of available 12 cores for parallel testing)
- **RAM:** 16GB (AI fuzzing tools memory-intensive)
- **Disk:** 100GB qcow2 (tools + datasets + test results)
- **Network:** Bridge to Tailscale (secure remote access)
- **Graphics:** VNC enabled (GUI-based tools like Burp Suite)

### Network Configuration:
- **Primary:** virbr0 (NAT for internet access)
- **Tailscale:** Install daemon for secure remote testing (100.110.82.187)
- **DNS:** 1.1.1.1 (Cloudflare) for privacy

---

## KALI TOOLS INSTALLATION MANIFEST

### Category 1: Core Testing Tools (Must-Have)

#### Web Application Testing:
- **Burp Suite Professional** - Primary web proxy, API testing
- **OWASP ZAP** - Alternative proxy for automation
- **Firefox Developer Edition** - Custom extensions
- **Chrome/Chromium** - Testing across browsers

#### AI-Specific Tools:
- **Python 3.12** (already in Messiah env - link to Kali)
- **OpenAI Python SDK** - API interaction testing
- **anthropic-sdk** - Claude API testing
- **LangChain** - LLM framework exploitation testing
- **Garak** - AI red-teaming framework
- **PromptFoo** - Prompt injection testing
- **AI Goat** - Vulnerable LLM playground

#### Reconnaissance:
- **subfinder** - Passive subdomain enumeration
- **amass** - OSINT gathering
- **httpx** - HTTP probe tool
- **nuclei** - Vulnerability scanner (validate manually)

### Category 2: Custom Development Tools

#### Programming Environments:
- **VS Code** - IDE for custom exploit development
- **Jupyter Notebook** - Interactive AI testing notebooks
- **Git** - Version control for test scripts

#### Python Libraries:
```python
# AI Security Testing
openai
anthropic
langchain
transformers
torch  # If GPU passthrough enabled

# Web Testing
requests
beautifulsoup4
selenium
playwright

# Data Analysis
pandas
numpy
matplotlib

# Exploit Development
pwntools
scapy
```

### Category 3: Documentation & Reporting

- **CherryTree** - Hierarchical note-taking
- **Obsidian** - Markdown knowledge base
- **Screenshot/recording tools** - Flameshot, peek
- **Markdown editor** - For report writing

---

## AI VULNERABILITY TESTING FRAMEWORK

### Custom Scripts to Develop:

#### 1. `gemini_fuzzer.py`
**Purpose:** Automated prompt injection testing against Gemini
**Features:**
- Payload library (indirect prompts, admin instructions, encoding bypasses)
- Response analysis (detect jailbreak success)
- Rate limiting (stay within ToS)
- Result logging to pgai database

#### 2. `model_exfil_detector.py`
**Purpose:** Detect model theft vulnerabilities
**Features:**
- Incremental prompt extraction
- Training data leakage tests
- Model weight inference attempts
- Baseline comparison analysis

#### 3. `ai_phishing_generator.py`
**Purpose:** Test if AI can be tricked into enabling phishing
**Features:**
- Generate fake Google Security alerts via prompt injection
- Test email summarization exploits (Gemini Workspace bug class)
- Screenshot evidence capture
- Impact assessment automation

#### 4. `cloud_assist_log_injection.py`
**Purpose:** Test log-to-prompt injection (Trifecta vuln class)
**Features:**
- Craft malicious log entries
- Monitor Gemini Cloud Assist behavior
- Detect command execution
- Proof-of-concept builder

---

## TAILSCALE INTEGRATION

### Installation Steps:
1. Install Tailscale: `curl -fsSL https://tailscale.com/install.sh | sh`
2. Authenticate: `tailscale up`
3. Set hostname: `tailscale set --hostname kali-aivrp`
4. Enable auto-start: `systemctl enable --now tailscaled`

### Access URLs:
- **SSH:** `ssh root@100.110.82.187`
- **Burp Suite Proxy:** `http://100.110.82.187:8080` (if exposed)
- **Jupyter Notebook:** `http://100.110.82.187:8888` (for remote testing)

---

## SECURITY HARDENING

### Firewall Rules (UFW):
```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow from 100.64.0.0/10  # Tailscale subnet
ufw allow 22/tcp  # SSH via Tailscale only
ufw enable
```

### SSH Configuration:
- Disable password auth (key-only)
- Restrict to Tailscale IPs
- Enable fail2ban

### Testing Isolation:
- **Separate user account** for testing (not root)
- **Virtual environments** for each test suite
- **Database isolation** - test results separate from prod pgai

---

## INTEGRATION WITH WOLF-AI ECOSYSTEM

### Memory Persistence:
All test results ingested to pgai:
```bash
python /mnt/Wolf-code/Wolf-Ai-Enterptises/writers/ingest_agent.py "/kali/test-results/*.md"
```

### Namespace Strategy:
- `google_ai_vrp` - All Google testing
- `gemini_vulns` - Specific Gemini findings
- `ai_attack_patterns` - Reusable exploit techniques

### Ollama Integration:
Kali can query Messiah's Ollama fleet for:
- Payload generation (qwen2.5:0.5b for creative prompts)
- Result analysis (embeddings for similarity detection)
- Report writing (LLM-assisted documentation)

---

## TESTING WORKFLOW

### Phase 1: Reconnaissance
1. Map Google AI product attack surface
2. Enumerate Gemini API endpoints
3. Review disclosed bug reports (learn patterns)
4. Identify feature release timelines (test new features first)

### Phase 2: Baseline Testing
1. Normal API interaction (establish baseline)
2. Document expected behavior
3. Test rate limits and error handling
4. Capture all HTTP traffic in Burp

### Phase 3: Vulnerability Discovery
1. **Prompt Injection:** Hidden instructions, encoding tricks
2. **Model Theft:** Incremental extraction attempts
3. **Data Exfiltration:** User data leakage tests
4. **Phishing Enablement:** Social engineering via AI responses

### Phase 4: Documentation
1. Reproduce vulnerability 3+ times
2. Screenshot/video evidence
3. Write reproduction steps
4. Assess severity and impact
5. Submit via Google VRP portal

### Phase 5: Memory Persistence
1. Ingest all findings to pgai
2. Tag with severity, status, dates
3. Cross-reference similar patterns
4. Update testing playbook

---

## SUCCESS METRICS

### Primary Goal:
- **First valid report submitted** within 2 weeks

### Learning Goals:
- Master AI-specific vulnerability classes
- Build reusable testing framework
- Establish Google AI attack surface map
- Develop novel exploit techniques

### Financial Goals (Realistic):
- **Informational/Low:** $0-500 (learning opportunities)
- **Medium:** $500-3000 (first paychecks)
- **High:** $1000-10000 (if we find a good one)
- **Critical:** $10000+ (moonshot - Trifecta-level discovery)

---

## RISK MITIGATION

### Legal Protection:
- Only test in-scope Google AI products
- Follow VRP rules exactly
- Never exfiltrate real user data
- Responsible disclosure only

### Technical Safety:
- Rate limit all tests (avoid DoS appearance)
- Use test accounts only
- Monitor for detection/blocking
- Stop immediately if flagged

### Operational Security:
- All traffic via Tailscale (encrypted mesh)
- No testing from public IPs
- Separate testing environment from production
- Regular backups of test data

---

**Status:** VM spec ready for deployment
**Next Steps:**
1. Wait for Kali ISO download completion
2. Create VM with virt-install
3. Install Kali + custom tools
4. Configure Tailscale
5. Begin reconnaissance phase
