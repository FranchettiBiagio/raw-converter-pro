# Privacy Policy - Franchetti Raw Converter Pro

**Effective Date:** September 24, 2024  
**Last Updated:** September 24, 2024  
**Version:** 1.0

## Summary

**Franchetti Raw Converter Pro collects zero personal data.**  
No analytics, no telemetry, no crash reports, no network connections.  
Your files never leave your computer.

## Data We Do NOT Collect

| Category | Collected? | Details |
|----------|------------|---------|
| Personal Identifiable Information | ❌ No | Name, email, IP, location, device ID |
| Usage Analytics | ❌ No | Feature usage, session duration, frequency |
| File Content | ❌ No | RAW files, output JPEGs, metadata |
| File Paths/Names | ❌ No | Source/destination folders, filenames |
| System Information | ❌ No | Hardware specs, OS version, installed software |
| Error/Crash Data | ❌ No | Stack traces, exception details |
| License/Registration | ❌ No | No activation, no account system |

## Data Processing (Local Only)

All processing occurs **entirely on your device**:

1. **File Selection**: You choose files/folders via native OS dialogs
2. **RAW Decoding**: LibRaw processes files in memory
3. **Image Operations**: Pillow resizes, watermarks, encodes JPEG
3. **Output**: Files written to your chosen destination folder
4. **Memory Cleanup**: All data released on app close

**No temporary files** are created outside your output folder.

## Network Activity

| Connection Type | Present? | Purpose |
|-----------------|----------|---------|
| Telemetry/Analytics | ❌ No | — |
| Crash Reporting | ❌ No | — |
| Update Checks | ❌ No | Manual only |
| License Validation | ❌ No | No license system |
| Cloud Sync | ❌ No | — |
| Any Outbound | ❌ No | **Zero network capability** |

The compiled executable **does not link** any network libraries (WinHTTP, WinINet, curl, OpenSSL, etc.).

## Your Rights (GDPR / CCPA / LGPD)

Since we process **no personal data**, these regulations don't apply. However, you retain full control:

| Right | How to Exercise |
|-------|-----------------|
| Access | No data exists to access |
| Rectification | No data exists to correct |
| Erasure | Delete the executable |
| Portability | No data to export |
| Restriction | Don't run the app |
| Objection | Don't run the app |
| Automated Decisions | None performed |

## Children's Privacy

The application does not target children under 13 (or 16 in EU). No age verification needed — no data collected from anyone.

## Third-Party Services

**None.** The application:
- Does not embed web views/browsers
- Does not use cloud APIs
- Does not integrate with social media
- Does not use advertising SDKs
- Does not use analytics platforms

## Bundled Libraries (Local Processing Only)

| Library | Purpose | Data Access |
|---------|---------|-------------|
| **LibRaw** (via rawpy) | RAW file decoding | Reads your selected files only |
| **Pillow** | Image processing | Operates on in-memory images |
| **NumPy** | Array operations | In-memory numerical computation |
| **tkinter** | GUI framework | OS window management only |

These libraries run **locally** within the application process. They have no network capability and no data persistence beyond your explicit file operations.

## File System Access

| Location | Access Type | Purpose |
|----------|-------------|---------|
| Source RAW files | Read-only | User-selected via dialog |
| Output folder | Write | User-selected via dialog |
| Application folder | Read-only | Executable and bundled resources |
| Temp (%TEMP%) | None | Not used |
| AppData/LocalAppData | None | Not used |
| Registry | None | Not used |

## Data Retention

| Data | Retention |
|------|-----------|
| In-memory image data | Released immediately after each conversion |
| Log messages (GUI) | Session only, cleared on close |
| User settings (UI) | Session only, not persisted |
| Output JPEGs | Forever (your files, your control) |

## Cookies / Local Storage

**Not applicable** — This is a native desktop application, not a web application. No cookies, localStorage, sessionStorage, IndexedDB, or similar technologies are used.

## International Data Transfers

**None** — No data leaves your device, so no cross-border transfers occur.

## Security Measures

| Measure | Implementation |
|---------|----------------|
| Encryption at rest | Your OS (BitLocker, FileVault, LUKS) |
| Encryption in transit | N/A (no transit) |
| Access control | OS file permissions |
| Audit logging | N/A (no server) |
| Data minimization | **Zero collection by design** |

## Changes to This Policy

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-09-24 | Initial policy |

Future changes will be posted here and in the application's About dialog. Material changes will be highlighted.

## Contact

**Data Protection Officer:** `privacy@franchetti.dev`  
**General Contact:** `support@franchetti.dev`  
**Postal:** Franchetti, [Address], Italy

## Legal Basis (GDPR Art. 6)

No processing occurs → no legal basis required.  
If you consider file conversion "processing," the basis is **Article 6(1)(b)**: necessary for the performance of a contract (the software license) at your explicit direction.

## Compliance

| Regulation | Status | Notes |
|------------|--------|-------|
| **GDPR (EU 2016/679)** | ✅ Compliant | No personal data processed |
| **CCPA (California)** | ✅ Compliant | No personal information collected |
| **LGPD (Brazil)** | ✅ Compliant | Nenhum dado pessoal processado |
| **PIPEDA (Canada)** | ✅ Compliant | No personal information collected |
| **PDPA (Singapore)** | ✅ Compliant | No personal data collected |
| **POPIA (South Africa)** | ✅ Compliant | No personal information processed |

## Verification

You can verify our claims:

1. **Network Monitor**: Run Wireshark/Process Monitor — zero connections
2. **File Monitor**: Run ProcMon — only reads your input, writes your output
3. **Registry Monitor**: No keys created/read
4. **Source Code**: Full source available on GitHub for audit
5. **Binary Analysis**: Strings, imports, sections — no network APIs

---

*This policy reflects the actual behavior of Franchetti Raw Converter Pro v1.0.0. If you observe any discrepancy, please contact privacy@franchetti.dev immediately.*
