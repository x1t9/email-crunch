"""
Email extraction, normalization, validation, and regex preset management.
Supports multiple pre-made patterns, custom user patterns, persistent settings,
and obfuscated email decoding.
"""

import os
import re
import json
from typing import List, Set, Iterable, Dict, Tuple, Optional

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")

# Pre-made Email Regex Patterns
PREMADE_PATTERNS: Dict[str, Dict[str, str]] = {
    "standard_catchy": {
        "name": "Standard Catchy (generate.py default)",
        "pattern": r'[a-zA-Z0-9_.%+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
        "description": "Catch-all pattern from generate.py. Handles subdomains, international TLDs, and complex formats."
    },
    "strict_rfc": {
        "name": "Strict RFC 5322 Standard",
        "pattern": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,63}',
        "description": "Standard RFC compliant format. Enforces 2-63 alphabetic character TLDs."
    },
    "corporate_only": {
        "name": "Corporate & Business Only (No Free Mail)",
        "pattern": r'[a-zA-Z0-9._%+-]+@(?!gmail|yahoo|hotmail|outlook|aol|icloud|proton|mail)[a-zA-Z0-9.-]+\.[a-zA-Z]{2,63}',
        "description": "Filters out common free webmail providers (Gmail, Yahoo, Outlook, Hotmail, etc.) to capture B2B leads."
    },
    "modern_tlds": {
        "name": "Modern & Tech TLDs (.io, .ai, .dev, .tech, etc.)",
        "pattern": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.(?:io|ai|dev|tech|app|cloud|co|org|net|com|agency|design|media)',
        "description": "Targets modern startups, tech companies, and agency domain names."
    },
    "obfuscated": {
        "name": "Obfuscated / Anti-Scraping ([at], (at), [dot])",
        "pattern": r'[a-zA-Z0-9._%+-]+\s*(?:\[at\]|\(at\)|@)\s*[a-zA-Z0-9.-]+\s*(?:\[dot\]|\(dot\)|\.)\s*[a-zA-Z]{2,24}',
        "description": "Extracts protected emails written like 'john[at]domain[dot]com' or 'support (at) site.org'."
    }
}

# Common non-email suffixes and asset extensions often preceded by @ (e.g. image@2x.png)
DISALLOWED_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'bmp', 'tiff', 'ico',
    'js', 'css', 'json', 'xml', 'html', 'htm', 'woff', 'woff2', 'ttf', 'eot',
    'mp4', 'mp3', 'wav', 'ogg', 'mov', 'avi', 'zip', 'tar', 'gz', 'rar', '7z',
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'exe', 'dll', 'bin'
}

PUNCTUATION_STRIP = " .,;:!?\'\"`()[]{}<>\\/*#$|~^"


def load_user_config() -> Dict:
    """Loads saved settings from config.json or returns defaults."""
    default_cfg = {
        "active_pattern_key": "standard_catchy",
        "custom_pattern": r'[a-zA-Z0-9_.%+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
        "hardware_acceleration": True,
        "active_ocr_engine": "windows_native" if os.name == 'nt' else "rapidocr"
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                default_cfg.update(data)
        except Exception:
            pass
    return default_cfg


def save_user_config(config: Dict):
    """Saves user settings to config.json."""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    except Exception:
        pass


def compile_pattern(pattern_str: str) -> re.Pattern:
    """Safely compiles a regex pattern string."""
    try:
        return re.compile(pattern_str, re.IGNORECASE)
    except re.error:
        # Fallback to standard catchy
        return re.compile(PREMADE_PATTERNS["standard_catchy"]["pattern"], re.IGNORECASE)


# Default active compiled regex
_current_compiled_regex = compile_pattern(PREMADE_PATTERNS["standard_catchy"]["pattern"])


def set_active_regex(pattern_str: str):
    """Sets the global active extraction regex pattern."""
    global _current_compiled_regex
    _current_compiled_regex = compile_pattern(pattern_str)


def get_active_regex() -> re.Pattern:
    """Returns the current active compiled regex."""
    return _current_compiled_regex


def clean_candidate_email(raw_candidate: str) -> Optional[str]:
    """
    Cleans a candidate email string by removing boundary artifacts,
    normalizing obfuscations, validating TLD, and filtering out assets.
    """
    if not raw_candidate:
        return None
    
    candidate = raw_candidate.strip()
    
    # Normalize obfuscated patterns [at], (at) -> @ and [dot], (dot) -> .
    candidate = re.sub(r'\s*(?:\[at\]|\(at\))\s*', '@', candidate, flags=re.IGNORECASE)
    candidate = re.sub(r'\s*(?:\[dot\]|\(dot\))\s*', '.', candidate, flags=re.IGNORECASE)
    
    # Strip mailto: prefix
    if candidate.lower().startswith('mailto:'):
        candidate = candidate[7:]
        
    candidate = candidate.strip(PUNCTUATION_STRIP)
    
    if '@' not in candidate or len(candidate) < 5 or len(candidate) > 254:
        return None
        
    parts = candidate.split('@')
    if len(parts) != 2:
        return None
        
    user_part = parts[0].strip(PUNCTUATION_STRIP)
    domain_part = parts[1].strip(PUNCTUATION_STRIP)
    
    if not user_part or not domain_part:
        return None
        
    domain_segments = domain_part.split('.')
    if len(domain_segments) < 2:
        return None
        
    tld = domain_segments[-1].lower()
    if len(tld) < 2 or not tld.isalpha():
        return None
        
    if tld in DISALLOWED_EXTENSIONS:
        return None
        
    for seg in domain_segments:
        if not seg or seg.startswith('-') or seg.endswith('-'):
            return None
            
    return f"{user_part}@{domain_part}".lower()


def extract_emails_from_text(text: str, custom_regex: Optional[re.Pattern] = None) -> List[str]:
    """
    Extracts all unique, valid emails from raw text string.
    Uses custom_regex if provided, otherwise get_active_regex().
    """
    if not text:
        return []
        
    regex = custom_regex or get_active_regex()
    seen: Set[str] = set()
    result: List[str] = []
    
    matches = regex.findall(text)
    for raw in matches:
        # If tuple match (from group captures in regex), join parts
        if isinstance(raw, tuple):
            raw = "".join(raw)
        valid = clean_candidate_email(raw)
        if valid and valid not in seen:
            seen.add(valid)
            result.append(valid)
            
    return result


def extract_emails_from_bytes(data: bytes, encoding: str = 'utf-8', custom_regex: Optional[re.Pattern] = None) -> List[str]:
    """Extracts emails from a byte buffer."""
    if not data:
        return []
    try:
        text = data.decode(encoding, errors='ignore')
        return extract_emails_from_text(text, custom_regex=custom_regex)
    except Exception:
        text = data.decode('ascii', errors='ignore')
        return extract_emails_from_text(text, custom_regex=custom_regex)


def deduplicate_email_list(emails: Iterable[str]) -> List[str]:
    """Deduplicates a list of emails while preserving order."""
    seen: Set[str] = set()
    unique_list = []
    for email in emails:
        norm = email.strip().lower()
        if norm and norm not in seen:
            seen.add(norm)
            unique_list.append(norm)
    return unique_list


def get_email_domain(email: str) -> str:
    """Returns domain portion of email in lowercase (e.g. '@gmail.com')."""
    if '@' in email:
        return '@' + email.split('@')[1].lower()
    return "@unknown"
