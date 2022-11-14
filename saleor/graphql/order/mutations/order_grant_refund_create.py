import graphene

from ....core.permissions import OrderPermissions
from ...core.mutations import BaseMutation
from ...core.scalars import Decimal
from ...core.types.common import Error
from ..enums import OrderGrantRefundCreateErrorCode
from ..types import Order, OrderGrantedRefund


class OrderGrantRefundCreateError(Error):
    code = OrderGrantRefundCreateErrorCode(description="The error code.", required=True)


class OrderGrantRefundCreateInput(graphene.InputObjectType):
    amount = Decimal(required=True, description="Amount of the granted refund.")
    reason = graphene.String(description="Reason of the granted refund.")


class OrderGrantRefundCreate(BaseMutation):
    order = graphene.Field(
        Order, description="Order which has assigned new grant refund."
    )
    granted_refund = graphene.Field(
        OrderGrantedRefund, description="Created granted refund."
    )

    class Arguments:
        id = graphene.ID(description="ID of the order.", required=True)
        input = OrderGrantRefundCreateInput(
            required=True,
            description="Fields required to create a granted refund for the order.",
        )

    class Meta:
        description = "Adds granted refund to the order."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderGrantRefundCreateError

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        order = cls.get_node_or_error(info, data["id"], only_type=Order)
        amount = data["input"]["amount"]
        reason = data["input"].get("reason", "")
        granted_refund = order.granted_refunds.create(
            amount_value=amount,
            currency=order.currency,
            reason=reason,
            user=info.context.user,
            app=info.context.app,
        )
        return cls(order=order, granted_refund=granted_refund)