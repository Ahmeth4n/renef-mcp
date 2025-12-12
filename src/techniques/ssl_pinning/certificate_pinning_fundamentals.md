## 3. Certificate Pinning Fundamentals

### What Gets Pinned

#### 1. Full Certificate (DER/PEM encoded)
```
-----BEGIN CERTIFICATE-----
MIIFazCCA1OgAwIBAgIRAIIQz7DSQONZRGPgu2OCiwAwDQYJKoZIhvcNAQELBQAw
TzELMAkGA1UEBhMCVVMxKTAnBgNVBAoTIEludGVybmV0IFNlY3VyaXR5IFJlc2Vh
...
-----END CERTIFICATE-----
```

#### 2. Subject Public Key Info (SPKI)
```
Public Key Algorithm: RSA
Public Key:
    Modulus (2048 bit):
        00:b6:e0:2f:c2:28:d4:c3:c5:2b:52:c7:e4:e9:b3:
        ...
    Exponent: 65537 (0x10001)
```

#### 3. SHA-256 Hash of SPKI
```
sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=
```

### Extracting Pin Values

```bash
# Extract certificate from server
openssl s_client -connect example.com:443 -servername example.com < /dev/null 2>/dev/null | \
    openssl x509 -outform DER > cert.der

# Get SHA-256 hash of certificate
openssl x509 -in cert.der -inform DER -outform DER | \
    openssl dgst -sha256 -binary | base64

# Get SHA-256 hash of public key (SPKI)
openssl x509 -in cert.der -inform DER -pubkey -noout | \
    openssl pkey -pubin -outform DER | \
    openssl dgst -sha256 -binary | base64

# Using curl to get pin
curl -v https://example.com 2>&1 | grep "public key hash"
```

---

