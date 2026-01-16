---
description: 'Jinja2 template structure, macro usage, and data preparation patterns'
applyTo: '**/templates/**/*.html'
---

# Jinja2 Template Development Standards

## Template Structure Principles

- **Minimal logic in templates** - prepare data in view functions
- Use macros for reusable markup → store in `templates/macros/`
- 4-space indentation (matching Python style)
- Double quotes for HTML attributes
- Single quotes inside Jinja expressions

---

## Macro Usage Pattern

Import macros at the start of the block where needed:

```jinja
{# At top of file or start of block where needed #}
{% import 'macros/forms.html' as form_macros %}

{# Use with namespace #}
{{ form_macros.render_field(form.username) }}
```

### When to Create Macros
- Repeated markup patterns (forms, cards, buttons)
- Complex HTML structures used across multiple templates
- Store in `templates/macros/` directory
- Use namespaced imports to avoid naming conflicts

---

## Data Preparation (CRITICAL)

**Prepare ALL complex data in view functions, not in templates:**

```python
# ✅ GOOD - Prepare in view function
categories = build_category_tree()  # Returns structured dict
return render_template('page.html', categories=categories)

# ❌ BAD - Complex logic in template
# Don't make templates build nested structures, filter lists, or transform data
```

### What to Prepare in Views
- Nested data structures (category trees, navigation menus)
- Sorted/filtered lists
- Aggregated data (counts, totals)
- Conditional visibility logic
- URL generation for collections

---

## HTML & Jinja Quoting

### HTML Attributes
Use double quotes consistently:
```jinja
<a href="{{ url_for('foo', id=item.id) }}" class="btn btn-primary">
```

### Jinja Expressions
Use single quotes for string literals inside expressions:
```jinja
<div class="{% if active %}active{% else %}inactive{% endif %}">
{{ item.name|default('Unknown') }}
```

---

## Template Organization

### Block Structure
```jinja
{% extends "base.html" %}

{% block title %}Page Title{% endblock %}

{% block content %}
  {# Main content here #}
{% endblock %}

{% block scripts %}
  {# Page-specific JavaScript here #}
{% endblock %}
```

### Include Partials for Repeated Sections
```jinja
{% include 'partials/header.html' %}
```

---

## Safety & Escaping

- Templates auto-escape by default - this is GOOD
- Only use `|safe` when content is guaranteed safe (e.g., from trusted markdown processor)
- Never use `|safe` on user-generated content

```jinja
{# ✅ Safe - auto-escaped #}
{{ user.bio }}

{# ❌ Dangerous - only if content is trusted #}
{{ markdown_content|safe }}
```

---

## Common Patterns

### Iteration with Fallback
```jinja
{% for item in items %}
  <div>{{ item.name }}</div>
{% else %}
  <p>No items found.</p>
{% endfor %}
```

### Conditional Classes
```jinja
<div class="item {% if item.featured %}featured{% endif %}">
```

### URL Generation
```jinja
<a href="{{ url_for('listings.view', listing_id=listing.id) }}">
```

---

## Performance Considerations

- Avoid calling functions repeatedly in loops - prepare data in view
- Use `{% cache %}` for expensive template fragments (if Flask-Caching is configured)
- Keep template inheritance depth reasonable (max 2-3 levels)
