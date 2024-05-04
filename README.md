# Django-Auto-Admin

This package provides mixin class that automatically generates default admin options.

### Installation

1. Pip install or add to your requirements.txt:

    ```bash
    pip install git+https://github.com/djangomango/django-auto-admin.git@main
    ```

2. Add to INSTALLED_APPS:

    ```bash
    INSTALLED_APPS = [
        ...
        'django_auto_admin',
    ]
    ```

### Usage

Use the admin mixin as needed:

```python
from django_auto_admin.adminmixins import AutoModelBaseAdminMixin, AutoModelLinkAdminMixin

app_config = apps.get_app_config('app')

app_config.model_imports()

class AutoModelAdminMixin(AutoModelBaseAdminMixin, AutoModelLinkAdminMixin, admin.ModelAdmin):
    pass

models = app_config.get_models()
for model in models:
    try:
        admin.site.register(model, AutoModelAdminMixin)
    except admin.sites.AlreadyRegistered:
        pass
```
