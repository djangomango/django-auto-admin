# Django-Auto-Admin

A Django package providing mixin classes that automatically generate default Django admin options, search fields, list filters, list displays, and relationship links across models.

---

## Installation

```bash
pip install git+https://github.com/djangomango/django-auto-admin.git@0.1.0
```

Or add to your `requirements.txt`:

```txt
git+https://github.com/djangomango/django-auto-admin.git@0.1.0
```

Add `django_auto_admin` to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    ...
    "django_auto_admin",
    ...
]
```

---

## Usage

### 1. ModelAdmin Mixin

Inherit from `AutoModelAdminMixin` (or `AutoModelNoModuleAdminMixin` if hiding from admin index) on your `ModelAdmin` classes:

```python
from django.contrib import admin
from django_auto_admin.adminmixins import AutoModelAdminMixin
from .models import Order


@admin.register(Order)
class OrderAdmin(AutoModelAdminMixin, admin.ModelAdmin):
    pass
```

### 2. Auto-Registering All Models in an App

You can also dynamically register all models within an app config:

```python
from django.apps import apps
from django.contrib import admin
from django_auto_admin.adminmixins import AutoModelAdminMixin

app_config = apps.get_app_config("myapp")
app_config.model_imports()

for model in app_config.get_models():
    try:
        admin.site.register(model, AutoModelAdminMixin)
    except admin.sites.AlreadyRegistered:
        pass
```

---

## License & Credits

- Licensed under the **GNU Lesser General Public License v3 (LGPLv3)**.
- Relation links mixin inspired by [Gitaarik](https://github.com/Gitaarik).
