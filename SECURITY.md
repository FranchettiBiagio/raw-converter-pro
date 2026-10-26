# Security Policy

## Supported Versions

| Version | Supported | End of Support |
|---------|-----------|----------------|
| 1.0.x   | ✅ Yes    | 2025-09-18     |
| < 1.0   | ❌ No     | —              |

Only the latest minor version of the current major version receives security updates.

---

## Reporting a Vulnerability

**Do not report security vulnerabilities via public GitHub issues.**

### Responsible Disclosure Process

1. **Email**: `security@franchetti.dev`
2. **Subject**: `[SECURITY] Brief description`
3. **Include**:
   - Detailed description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
   - Suggested fix (if any)
   - Your contact information for follow-up

### Response Timeline

| Phase | Target |
|-------|--------|
| Acknowledgment | 48 hours |
| Initial Assessment | 5 business days |
| Fix Development | 30 days (critical), 90 days (moderate) |
| Release & Disclosure | Coordinated with reporter |

We follow **Coordinated Vulnerability Disclosure (CVD)**. Public disclosure occurs after a fix is released and users have had reasonable time to update.

---

## Security Architecture

### Threat Model

| Asset | Threat | Mitigation |
|-------|--------|------------|
| User RAW files | Malicious file parsing | LibRaw sandboxed, no code execution |
| Output JPEGs | Metadata leakage | Optional EXIF strip (planned) |
| User system | Privilege escalation | No admin rights, no install, no services |
| Network | Data exfiltration | **Zero network capability** |
| Supply chain | Compromised dependencies | Pinned versions, verified hashes |

### Key Security Properties

1. **No Network Stack**
   - Application never opens sockets
   - No HTTP/HTTPS/FTP/websocket libraries bundled
   - No telemetry, analytics, crash reporting
   - No auto-update mechanism

2. **No Persistence**
   - No registry writes
   - No AppData/LocalAppData writes
   - No scheduled tasks, services, drivers
   - Runs entirely in user memory space

3. **Input Validation**
   - File extension allowlist (25 formats)
   - LibRaw validates RAW structure before decode
   - Pillow validates image operations
   - Path traversal prevented by `pathlib.Path`

4. **Memory Safety**
   - Python managed memory (no manual malloc/free)
   - LibRaw C++ code audited by upstream
   - NumPy/Pillow C extensions mature, widely used

5. **Least Privilege**
   - Runs as standard user
   - No UAC elevation prompt
   - File access only via explicit user dialogs

---

## Dependency Security

### Pinned Versions (requirements.txt)
```text
rawpy==0.27.1
pillow==12.3.0
numpy==2.5.3
```

### Update Policy
- **Security patches**: Within 14 days of upstream release
- **Feature updates**: Quarterly review
- **Vulnerability scanning**: Automated via GitHub Dependabot

### Verification
```bash
# Verify installed packages match requirements
pip freeze | grep -E "rawpy|pillow|numpy"

# Check for known vulnerabilities
pip audit
# or
safety check
```

---

## Build Integrity

### Reproducible Builds
```bash
# Fixed Python version (3.12.10)
# Fixed PyInstaller version (6.22.3)
# Fixed dependency versions
python build_exe.py
```

### Binary Verification
| Check | Method |
|-------|--------|
| **SHA-256** | Published on GitHub Releases |
| **Code Signing** | Planned (EV certificate) |
| **VirusTotal** | Community scans encouraged |

### Anti-Tampering
- Single-file executable (PyInstaller --onefile)
- Embedded manifest with `requestedExecutionLevel=asInvoker`
- No external DLL dependencies (all bundled)

---

## Privacy by Design

| Data Type | Collected | Stored | Transmitted |
|-----------|-----------|--------|-------------|
| RAW files | ❌ | ❌ | ❌ |
| Output JPEGs | ❌ | ❌ | ❌ |
| File paths | ❌ | ❌ (memory only) | ❌ |
| Settings | ❌ | ❌ (memory only) | ❌ |
| Usage stats | ❌ | ❌ | ❌ |
| Crash reports | ❌ | ❌ | ❌ |
| Personal info | ❌ | ❌ | ❌ |

**GDPR/CCPA**: Not applicable — no personal data processed.

---

## Secure Deployment (Enterprise)

### Group Policy / Intune
```xml
<!-- Example AppLocker rule: allow only signed Franchetti executable -->
<RuleCollection Type="Exe" EnforcementMode="Enabled">
  <FilePublisherRule Id="..." Name="Franchetti Raw Converter Pro"
    Description="Official release" UserOrGroupSid="S-1-1-0"
    Action="Allow">
    <Conditions>
      <FilePublisherCondition PublisherName="O=Franchetti, L=City, S=State, C=IT"
        ProductName="Franchetti Raw Converter Pro" BinaryName="FranchettiRawConverterPro.exe">
        <BinaryVersionRange LowSection="2.50.1.0" HighSection="2.9999.9999.9999" />
      </FilePublisherCondition>
    </Conditions>
  </FilePublisherRule>
</RuleCollection>
```

### Network Isolation
- Application functions fully offline
- No firewall exceptions needed
- No proxy configuration needed

---

## Incident Response

### If You Suspect Compromise
1. **Stop using** the application
2. **Delete** the executable and any downloaded copies
3. **Report** to `security@franchetti.dev`
4. **Monitor** official channels for advisory

### Official Channels
- **GitHub Releases**: https://github.com/franchetti/raw-converter-pro/releases
- **Website**: https://franchetti.dev/raw-converter-pro
- **uptodown.dev**: https://www.uptodown.dev/apps/franchetti-raw-converter-pro

**Verify SHA-256** before running any downloaded file.

---

## Security Hall of Fame

We recognize responsible disclosure:

| Researcher | Vulnerability | Date | Status |
|------------|---------------|------|--------|
| — | — | — | — |

*Be the first! Report to security@franchetti.dev*

---

## Contact

**Security Team**: `security@franchetti.dev`  
**PGP Key**: [Available on request]  
**Response SLA**: 48 hours acknowledgment

---

*Last updated: 2024-09-18*  
*Policy version: 1.0*