from django import forms
from django.contrib.admin import widgets as admin_widgets

from store.models import ItemVariant, Purchase, CartItem, WishlistItem
from administrator.fields import ItemVariantChoiceField


class BootstrapModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _, field in self.fields.items():
            form_class = {
                forms.widgets.CheckboxInput: "form-check-input",
                forms.widgets.RadioSelect: "form-check-input",
                forms.widgets.FileInput: "form-control",
                admin_widgets.AdminFileWidget: "form-control",
            }.get(field.widget.__class__, "")

            if form_class:
                if "class" in field.widget.attrs:
                    field.widget.attrs["class"] += " " + form_class
                else:
                    field.widget.attrs.update({"class": form_class})


class PurchaseInlineAdminForm(BootstrapModelForm):
    item_variant = ItemVariantChoiceField(ItemVariant.objects.all())

    class Meta:
        model = Purchase
        fields = "__all__"


class CartItemInlineAdminForm(BootstrapModelForm):
    item_variant = ItemVariantChoiceField(ItemVariant.objects.all())

    class Meta:
        model = CartItem
        fields = "__all__"


class WishlistItemInlineAdminForm(BootstrapModelForm):
    item_variant = ItemVariantChoiceField(ItemVariant.objects.all())

    class Meta:
        model = WishlistItem
        fields = "__all__"
