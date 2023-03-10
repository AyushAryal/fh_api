from itertools import groupby
from django import forms


class ItemVariantChoiceIterator(forms.models.ModelChoiceIterator):
    def __iter__(self):
        queryset = self.queryset.select_related("item")
        groups = groupby(queryset, key=lambda x: x.item)
        for item, item_variants in groups:
            yield (
                (item.name),
                [
                    (item_variant.id, str(item_variant))
                    for item_variant in item_variants
                ],
            )


class ItemVariantChoiceField(forms.models.ModelChoiceField):
    iterator = ItemVariantChoiceIterator
