# BlankOBF Deobfuscator - Quick Start Guide

## What is This?

This is a **static analysis tool** for deobfuscating Python malware obfuscated with BlankOBF. It safely analyzes obfuscated code WITHOUT executing it.

## Files Included

1. **deobfuscator.py** - Main deobfuscation tool
2. **advanced_analyzer.py** - Advanced analysis features
3. **example_obfuscated.py** - Example obfuscated file for testing
4. **README.md** - Full documentation

## Quick Examples

### Example 1: Basic Deobfuscation

```bash
python deobfuscator.py malware_obfuscated.py -o malware_clean.py
```

### Example 2: Analyze a Built Executable

```bash
python advanced_analyzer.py Built.exe --all
```

This will:
- Extract PyInstaller archive information
- Check for metadata manipulation
- Detect file size pumping
- Show what files are embedded

### Example 3: Extract Malware Configuration

```bash
python advanced_analyzer.py stub.py --extract-config
```

This extracts:
- Discord webhooks / C2 endpoints
- Enabled modules (password theft, cookie theft, etc.)
- Persistence mechanisms
- Evasion techniques

### Example 4: Analyze AES Payload

```bash
python advanced_analyzer.py blank.aes --analyze-aes
```

## Understanding the Obfuscation

BlankOBF uses multiple layers:

```
Original Code (stub.py)
    ↓
[Marshal compile]
    ↓
Layer 1: Base64 + ROT13 + Variable splitting
    ↓
Layer 2: LZMA compression + String encryption
    ↓
Layer 3 (optional): Additional Base64 + LZMA
    ↓
Obfuscated Python file
    ↓
[Py compile to .pyc]
    ↓
[Zip]
    ↓
[AES-GCM encrypt]
    ↓
[ZLIB compress]
    ↓
[Reverse bytes]
    ↓
blank.aes
    ↓
[Bundled with loader-o.py in PyInstaller]
    ↓
Built.exe (with stolen certificate, metadata removed, size pumped)
```

## Limitations

⚠️ **Marshal Limitation**: The original code is compiled to Python bytecode using `marshal`. This cannot be perfectly decompiled back to source without specialized tools.

✅ **What you CAN get**:
- Disassembly of bytecode
- Extracted string literals
- Overall structure
- Configuration values

❌ **What you CAN'T get** (without additional tools):
- Perfect recreation of original source
- Variable names (these are lost in bytecode)
- Comments (these are lost in compilation)

## Advanced: Full Deobfuscation Pipeline

If you have a built `.exe` file and want to fully reverse it:

### Step 1: Extract PyInstaller Archive
```bash
# Use pyinstxtractor or similar tool
python pyinstxtractor.py Built.exe
```

### Step 2: Extract loader-o.pyc
Look in the extracted files for `loader-o.pyc`

### Step 3: Decompile loader-o.pyc
```bash
uncompyle6 loader-o.pyc > loader-o.py
```

### Step 4: Extract AES Key/IV
Look in `loader-o.py` for:
```python
key = base64.b64decode("...")
iv = base64.b64decode("...")
```

### Step 5: Decrypt blank.aes
```python
import base64, zlib
from pyaes import AESModeOfOperationGCM

key = base64.b64decode("YOUR_KEY_HERE")
iv = base64.b64decode("YOUR_IV_HERE")

with open("blank.aes", "rb") as f:
    data = f.read()

# Reverse, decompress, decrypt
data = data[::-1]
data = zlib.decompress(data)
data = AESModeOfOperationGCM(key, iv).decrypt(data)

with open("decrypted.zip", "wb") as f:
    f.write(data)
```

### Step 6: Extract and Decompile stub-o.pyc
```bash
unzip decrypted.zip
uncompyle6 stub-o.pyc > stub-o.py
```

### Step 7: Deobfuscate stub-o.py
```bash
python deobfuscator.py stub-o.py -o final_malware.py
```

## Safety Notes

✅ This tool is safe because:
- No code execution
- Only static pattern matching and decompression
- Safe library functions only (base64, zlib, lzma, re)

❌ Do NOT:
- Execute deobfuscated code on your main machine
- Use `eval()` or `exec()` on untrusted code
- Run the original malware

## Tips for Analysts

1. **Always use a VM** when analyzing malware
2. **Disable network** before running ANY potentially malicious code
3. **Take snapshots** before each step
4. **Use tools like Process Monitor** to see what the malware does
5. **Check VirusTotal** but don't upload unique samples (they become public)

## Getting Help

If the deobfuscator doesn't work:
1. Check if it's actually BlankOBF (look for the comment)
2. Try the advanced analyzer
3. The obfuscator may have been modified
4. Some layers might need manual analysis

## Example Analysis Session

```bash
# 1. Quick check
python advanced_analyzer.py suspicious.exe --all

# 2. If it's BlankOBF, extract and deobfuscate
python deobfuscator.py extracted_script.py -o clean.py

# 3. Extract config
python advanced_analyzer.py clean.py --extract-config

# 4. Review output
cat clean.py
```

## What to Look For

In deobfuscated malware, look for:
- **Discord webhooks**: `https://discord.com/api/webhooks/...`
- **Browser paths**: Passwords, cookies, tokens
- **File operations**: What files it steals
- **Network requests**: Where data is sent
- **Persistence**: Registry keys, startup folders
- **Anti-analysis**: VM detection, debugger detection

## License

Use for security research and malware analysis only.
