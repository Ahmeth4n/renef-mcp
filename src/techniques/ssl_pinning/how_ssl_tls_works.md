## 2. How SSL/TLS Works

### TLS Handshake Process

```
Client                                              Server
   |                                                   |
   |  1. ClientHello (supported ciphers, random)       |
   |-------------------------------------------------->|
   |                                                   |
   |  2. ServerHello (chosen cipher, random)           |
   |  3. Certificate (server's X.509 certificate)      |
   |  4. ServerKeyExchange (if needed)                 |
   |  5. ServerHelloDone                               |
   |<--------------------------------------------------|
   |                                                   |
   |  6. ClientKeyExchange (pre-master secret)         |
   |  7. ChangeCipherSpec                              |
   |  8. Finished (encrypted)                          |
   |-------------------------------------------------->|
   |                                                   |
   |  9. ChangeCipherSpec                              |
   | 10. Finished (encrypted)                          |
   |<--------------------------------------------------|
   |                                                   |
   |  ============ Encrypted Data Exchange =========== |
```

### Certificate Chain Validation (Normal)

```
┌─────────────────────────────────────────────────────────────┐
│                     Root CA (Self-signed)                    │
│                    Trusted by OS/Browser                     │
└─────────────────────────┬───────────────────────────────────┘
                          │ Signs
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Intermediate CA                           │
│                  Signed by Root CA                           │
└─────────────────────────┬───────────────────────────────────┘
                          │ Signs
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Server Certificate                         │
│              Signed by Intermediate CA                       │
│              Contains: domain, public key, validity          │
└─────────────────────────────────────────────────────────────┘
```

### Where Pinning Intercepts

```
Normal Flow:
Certificate → Chain Validation → Trust Store Check → ✓ Accept

With Pinning:
Certificate → Chain Validation → Trust Store Check → PIN CHECK → ✓/✗
                                                          ↑
                                                   Additional validation
                                                   against stored pin
```

---

