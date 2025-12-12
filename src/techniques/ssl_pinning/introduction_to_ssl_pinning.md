## 1. Introduction to SSL Pinning

### What is SSL/Certificate Pinning?

SSL Pinning (also known as Certificate Pinning or Public Key Pinning) is a security technique that associates a host with its expected X.509 certificate or public key. Once a certificate or public key is known or seen for a host, the certificate or public key is associated or "pinned" to the host.

### Why Applications Use SSL Pinning

1. **Prevent Man-in-the-Middle (MITM) Attacks**: Even if an attacker has a trusted CA certificate installed on the device, they cannot intercept traffic.

2. **Protect Against Compromised CAs**: If a Certificate Authority is compromised, pinning prevents accepting fraudulent certificates.

3. **Ensure Data Integrity**: Guarantees communication only with the intended server.

4. **Compliance Requirements**: Many security standards (PCI-DSS, HIPAA) recommend or require certificate pinning.

### Types of Pinning

| Type | Description | Security Level | Flexibility |
|------|-------------|----------------|-------------|
| **Certificate Pinning** | Pin the entire X.509 certificate | Highest | Lowest (must update app when cert changes) |
| **Public Key Pinning** | Pin only the Subject Public Key Info (SPKI) | High | Medium (survives cert renewal if key unchanged) |
| **Hash Pinning** | Pin SHA-256 hash of certificate or public key | High | Medium |
| **CA Pinning** | Pin the intermediate or root CA | Medium | Highest |

---

