import graphene
from django.db.models import Exists, OuterRef, Q

from ....attribute import models as models
from ....product import models as product_models
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_310
from ...core.mutations import ModelDeleteMutation, ModelWithExtRefMutation
from ...core.types import AttributeError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Attribute, AttributeValue
from ..utils import check_permissions_for_attribute


class AttributeValueDelete(ModelDeleteMutation, ModelWithExtRefMutation):
    attribute = graphene.Field(Attribute, description="The updated attribute.")

    class Arguments:
        id = graphene.ID(required=False, description="ID of a value to delete.")
        external_reference = graphene.String(
            required=False,
            description=f"External ID of a value to delete. {ADDED_IN_310}",
        )

    class Meta:
        auto_permission_message = False
        model = models.AttributeValue
        object_type = AttributeValue
        description = (
            "Deletes a value of an attribute.\n\n"
            "Depending on the attribute type, it requires different permissions to delete:\n"
            "`PRODUCT_TYPE` requires `MANAGE_PRODUCTS` or `MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES` permissions,\n"
            "`PAGE_TYPE` requires `MANAGE_PAGES` or `MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES` permissions.\n"
            "DEPRECATED: it will be changed in 3.15."
        )
        error_type_class = AttributeError
        error_type_field = "attribute_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, external_reference=None, id=None
    ):
        instance = cls.get_instance(info, external_reference=external_reference, id=id)
        check_permissions_for_attribute(info.context, instance.attribute)
        product_ids = cls.get_product_ids_to_update(instance)
        response = super().perform_mutation(
            _root, info, external_reference=external_reference, id=id
        )
        product_models.Product.objects.filter(id__in=product_ids).update(
            search_index_dirty=True
        )
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.attribute_value_deleted, instance)
        cls.call_event(manager.attribute_updated, instance.attribute)
        return response

    @classmethod
    def get_product_ids_to_update(cls, instance):
        variants = product_models.ProductVariant.objects.filter(
            Exists(instance.variantassignments.filter(variant_id=OuterRef("id")))
        )
        product_ids = product_models.Product.objects.filter(
            Q(Exists(instance.productassignments.filter(product_id=OuterRef("id"))))
            | Q(Exists(variants.filter(product_id=OuterRef("id"))))
        ).values_list("id", flat=True)
        return list(product_ids)

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.attribute = instance.attribute
        return response
