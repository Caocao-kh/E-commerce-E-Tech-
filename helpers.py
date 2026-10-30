import os
import re
import time
from functools import wraps
from collections import defaultdict
from urllib.parse import urlparse, urljoin
from flask import request, redirect, url_for, flash, abort
from flask_login import current_user
from werkzeug.security import generate_password_hash

# =========================================================
# FILE UPLOAD CONSTANTS & UTILITIES
# =========================================================

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def allowed_image_file(filename):
    """Check if uploaded file has an allowed image extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


# =========================================================
# WAF (WEB APPLICATION FIREWALL) SIGNATURES & ENGINES
# =========================================================

BLOCKED_USER_AGENTS = {
    "sqlmap", "nikto", "dirbuster", "gobuster", "wpscan", "masscan",
    "acunetix", "havij", "zgrab", "nmap", "nessus", "openvas"
}

PATH_TRAVERSAL_REGEX = re.compile(r'(?i)(\.\./|\.\.\\|%2e%2e|/etc/(?:passwd|shadow)|(?:boot|win)\.ini)')
COMMAND_INJECTION_REGEX = re.compile(r'(?i)(\b(?:cat|ls|rm|nc|curl|wget)\s+/|[;&|`]\s*(?:bash|sh|cmd|powershell))')
SQLI_EXPLOIT_REGEX = re.compile(r'(?i)(\bUNION\b\s+(?:ALL\s+)?\bSELECT\b|\bDROP\b\s+TABLE\b|\bWAITFOR\b\s+DELAY\b|\bSLEEP\(\d+\)|\bEXEC(?:UTE)?\b\s*\(|\bOR\b\s+1\s*=\s*1\s*--|\bAND\b\s+1\s*=\s*1\s*--)')


def sanitize_url_param(val):
    """Strip dangerous pseudo-protocols (javascript:, vbscript:, data:) and HTML script tags."""
    if not val or not isinstance(val, str):
        return val
    if re.search(r'(?i)^\s*(javascript|vbscript|data):', val):
        return ""
    clean = re.sub(r'(?i)<script.*?>.*?</script>', '', val)
    clean = re.sub(r'(?i)on\w+\s*=', '', clean)
    return clean.strip()


def sanitize_js_code(val):
    """Strip dangerous JavaScript code, pseudo-protocols, and inline event handlers."""
    if not val or not isinstance(val, str):
        return val
    val = re.sub(r'(?i)^\s*(javascript|vbscript|data):', '', val)
    val = re.sub(r'(?i)<script.*?>.*?</script>', '', val)
    val = re.sub(r'(?i)\bon\w+\s*=', '', val)
    return val.strip()


def contains_malicious_js(val):
    """Check if value contains malicious JS script tags or executable protocols."""
    if not val or not isinstance(val, str):
        return False
    has_script_tag = bool(re.search(r'(?i)<script.*?>', val))
    has_js_proto = bool(re.search(r'(?i)\bjavascript\s*:', val))
    has_event_handler = bool(re.search(r'(?i)\bon\w+\s*=\s*["\'].*?["\']', val))
    return has_script_tag or has_js_proto or has_event_handler


def detect_waf_threat(val):
    """Inspect string value for severe WAF threat signatures (Path Traversal, Cmd Injection, SQLi)."""
    if not val or not isinstance(val, str):
        return None
    if PATH_TRAVERSAL_REGEX.search(val):
        return "Path Traversal / LFI Signature"
    if COMMAND_INJECTION_REGEX.search(val):
        return "Command Injection Signature"
    if SQLI_EXPLOIT_REGEX.search(val):
        return "SQL Injection Attack Signature"
    return None


def is_safe_redirect_url(target):
    """Ensure redirect target URL is safe and relative to prevent Open Redirect / JS Execution."""
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    if test_url.scheme not in ('http', 'https') or ref_url.netloc != test_url.netloc:
        return False
    if re.search(r'(?i)^\s*javascript:', target):
        return False
    return True


# =========================================================
# DDOS / RATE LIMITING & BRUTE FORCE DEFENSE ENGINES
# =========================================================

class DDoSRateLimiter:
    """Sliding-window IP rate limiter to mitigate DDoS, request floods, and scraper abuse."""
    def __init__(self):
        self.ip_hits = defaultdict(list)
        self.endpoint_hits = defaultdict(list)

    def check(self, ip, endpoint, is_testing=False):
        if is_testing:
            return True, 0

        now = time.time()
        cutoff_min = now - 60.0

        # Global IP rate limit (120 requests/minute)
        hits = [t for t in self.ip_hits[ip] if t > cutoff_min]
        if len(hits) >= 120:
            self.ip_hits[ip] = hits
            return False, 60
        hits.append(now)
        self.ip_hits[ip] = hits

        # Sensitive endpoints (e.g. /login, /register, /checkout: max 12 requests/minute)
        sensitive = any(s in endpoint for s in ("/login", "/register", "/checkout/process"))
        if sensitive:
            ep_key = f"{ip}:{endpoint}"
            ep_hits = [t for t in self.endpoint_hits[ep_key] if t > cutoff_min]
            limit = 10 if "/login" in endpoint else 15
            if len(ep_hits) >= limit:
                self.endpoint_hits[ep_key] = ep_hits
                return False, 60
            ep_hits.append(now)
            self.endpoint_hits[ep_key] = ep_hits

        return True, 0


class BruteForceProtector:
    """Tracks consecutive failed logins and locks accounts/IPs temporarily."""
    def __init__(self, max_attempts=5, lockout_seconds=900):  # 15 minutes lockout
        self.max_attempts = max_attempts
        self.lockout_seconds = lockout_seconds
        self.failed_attempts = defaultdict(list)
        self.lockouts = {}

    def is_locked(self, identifier):
        now = time.time()
        if identifier in self.lockouts:
            expiry = self.lockouts[identifier]
            if now < expiry:
                remaining = int(expiry - now)
                return True, remaining
            else:
                del self.lockouts[identifier]
                self.failed_attempts.pop(identifier, None)
        return False, 0

    def record_failure(self, identifier):
        now = time.time()
        attempts = [t for t in self.failed_attempts[identifier] if now - t < self.lockout_seconds]
        attempts.append(now)
        self.failed_attempts[identifier] = attempts

        if len(attempts) >= self.max_attempts:
            self.lockouts[identifier] = now + self.lockout_seconds
            return True, self.lockout_seconds
        return False, 0

    def record_success(self, identifier):
        self.failed_attempts.pop(identifier, None)
        self.lockouts.pop(identifier, None)

    def reset(self, identifier):
        self.record_success(identifier)


rate_limiter = DDoSRateLimiter()
brute_force_protector = BruteForceProtector(max_attempts=5, lockout_seconds=900)
DUMMY_TIMING_HASH = generate_password_hash("DummyTimingAttackNormalizationString!123", method="pbkdf2:sha256:600000")


def validate_password_complexity(password):
    """
    Enforces enterprise password requirements:
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    - At least 1 special symbol
    - Not in known common weak passwords
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter (A-Z)."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter (a-z)."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number (0-9)."
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?~`]", password):
        return False, "Password must contain at least one special symbol (!@#$%^&* etc.)."

    common_passwords = {
        "password", "12345678", "admin123", "password123", "qwerty123",
        "letmein1", "welcome1", "etech123", "iloveyou"
    }
    if password.lower() in common_passwords:
        return False, "Password is too common and easily guessed."

    return True, ""


# =========================================================
# RBAC ACCESS CONTROL DECORATORS
# =========================================================

def admin_required(f):
    """Ensure user is authenticated AND possesses the 'admin' role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Administrator login required to access the Admin Panel.", "warning")
            return redirect(url_for("admin_login", next=request.url))
        if getattr(current_user, "role", "") != "admin":
            flash("Access denied: You must be signed in with an Administrator account.", "danger")
            return redirect(url_for("admin_login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function
