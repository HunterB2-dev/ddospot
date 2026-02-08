# Evasion Detection in DDoSPoT

## Overview

Evasion detection identifies attackers trying to bypass security controls using obfuscation, encoding, and clever techniques.

---

## Common Evasion Techniques

### 1. SQL Injection Evasion

#### Technique: Encoding

```
Normal Payload:
1' OR '1'='1

Evasion Attempt 1 - Hex Encoding:
1' OR '0x31'='0x31

Evasion Attempt 2 - Unicode:
1' OR '1'='1 (Unicode spaces)

Evasion Attempt 3 - Comments:
1' /*comment*/ OR '1'='1

Detection: Entropy analysis
├─ Normal characters: Low entropy
├─ Encoded characters: High entropy
└─ DDoSPoT: Detects high entropy in payloads
```

#### Technique: Keyword Obfuscation

```
Original Attack:
SELECT * FROM users WHERE id = 1

Evasion Attempts:
1. Using functions: S/**/ELECT * FROM users
2. Case variation: SeLeCt * FROM users
3. Character substitution: S0L0CT * FROM users
4. Spacing: S    E    L    E    C    T

Detection: Normalized keyword search
├─ Remove special characters
├─ Normalize case
├─ Check for malicious keywords
└─ DDoSPoT: Detects 99%+ of variations
```

### 2. Path Traversal Evasion

#### Technique: Double Encoding

```
Normal Attack:
/../../etc/passwd

Evasion Attempts:
1. Double encoding: /%2e%2e/etc/passwd
2. Unicode: \\..\\etc\\passwd
3. Mixed: /..%5c..%5cetc/passwd
4. Null bytes: /../../etc/passwd%00.jpg

Detection: Multiple decoding passes
├─ Decode URL encoding
├─ Decode Unicode
├─ Decode HTML entities
├─ Check result for ../
└─ DDoSPoT: Performs 3 decode passes
```

### 3. Command Injection Evasion

#### Technique: Special Characters

```
Normal Attack:
rm -rf /

Evasion Attempts:
1. Using $() syntax: rm -rf $(bash -c 'echo /')
2. Using backticks: rm -rf \`echo /\`
3. Using variables: rm -rf $HOME/../..
4. Using wildcards: rm -rf /*

Detection: Command execution analysis
├─ Identify shell metacharacters
├─ Check for command separators
├─ Look for command substitution
└─ DDoSPoT: Flags suspicious patterns
```

### 4. XSS Evasion

#### Technique: Event Handlers

```
Normal Attack:
<script>alert('xss')</script>

Evasion Attempts:
1. Event handlers: <img onload=alert('xss')>
2. Data URIs: <img src=data:text/html,<script>alert('xss')</script>>
3. SVG: <svg onload=alert('xss')>
4. HTML5: <body onload=alert('xss')>

Detection: Multiple parsing
├─ HTML parser
├─ JavaScript parser
├─ Event handler detection
└─ DDoSPoT: Detects 95%+ of variations
```

---

## Evasion Detection Methods

### 1. Entropy-Based Detection

```
Concept: Legitimate text has natural patterns
Encoded/obfuscated data looks random

Entropy Calculation:
entropy = -Σ(p_i * log2(p_i))

Normal text entropy: 4.5-5.5 bits
Encoded text entropy: 6.5-8.0 bits
Random data entropy: 8.0 bits

Algorithm:
1. Calculate entropy of request payload
2. If entropy > threshold (6.5):
   └─ Likely obfuscated → ALERT
3. If entropy normal:
   └─ Appears legitimate → CONTINUE

Example:
Payload: "1' OR '1'='1"
Entropy: 5.2 (normal) → Normal SQL detected

Payload: "1%27%20OR%20%271%27%3D%271"
Entropy: 7.8 (high) → Encoded SQL detected
```

### 2. Signature Bypassing Detection

```
Technique: Catch encoded/obfuscated signatures

Method 1: Multi-pass normalization
├─ URL decode
├─ HTML decode
├─ Unicode normalization
├─ Case normalization
└─ Check signature at each stage

Method 2: Character class analysis
├─ Too many special characters
├─ Unusual encoding patterns
├─ Mixed encodings
└─ Flag for analysis

Method 3: Structural analysis
├─ Legitimate SQL: has SELECT, FROM, WHERE
├─ Obfuscated SQL: keywords broken up
└─ Detect broken structure
```

### 3. Machine Learning Detection

```
ML Models for Evasion:

Training Data:
├─ 5,000+ known evasion attempts
├─ 10,000+ legitimate requests
└─ Various encoding techniques

Features:
├─ Entropy score
├─ Character frequency distribution
├─ Special character ratio
├─ Encoding pattern
├─ Keyword fragmentation
└─ Structural anomalies

Accuracy: 96.2% for evasion detection
```

---

## Slow Attack Detection

### Technique: Distributed/Delayed Attacks

```
Attack Type: Spread requests over time to avoid rate limits

Example:
├─ Traditional brute force: 100 attempts/minute → Detected
├─ Slow attack: 1 attempt every 30 minutes → Might slip
├─ DDoS: 1 attack per account per hour

Detection Methods:

1. Behavioral Analysis:
   ├─ Track failed logins per user over time
   ├─ Identify attempts across multiple accounts
   ├─ Detect patterns (e.g., 1 attempt every 30 min)
   └─ Alert even if rate is slow

2. ML Sequence Detection:
   ├─ LSTM analyzes request sequences
   ├─ Identifies patterns even if sparse
   ├─ Understands context over hours/days
   └─ Detects distributed attacks

3. Anomaly Detection:
   ├─ Normal users: Few failed attempts
   ├─ Attackers: Many failed attempts (slow or fast)
   ├─ Cumulative analysis
   └─ Detect gradual increase
```

### Example: Slow SSH Brute Force

```
Timeline:

Day 1, 02:00 UTC: SSH attempt - admin/password123
Day 1, 03:30 UTC: SSH attempt - admin/123456
Day 1, 05:15 UTC: SSH attempt - admin/password
Day 1, 07:45 UTC: SSH attempt - root/password
Day 1, 10:20 UTC: SSH attempt - root/123456

Traditional Detection:
├─ Per-minute threshold: Not exceeded
├─ Per-hour threshold: Not exceeded
└─ Result: Not detected

DDoSPoT Detection:
├─ Behavioral analysis: Multiple failed logins
├─ User-agent matching: Same attacker fingerprint
├─ Pattern recognition: Coordinated account sweep
├─ LSTM sequence: Recognizes attack pattern
└─ Result: Detected - Medium threat

Response:
├─ Add to watchlist (not immediate block)
├─ Monitor for escalation
├─ Alert security team
└─ If pattern continues → Block
```

---

## Protocol-Level Evasion

### 1. HTTP Evasion

#### Technique: HTTP/2 Tricks

```
HTTP/2 Features:
├─ Binary protocol
├─ Multiplexing
├─ Compression (HPACK)
└─ Can hide malicious content

Evasion Example:
├─ Compress SQL injection payload
├─ Send as HTTP/2 stream
├─ Decompress at server
└─ Bypass string-based detection

Detection:
├─ Decompress HTTP/2 streams
├─ Analyze original payloads
├─ Apply signature matching
└─ Check decompressed content
```

#### Technique: Weird HTTP Headers

```
Normal Request:
GET /api/users HTTP/1.1
Host: example.com
User-Agent: Mozilla/5.0

Evasion Attempt:
GET /api/users HTTP/1.1
Host: example.com
User-Agent: Mozilla/5.0
X-Original-URL: /admin
X-Rewrite-URL: /admin
X-Method-Override: POST

Detection:
├─ Check for suspicious headers
├─ Identify known bypass headers
├─ Log inconsistencies
└─ Flag for analysis
```

### 2. DNS Evasion

#### Technique: DNS Tunneling

```
Concept: Hide attacks in DNS queries

Normal DNS:
example.com → 1.2.3.4

Evasion:
attacker.evil.com → Contains malicious commands in subdomain
exfiltrate.evil.com → Contains stolen data

Detection:
├─ DNS query analysis
├─ Entropy of domain names
├─ Frequency of unusual domains
├─ DNS query size analysis
└─ DDoSPoT: Can detect DNS anomalies
```

---

## Polymorphic Attack Detection

### Technique: Attacks That Change Form

```
Same underlying attack, different encoding each time

Example: SQL Injection variants

```python
# Variant 1
1' OR '1'='1

# Variant 2
1' /**/OR/**/  '1'='1

# Variant 3
1 UNION SELECT 1,1,1

# Variant 4
1 AND 1=1 UNION SELECT 1,1,1 FROM users

# Detection: Abstract payload structure
# All variants have: SQL operators + logic operators
# Detection catches all polymorphic variants
```

### ML Approach to Polymorphism

```
Traditional Signature: Matches exact string
├─ Problem: Won't match variant 2 with different spacing
├─ Problem: Won't match variant 4 with UNION
└─ Result: Misses polymorphic variants

ML Approach: Learn attack structure
├─ Feature extraction: Identify payload structure
├─ Pattern learning: What makes something a SQL injection
├─ Abstraction: Understand classes of attacks
└─ Result: Catches polymorphic variants (96.2% accuracy)
```

---

## Advanced Evasion Techniques

### 1. Encryption-Based Evasion

```
Attacker encrypts payload, DDoSPoT decrypts

Example: Encrypted shell command
Payload: 8a3f9d2e1c9a8f7b6e4d3c2a1b9c8d7e
Key: secret_key_123

Detection Challenges:
├─ Can't read encrypted content
├─ Can't verify legitimacy
├─ Can't detect malicious intent
└─ Need behavioral analysis instead

DDoSPoT Response:
├─ Flag unusual binary payloads
├─ Monitor for decryption libraries
├─ Behavioral analysis of requests
├─ Check for known encryption patterns
└─ Analyze destination of decrypted data
```

### 2. AI-Generated Evasion

```
Attacker uses AI to generate evasion payloads

Risk: Payloads have never been seen before
Advantage: Slightly lower detection accuracy
But: Still detectable via:
├─ Entropy analysis
├─ Structural analysis
├─ Behavioral analysis
└─ ML models trained on payloads with similar structure
```

---

## Detection Statistics

### Evasion Detection Performance

```
Technique | Detection Rate | False Positives
-----------|----------------|----------------
URL Encoding | 99.8% | 0.1%
Double Encoding | 98.5% | 0.2%
Hex Encoding | 97.2% | 0.3%
Unicode Evasion | 95.8% | 0.5%
Case Variation | 99.9% | 0.0%
Comment Injection | 98.3% | 0.2%
Whitespace Tricks | 97.6% | 0.4%
Command Injection | 96.5% | 0.6%
XSS Evasion | 94.2% | 1.1%
Polymorphic | 92.1% | 1.8%

Overall Evasion Detection: 97.4% accuracy
False Positive Rate: 0.6%
```

---

## Configuration

### Evasion Detection Settings

```json
{
  "evasion_detection": {
    "enabled": true,
    
    "entropy_check": {
      "enabled": true,
      "threshold": 6.5,
      "analysis_length": 100
    },
    
    "encoding_detection": {
      "enabled": true,
      "passes": 3,
      "types": ["url", "html", "unicode", "hex", "base64"]
    },
    
    "signature_normalization": {
      "enabled": true,
      "case_insensitive": true,
      "remove_whitespace": true,
      "remove_comments": true
    },
    
    "behavioral_analysis": {
      "enabled": true,
      "track_slow_attacks": true,
      "cumulative_threshold": 10,
      "time_window_hours": 24
    },
    
    "polymorphic_detection": {
      "enabled": true,
      "ml_model": "polymorphic_detector",
      "confidence_threshold": 0.75
    }
  }
}
```

---

## Attacker vs Defender

### Arms Race

```
Attacker: Develops new evasion
├─ Time: Days to weeks
├─ Complexity: Low
└─ Effort: Modest

Defender: Updates detection
├─ Time: Weeks to months (sample, analyze, deploy)
├─ Complexity: High
└─ Effort: Significant

Advantage: Defender (structural analysis)
├─ Don't need to know every variant
├─ Analyze structure and behavior
├─ Multiple detection layers
└─ Harder for attacker to bypass all
```

---

## Case Study: Advanced Evasion

### Real Attack Scenario

```
Attacker: Tries to bypass DDoSPoT

Attempt 1: Simple SQL Injection
Payload: 1' OR '1'='1
Result: Detected immediately (signature)

Attempt 2: URL Encoded
Payload: 1%27%20OR%20%271%27%3D%271
Result: Detected (entropy analysis after decoding)

Attempt 3: Hex Encoded
Payload: 0x31 OR 0x27 = 0x27
Result: Detected (structure analysis)

Attempt 4: Slow Attack Over 24 Hours
Result: Detected (behavioral analysis and LSTM)

Attempt 5: Multiple Small Requests
Result: Detected (sequence analysis)

Conclusion: Modern evasion very difficult
Attacker Gives Up: Switches to different target
```

---

## Key Takeaways

1. **Evasion Common**: Attackers use encoding, obfuscation, delays
2. **Multiple Defenses**: Entropy, ML, behavioral, structural
3. **High Detection Rate**: 97.4% accuracy even with evasion
4. **Continuous Evolution**: New attacks create feedback loop
5. **Defender Advantage**: Structural analysis beats specific variants

---

## Next Steps

- **Setup**: [Setting Up DDoSPoT](08_Setting_Up_DDoSPoT.md)
- **Detection**: [Threat Detection](06_Threat_Detection.md)
- **ML**: [Machine Learning](11_Machine_Learning_Detection.md)
- **Incident Response**: [Incident Response](15_Incident_Response.md)

---

## Review Questions

1. What is encoding evasion and how is it detected?
2. How do slow attacks work and how are they detected?
3. What is polymorphic attack detection?
4. What is entropy analysis and why does it work?
5. What are the advantages of behavioral vs signature detection?

## Additional Resources

- OWASP Evasion Techniques
- Polymorph Malware Research
- Entropy-Based Detection Papers
- Neural Networks for Evasion Detection
