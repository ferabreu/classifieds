---
description: 'Project-specific safety patterns: ACID file uploads and admin user protection'
applyTo: '**/*.py'
---

# Project-Specific Safety Patterns

## 📁 File Upload Pattern (CRITICAL - ACID-like Operations)

**ALWAYS follow this exact sequence for file uploads:**

```python
# 1. Save uploads to TEMP_DIR
temp_path = os.path.join(current_app.config['TEMP_DIR'], filename)
file.save(temp_path)

# 2. Create thumbnail in TEMP_DIR
thumbnail_path = os.path.join(current_app.config['TEMP_DIR'], thumbnail_name)
create_thumbnail(temp_path, thumbnail_path)

# 3. Commit to database
try:
    db.session.add(listing)
    db.session.commit()
except Exception as e:
    # Rollback and cleanup temp files
    db.session.rollback()
    os.remove(temp_path)
    os.remove(thumbnail_path)
    raise

# 4. Move files to final location (only after successful commit)
final_path = os.path.join(current_app.config['UPLOAD_DIR'], filename)
final_thumb = os.path.join(current_app.config['THUMBNAIL_DIR'], thumbnail_name)
shutil.move(temp_path, final_path)
shutil.move(thumbnail_path, final_thumb)
```

### Why This Pattern?
- ✅ Prevents orphaned files in `UPLOAD_DIR` if DB commit fails
- ✅ Prevents inconsistent DB state if file operations fail
- ✅ Allows atomic rollback of both DB and filesystem changes

### Critical Rules
- ❌ **NEVER** write uploaded files directly to `UPLOAD_DIR` before DB commit
- ✅ **ALWAYS** use `TEMP_DIR` for staging
- ✅ **ALWAYS** cleanup temp files on DB error
- ✅ **ALWAYS** move (not copy) files after successful commit

---

## 👤 Admin User Protection

**NEVER allow operations that remove the last admin user:**

```python
# ✅ CORRECT - Check before demotion/deletion
def admin_delete_user(user_id):
    user = db.get_or_404(User, user_id)
    
    if user.is_admin:
        # Count other admin users
        admin_count = db.session.execute(
            select(func.count(User.id)).where(User.is_admin == True)
        ).scalar()
        
        if admin_count <= 1:
            flash("Cannot delete the last admin user", "danger")
            return redirect(url_for('admin.users'))
    
    # Safe to proceed
    db.session.delete(user)
    db.session.commit()
```

### Admin Safety Rules
- ❌ **NEVER** allow deletion of the last admin
- ❌ **NEVER** allow demotion of the last admin to regular user
- ✅ **ALWAYS** count remaining admins before demotion/deletion
- ✅ Provide clear error message explaining why operation was blocked

### Reference Implementation
See `app/routes/admin.py` for complete examples:
- `admin_edit_user()` - prevents last admin demotion
- `admin_delete_user()` - prevents last admin deletion

---

## 🖼️ Thumbnail Generation

- Thumbnails are always JPEG (224x224, white background)
- Generated via `app/routes/utils.create_thumbnail(src, dst)`
- Stored in `static/uploads/thumbnails/`
- Filename stored in `ListingImage.thumbnail_filename`

```python
# Always generate thumbnails during upload
create_thumbnail(temp_path, thumbnail_path)
```

---

## 🔐 External Service Checks

**NEVER assume external services are configured:**

```python
# ✅ CORRECT - Check before using
if current_app.config.get('MAIL_SERVER'):
    send_email(user.email, reset_link)
else:
    flash(f"Password reset link: {reset_link}", "info")

# ✅ CORRECT - LDAP is optional
if current_app.config.get('LDAP_SERVER'):
    ldap_user = authenticate_with_ldap(email, password)
    if ldap_user:
        return ldap_user

# Fall back to local authentication
return check_local_password(email, password)
```

### Service Availability
- **MAIL_SERVER**: Optional - fallback to flash messages
- **LDAP_SERVER**: Optional - fallback to local auth
- **Check configuration** before using any external service

---

## 🗂️ Directory Configuration

**NEVER hardcode paths - use config:**

```python
# ✅ CORRECT
upload_path = os.path.join(current_app.config['UPLOAD_DIR'], filename)
temp_path = os.path.join(current_app.config['TEMP_DIR'], filename)
thumbnail_path = os.path.join(current_app.config['THUMBNAIL_DIR'], thumb_name)

# ❌ WRONG
upload_path = 'app/static/uploads/' + filename  # DO NOT HARDCODE
```

### Configuration Keys
- `UPLOAD_DIR` - Final destination for uploaded images
- `THUMBNAIL_DIR` - Final destination for thumbnails
- `TEMP_DIR` - Staging area for ACID-like operations
- Resolved to absolute paths in `app/__init__.py`

---

## 📋 Manual Testing Checklist

After changes to file upload or admin logic:

1. **File Upload Testing:**
   - Create listing with images → verify thumbnails generated
   - Edit listing, delete image → verify file cleanup
   - Delete listing with images → verify cleanup
   - Simulate DB error → verify temp files cleaned up

2. **Admin Safety Testing:**
   - Try to delete last admin user → should be blocked
   - Try to demote last admin user → should be blocked
   - Delete/demote admin when multiple exist → should work
   - Verify error messages are clear and helpful
