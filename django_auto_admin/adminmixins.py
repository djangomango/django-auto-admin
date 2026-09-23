from collections.abc import Iterator
from typing import Any

from django.contrib import admin
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.db.models import (
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    ForeignKey,
    IntegerField,
    PositiveIntegerField,
    PositiveSmallIntegerField,
    SmallIntegerField,
)
from django.shortcuts import resolve_url
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import SafeText


def parse_field_config(links_config: Any) -> Iterator[tuple[str, str]]:
    """Yield tuples of model field names and corresponding admin link field names."""
    for link in links_config:
        model_field_name = link
        admin_field_name = f"{link}_link"
        yield model_field_name, admin_field_name


def get_link_field(url: str, label: str) -> SafeText:
    """Return formatted HTML link for the admin change or changelist view."""
    return format_html('<a href="{}" class="changelink">{}</a>', url, label)


def get_obj_link_field(obj: Any, name: str) -> Any:
    """Return HTML link to the change view of the specified object instance."""
    url = resolve_url(admin_urlname(obj._meta, SafeText("change")), obj.pk)
    return get_link_field(url, name)


class AutoModelBaseAdminMixin(admin.ModelAdmin):
    """Admin mixin generating default list display, filters, and search from model fields."""

    def __init__(self, model: Any, admin_site: Any) -> None:
        self.list_display = ()
        self.list_filter = ()
        self.search_fields = ()
        self.readonly_fields = ()
        self.date_hierarchy = None

        self.set_list_display_fields(model)
        self.set_list_filter_fields(model)
        self.set_search_fields(model)
        self.set_date_hierarchy(model)

        super().__init__(model, admin_site)

    def set_list_display_fields(self, model: Any) -> None:
        """Populate list_display with eligible model fields."""
        max_fields = 10
        display_field_types = (
            DateField,
            DateTimeField,
            ForeignKey,
            BooleanField,
            CharField,
            IntegerField,
            PositiveIntegerField,
            PositiveSmallIntegerField,
            SmallIntegerField,
        )

        fields = [
            f.name for f in model._meta.fields if not f.one_to_many and not f.one_to_one
        ]
        for field in fields:
            if (not self.list_display and model._meta.pk.name != field) or (
                isinstance(model._meta.get_field(field), display_field_types)
                and len(self.list_display) < max_fields
            ):
                self.list_display += (field,)

    def set_list_filter_fields(self, model: Any) -> None:
        """Populate list_filter with eligible filterable fields."""
        max_fields = 10
        filter_field_types = (
            DateField,
            DateTimeField,
            ForeignKey,
            BooleanField,
        )

        fields = [
            f.name for f in model._meta.fields if not f.one_to_many and not f.one_to_one
        ]
        for field in fields:
            if (
                isinstance(model._meta.get_field(field), filter_field_types)
                and len(self.list_filter) < max_fields
            ):
                self.list_filter += (field,)

    def set_search_fields(self, model: Any) -> None:
        """Populate search_fields based on common searchable field names."""
        search_field_names = ["name", "slug", "title"]
        fields = [
            f.name for f in model._meta.fields if not f.one_to_many and not f.one_to_one
        ]
        self.search_fields = tuple(
            field for field in search_field_names if field in fields
        )

    def set_date_hierarchy(self, model: Any) -> None:
        """Configure date hierarchy navigation using common date fields."""
        date_hierarchy_field_names = [
            "joined_at",
            "updated_at",
            "created_at",
            "modified_at",
        ]
        fields = [
            f.name for f in model._meta.fields if not f.one_to_many and not f.one_to_one
        ]
        for field in date_hierarchy_field_names:
            if field in fields and not self.date_hierarchy:
                self.date_hierarchy = field

                if field in self.list_display:
                    self.list_display = (
                        *tuple(f for f in self.list_display if f != field),
                        field,
                    )


class AutoModelLinkAdminMixin(admin.ModelAdmin):
    """Admin mixin generating change and changelist links to related models."""

    def add_admin_field(self, field_name: str, func: Any) -> None:
        """Register a dynamic read-only method or attribute on the admin class."""
        if not hasattr(self, field_name):
            setattr(self, field_name, func)

        if field_name not in self.readonly_fields:
            self.readonly_fields += (field_name,)

    def add_change_link(self, model_field_name: str, admin_field_name: str) -> None:
        """Add a link to the change view of a related one-to-one model."""

        def make_change_link(model_field_name: str) -> Any:
            def func(instance: Any) -> Any:
                return self.get_change_link(
                    instance, model_field_name, admin_field_name
                )

            self.decorate_link_func(func, model_field_name)
            return func

        self.add_admin_field(admin_field_name, make_change_link(model_field_name))

    def get_change_link(
        self, instance: Any, model_field_name: str, admin_field_name: str
    ) -> Any:
        """Return HTML link to the related model change view."""
        try:
            target_instance = getattr(instance, model_field_name)
        except Exception:
            return

        return get_link_field(
            reverse(
                f"{self.admin_site.name}:{target_instance._meta.app_label}_{target_instance._meta.model_name}_change",
                args=[target_instance.pk],
            ),
            self.link_label(admin_field_name, target_instance),
        )

    def add_changelist_link(self, model_field_name: str, admin_field_name: str) -> None:
        """Add a link to the changelist view of related one-to-many models."""

        def make_changelist_link(model_field_name: str) -> Any:
            def func(instance: Any) -> Any:
                return self.get_changelist_link(instance, model_field_name)

            self.decorate_link_func(func, model_field_name)
            return func

        self.add_admin_field(admin_field_name, make_changelist_link(model_field_name))

    def get_changelist_link(self, instance: Any, model_field_name: str) -> Any:
        """Return HTML link to the changelist view filtered by instance."""
        try:
            target_instance = getattr(instance, model_field_name)
        except Exception:
            return

        if not target_instance.exists():
            return

        def get_url() -> str:
            app, model = self.get_app_model(instance, model_field_name)
            return reverse(f"{self.admin_site.name}:{app}_{model}_changelist")

        def get_lookup_filter() -> str:
            return instance._meta.get_field(model_field_name).field.name

        def get_label() -> str:
            return target_instance.model._meta.verbose_name_plural.capitalize()

        return get_link_field(
            f"{get_url()}?{get_lookup_filter()}={instance.pk}", get_label()
        )

    def get_app_model(self, instance: Any, model_field_name: str) -> tuple[str, str]:
        """Return the app label and model name for a related field."""
        model_meta = getattr(instance, model_field_name).model._meta
        app = model_meta.app_label
        model = model_meta.model_name

        return app, model

    def decorate_link_func(self, func: Any, model_field_name: str) -> None:
        """Configure short description and ordering on the link callable."""
        func.short_description = model_field_name.replace("_", " ").capitalize()

        try:
            field = self.model._meta.get_field(model_field_name)
        except Exception:
            pass
        else:
            if (
                hasattr(field.related_model._meta, "ordering")
                and len(field.related_model._meta.ordering) > 0
            ):
                ordering = field.related_model._meta.ordering[0].replace("-", "")
                func.admin_order_field = f"{field.name}__{ordering}"

    def link_label(self, admin_field_name: str, target_instance: Any) -> str:
        """Return display label for a related admin link target."""
        label_method_name = f"{admin_field_name}_label"
        if hasattr(self, label_method_name):
            return getattr(self, label_method_name)(target_instance)

        return str(target_instance)

    def __init__(self, model: Any, admin_site: Any) -> None:
        if not self.readonly_fields:
            self.readonly_fields = ()

        change_links = [
            f.name
            for f in model._meta.get_fields()
            if f not in model._meta.fields and f.one_to_one
        ]

        for model_field_name, admin_field_name in parse_field_config(change_links):
            self.add_change_link(model_field_name, admin_field_name)

        changelist_links = [
            f.name
            for f in model._meta.get_fields()
            if f not in model._meta.fields and f.one_to_many
        ]

        for model_field_name, admin_field_name in parse_field_config(changelist_links):
            self.add_changelist_link(model_field_name, admin_field_name)

        super().__init__(model, admin_site)


class AutoModelAdminMixin(
    AutoModelBaseAdminMixin, AutoModelLinkAdminMixin, admin.ModelAdmin
):
    """Admin mixin combining automatic fields and relation links."""

    pass


class NoModuleAdminMixin:
    """ModelAdmin mixin disabling admin module index view permissions."""

    @staticmethod
    def has_module_permission(request: Any, obj: Any = None) -> bool:
        """Deny module permission."""
        return False


class AutoModelNoModuleAdminMixin(
    AutoModelAdminMixin, NoModuleAdminMixin, admin.ModelAdmin
):
    """Admin mixin combining automatic fields and relation links with module hiding."""

    pass
