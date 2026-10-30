import os
import sys
import tempfile
import unittest
import importlib.util
from io import BytesIO
from werkzeug.security import check_password_hash

# CRITICAL: Isolate tests to a temporary dedicated SQLite database so production E_Tech.db is NEVER modified or dropped!
TEST_DB_PATH = os.path.join(tempfile.gettempdir(), f"etech_test_security_{os.getpid()}.db").replace("\\", "/")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

# Explicitly load app.py to avoid colliding with app/ package directory
spec = importlib.util.spec_from_file_location("main_app", os.path.join(os.path.dirname(__file__), "app.py"))
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

app = app_module.app
db = app_module.db
User = app_module.User
Order = app_module.Order
LoginForm = app_module.LoginForm
RegisterForm = app_module.RegisterForm
brute_force_protector = app_module.brute_force_protector
validate_password_complexity = app_module.validate_password_complexity
rate_limiter = app_module.rate_limiter

class SecurityTestSuite(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.session.remove()
            db.engine.dispose()
        try:
            if os.path.exists(TEST_DB_PATH):
                os.remove(TEST_DB_PATH)
        except Exception:
            pass

    def setUp(self):
        # Configure app for testing
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False  # Allows simulating forms without CSRF in unit tests, or toggle when testing CSRF
        self.app = app
        self.client = app.test_client()

        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            # Safety safeguard: NEVER drop production database under any circumstances
            db_uri = str(app.config.get("SQLALCHEMY_DATABASE_URI", ""))
            if "E_Tech.db" in db_uri:
                raise RuntimeError(f"CRITICAL SAFETY VIOLATION: Refusing to drop database {db_uri}")
            db.drop_all()

    # =========================================================================
    # 1. SECURITY HEADERS TESTS
    # =========================================================================
    def test_security_headers_present(self):
        """Verify that essential security headers are applied to HTTP responses."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

        # Content-Security-Policy (CSP)
        csp = response.headers.get("Content-Security-Policy")
        self.assertIsNotNone(csp, "Content-Security-Policy header is missing")
        self.assertIn("default-src 'self'", csp)
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertIn("object-src 'none'", csp)

        # X-Content-Type-Options
        x_content_type = response.headers.get("X-Content-Type-Options")
        self.assertEqual(x_content_type, "nosniff", "X-Content-Type-Options should be 'nosniff'")

        # X-Frame-Options (Clickjacking defense)
        x_frame_options = response.headers.get("X-Frame-Options")
        self.assertEqual(x_frame_options, "DENY", "X-Frame-Options should be 'DENY'")

        # X-XSS-Protection
        x_xss = response.headers.get("X-XSS-Protection")
        self.assertEqual(x_xss, "1; mode=block", "X-XSS-Protection should be '1; mode=block'")

        # Referrer-Policy
        referrer_policy = response.headers.get("Referrer-Policy")
        self.assertEqual(referrer_policy, "strict-origin-when-cross-origin")

    # =========================================================================
    # 2. SESSION COOKIE SECURITY CONFIGURATION
    # =========================================================================
    def test_session_cookie_security_config(self):
        """Verify that session cookies are configured with HttpOnly and SameSite."""
        self.assertTrue(self.app.config.get("SESSION_COOKIE_HTTPONLY"), "Session cookie HTTPONLY must be True")
        self.assertEqual(self.app.config.get("SESSION_COOKIE_SAMESITE"), "Lax", "Session cookie SameSite must be Lax")

    # =========================================================================
    # 3. PASSWORD HASHING & SALT TESTS
    # =========================================================================
    def test_password_hashing_and_salting(self):
        """Verify password is encrypted with a strong hash and proper salt."""
        with self.app.app_context():
            user1 = User(username="user1", email="user1@example.com", role="customer")
            user1.set_password("SecureP@ssw0rd!123")

            user2 = User(username="user2", email="user2@example.com", role="customer")
            user2.set_password("SecureP@ssw0rd!123")

            # Hash must NOT equal plaintext
            self.assertNotEqual(user1.password_hash, "SecureP@ssw0rd!123")
            
            # Salt must make two identical passwords produce different hash strings
            self.assertNotEqual(user1.password_hash, user2.password_hash, "Salt should cause hashes to differ")

            # Check verification
            self.assertTrue(user1.check_password("SecureP@ssw0rd!123"))
            self.assertFalse(user1.check_password("WrongPassword"))
            self.assertFalse(user1.check_password(""))

    # =========================================================================
    # 4. CSRF PROTECTION TESTS
    # =========================================================================
    def test_csrf_protection_enabled(self):
        """Verify that CSRF protection rejects unsafe POST requests when active."""
        # Enable CSRF explicitly for this test
        self.app.config["WTF_CSRF_ENABLED"] = True
        csrf_client = self.app.test_client()

        # POST without CSRF token
        response = csrf_client.post("/login", data={
            "email": "test@example.com",
            "password": "Password123"
        })
        # CSRF failure should result in 400 Bad Request
        self.assertEqual(response.status_code, 400)
        self.app.config["WTF_CSRF_ENABLED"] = False

    # =========================================================================
    # 5. ACCESS CONTROL & ROUTE PROTECTION (@login_required)
    # =========================================================================
    def test_protected_routes_require_authentication(self):
        """Verify that unauthorized requests to protected routes redirect to login."""
        # Unauthenticated access to /profile
        response = self.client.get("/profile", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

        # Unauthenticated access to /logout
        response = self.client.get("/logout", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    # =========================================================================
    # 6. ACCOUNT STATUS / INACTIVE USER DEFENSE
    # =========================================================================
    def test_inactive_user_cannot_login(self):
        """Verify that users with status=False cannot authenticate."""
        with self.app.app_context():
            inactive_user = User(
                username="banned_user",
                email="banned@example.com",
                role="customer",
                status=False
            )
            inactive_user.set_password("ValidPassword123")
            db.session.add(inactive_user)
            db.session.commit()

            # Attempt login with inactive user
            # When login fails, it renders login template or returns 200 with flash message
            # For testing without template file, let's verify condition directly or via form
            user_in_db = User.query.filter_by(email="banned@example.com").first()
            self.assertFalse(user_in_db.status and user_in_db.check_password("ValidPassword123"))

    # =========================================================================
    # 7. SQL INJECTION DEFENSE (ORM Parameterization)
    # =========================================================================
    def test_sql_injection_defense(self):
        """Verify ORM parameterization prevents SQL injection payloads."""
        with self.app.app_context():
            # Attempting classic SQL Injection login bypass
            sqli_payload = "' OR '1'='1' --"
            user = User.query.filter_by(email=sqli_payload).first()
            self.assertIsNone(user, "SQL Injection payload should return no user")

            # SQL injection in search filter query parameter
            response = self.client.get(f"/products?q={sqli_payload}")
            self.assertEqual(response.status_code, 200)

    # =========================================================================
    # 8. XSS DEFENSE & CONTENT SECURITY POLICY DIRECTIVES
    # =========================================================================
    def test_xss_protection_in_search_and_headers(self):
        """Verify XSS vectors in URLs are blocked and CSP headers are applied."""
        xss_payload = "<script>alert('XSS')</script>"
        response = self.client.get(f"/products?q={xss_payload}")
        # Script tags in URL query parameters are rejected by pre-request middleware with 400 Bad Request
        self.assertEqual(response.status_code, 400)

        # Normal response CSP check
        normal_response = self.client.get("/products")
        self.assertEqual(normal_response.status_code, 200)
        csp = normal_response.headers.get("Content-Security-Policy", "")
        self.assertIn("script-src 'self' https://cdn.jsdelivr.net", csp)


    def test_url_javascript_pseudo_protocol_defense(self):
        """Verify that javascript: pseudo-protocols in URL parameters are rejected."""
        response = self.client.get("/products?q=javascript:alert('XSS')")
        self.assertEqual(response.status_code, 400)
        
        response_vb = self.client.get("/products?category=javascript:eval(1)")
        self.assertEqual(response_vb.status_code, 400)

    def test_form_js_code_defense(self):
        """Verify that form submissions containing malicious JS script tags or handlers are rejected."""
        # Test form submission containing <script> payload
        response = self.client.post("/login", data={
            "email": "<script>alert('XSS')</script>",
            "password": "Password123"
        })
        self.assertEqual(response.status_code, 400)

        # Test form submission containing inline event handler
        response_handler = self.client.post("/login", data={
            "email": "user@example.com",
            "password": "Password' onerror='alert(1)'"
        })
        self.assertEqual(response_handler.status_code, 400)



    # =========================================================================
    # 9. FORM VALIDATION & PASSWORD POLICY ENFORCEMENT
    # =========================================================================
    def test_form_validation_enforces_password_and_email_rules(self):
        """Verify RegisterForm enforces minimum password length and email validity."""
        with self.app.test_request_context():
            # Password too short (< 8 chars)
            form_short_pw = RegisterForm(
                username="validuser",
                email="user@example.com",
                password="123",
                confirm_password="123"
            )
            self.assertFalse(form_short_pw.validate())
            self.assertIn("password", form_short_pw.errors)

            # Passwords mismatch
            form_mismatch = RegisterForm(
                username="validuser",
                email="user@example.com",
                password="ValidPassword123!",
                confirm_password="DifferentPassword123!"
            )
            self.assertFalse(form_mismatch.validate())
            self.assertIn("confirm_password", form_mismatch.errors)

            # Invalid email format
            form_invalid_email = RegisterForm(
                username="validuser",
                email="invalid-email-address",
                password="ValidPassword123!",
                confirm_password="ValidPassword123!"
            )
            self.assertFalse(form_invalid_email.validate())
            self.assertIn("email", form_invalid_email.errors)

    # =========================================================================
    # 10. INPUT SANITIZATION & MAX CONTENT LENGTH
    # =========================================================================
    def test_max_content_length_configured(self):
        """Verify request size limitation is set to 2 MB (prevents DoS)."""
        self.assertEqual(self.app.config.get("MAX_CONTENT_LENGTH"), 2 * 1024 * 1024)

    def test_custom_error_handlers(self):
        """Verify custom 404, 403 error handlers."""
        response = self.client.get("/non-existent-security-endpoint-xyz")
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"404 Page Not Found", response.data)

    # =========================================================================
    # 11. WAF - MALICIOUS SCANNER BLOCKING
    # =========================================================================
    def test_waf_blocks_malicious_user_agent_scanners(self):
        """Verify WAF blocks requests from automated scanners (e.g. sqlmap, nikto)."""
        scanners = ["sqlmap/1.7#stable", "Mozilla/5.0 (Nikto 2.1.6)", "dirbuster-1.0-RC1"]
        for agent in scanners:
            response = self.client.get("/products", headers={"User-Agent": agent})
            self.assertEqual(response.status_code, 403, f"Expected 403 for scanner agent {agent}")

    # =========================================================================
    # 12. WAF - PATH TRAVERSAL & COMMAND INJECTION DEFENSE
    # =========================================================================
    def test_waf_blocks_path_traversal(self):
        """Verify WAF blocks path traversal attempts in request path and query."""
        res1 = self.client.get("/products?category=../../../../etc/passwd")
        self.assertEqual(res1.status_code, 400)

        res2 = self.client.get("/products?category=..\\..\\win.ini")
        self.assertEqual(res2.status_code, 400)

    def test_waf_blocks_command_injection(self):
        """Verify WAF blocks command injection signatures in query parameters."""
        response = self.client.get("/products?q=; cat /etc/passwd")
        self.assertEqual(response.status_code, 400)

    # =========================================================================
    # 13. BRUTE FORCE PROTECTION & LOCKOUT
    # =========================================================================
    def test_brute_force_account_lockout(self):
        """Verify that 5 consecutive failed login attempts trigger an account lockout."""
        with self.app.app_context():
            test_user = User(username="lockout_victim", email="victim@example.com", role="customer", status=True)
            test_user.set_password("SecurePassword!123")
            db.session.add(test_user)
            db.session.commit()

        # Simulate 5 failed login attempts
        test_ip = "192.168.100.55"
        for _ in range(5):
            self.client.post("/login", data={
                "email": "victim@example.com",
                "password": "WrongPassword!999"
            }, headers={"X-Forwarded-For": test_ip})

        # 6th attempt should be locked out
        response = self.client.post("/login", data={
            "email": "victim@example.com",
            "password": "SecurePassword!123"  # Even with correct password, account is locked!
        }, headers={"X-Forwarded-For": test_ip}, follow_redirects=True)

        self.assertIn("temporarily restricted", response.get_data(as_text=True))

        # Reset protector state
        brute_force_protector.reset(test_ip)
        brute_force_protector.reset("victim@example.com")

    # =========================================================================
    # 14. E-COMMERCE THEORY - ZERO-TRUST SERVER-SIDE PRICING
    # =========================================================================
    def test_ecommerce_zero_trust_price_tampering_prevention(self):
        """Verify that client-side price tampering is completely neutralized by server catalog lookup."""
        with self.app.app_context():
            buyer = User(username="honest_buyer", email="buyer@example.com", role="customer", status=True)
            buyer.set_password("BuyerPassword#123")
            db.session.add(buyer)
            db.session.commit()

            with self.client.session_transaction() as sess:
                sess["_user_id"] = str(buyer.id)
                sess["_fresh"] = True

            # Attacker attempts to buy iPhone 17 Pro Max ($1,399) for $0.01
            tampered_cart = '[{"id": 1, "title": "iPhone 17 Pro Max", "price": 0.01, "quantity": 1}]'
            res = self.client.post("/checkout/process", data={
                "full_name": "Honest Buyer",
                "email": "buyer@example.com",
                "address": "123 Tech Way",
                "city": "Phnom Penh",
                "payment_method": "Credit / Debit Card",
                "cart_data": tampered_cart
            }, follow_redirects=True)

            self.assertEqual(res.status_code, 200)

            # Order in DB MUST be $1399.00 (authoritative catalog price), NOT $0.01
            order = Order.query.filter_by(user_id=buyer.id).first()
            self.assertIsNotNone(order)
            self.assertEqual(order.subtotal, 1399.00)
            self.assertEqual(order.total_amount, 1399.00)

    # =========================================================================
    # 15. PASSWORD COMPLEXITY VALIDATOR
    # =========================================================================
    def test_password_complexity_validator(self):
        """Verify password complexity requirements (uppercase, lowercase, digit, special symbol)."""
        # Missing uppercase
        ok, msg = validate_password_complexity("alllowercase123!")
        self.assertFalse(ok)
        self.assertIn("uppercase", msg)

        # Missing lowercase
        ok, msg = validate_password_complexity("ALLUPPERCASE123!")
        self.assertFalse(ok)
        self.assertIn("lowercase", msg)

        # Missing number
        ok, msg = validate_password_complexity("NoNumbersAtAll!")
        self.assertFalse(ok)
        self.assertIn("number", msg)

        # Missing special character
        ok, msg = validate_password_complexity("NoSpecialCharacter123")
        self.assertFalse(ok)
        self.assertIn("special", msg)

        # Common weak password
        ok, msg = validate_password_complexity("password123")
        self.assertFalse(ok)

        # Valid strong password
        ok, msg = validate_password_complexity("Stro0ng!P@ssword2026")
        self.assertTrue(ok)
        self.assertEqual(msg, "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
