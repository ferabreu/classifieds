# Security Review Recommendations (2025-06-23)

## 1. CSRF Protection
- All forms should continue to inherit from `FlaskForm` to ensure CSRF protection.
- If adding custom POST endpoints or APIs that do not use `FlaskForm`, implement explicit CSRF protection (e.g., via Flask-WTF CSRF decorators).

## 2. Authentication and Authorization
- Ensure all routes that mutate user data use `@login_required`.
- Admin actions must always require both `@login_required` and the custom `@admin_required` decorator, which checks `current_user.is_admin`.
- For user self-edit routes, always confirm `current_user.id == user.id` or `current_user.is_admin` before allowing edits.

## 3. Session Security
- Never use the default `SECRET_KEY='dev'` in production. Always set a strong, unpredictable secret via environment/config.
- Always deploy with HTTPS in production to protect session cookies and CSRF tokens.

## 4. Password Handling
- Continue to use secure password hashing (`generate_password_hash` / `check_password_hash` from Werkzeug).
- Never store or log plaintext passwords.

## 5. Password Reset
- Ensure reset tokens are always generated and verified with `itsdangerous`, signed with `SECRET_KEY`, and expire after a reasonable time (currently 1 hour).
- Ensure password reset only works for local users, not LDAP users.
- In development, if reset links are flashed to the UI for testing, be cautious with screen sharing or demos to prevent account hijacking.

## 6. User/Item Ownership Checks
- Always check that users can only edit/delete their own resources, unless they are admin.
- Maintain the logic that prevents removing the last admin user from the system.

## 7. Miscellaneous
- Maintain unique constraint on the email field in the User model.
- Continue to check for existing emails at registration.
- Confirm that LDAP users cannot use password reset or local password authentication flows.
- Avoid trusting user-supplied IDs for sensitive actions—always verify permissions server-side.

## 8. Additional Recommendations
- Regularly audit for any new POST endpoints to ensure they are covered by authentication, authorization, and CSRF protection.
- Double-check error messages in registration and password reset flows to avoid leaking information about which accounts exist (to prevent user enumeration).
- Consider adding unit and integration tests for all authentication, authorization, and CSRF flows.
- Always use secure cookies and set proper cookie flags (`Secure`, `HttpOnly`, `SameSite`) in production.

For a deeper or more up-to-date review, search the full codebase for `csrf`, `user`, `session`, and `form`.  
See: https://github.com/ferabreu/classifieds/search?q=csrf+OR+user+OR+session+OR+form