from typing import List, Optional

from collections import namedtuple

from drf_yasg.inspectors import SwaggerAutoSchema as DrfYasgSwaggerAutoSchema
from rest_framework.permissions import OperandHolder, SingleOperandHolder

PermissionItem = namedtuple("PermissionItem", ["name", "doc_str"])


def _render_permission_item(item):
    return f"+ `{item.name}`: *{item.doc_str}*"


class SwaggerAutoSchema(DrfYasgSwaggerAutoSchema):
    """View inspector with some project-specific logic."""

    def get_summary_and_description(self):
        """Return summary and description extended with permission docs."""
        summary, description = super().get_summary_and_description()
        permissions_description = self._get_permissions_description()
        if permissions_description:
            description += permissions_description
        return summary, description

    def _handle_permission(self, permission_class) -> Optional[PermissionItem]:
        permission = None

        try:
            permission = PermissionItem(
                permission_class.__name__,
                permission_class.get_description(self.view),
            )
        except AttributeError:
            if permission_class.__doc__:
                permission = PermissionItem(
                    permission_class.__name__,
                    permission_class.__doc__.replace("\n", " ").strip(),
                )

        return permission

    def _gather_permissions(self) -> List[PermissionItem]:
        items = []

        for permission_class in getattr(self.view, "permission_classes", []):
            if isinstance(permission_class, OperandHolder):
                items.append(self._handle_permission(permission_class.op1_class))
                items.append(self._handle_permission(permission_class.op2_class))

            if isinstance(permission_class, SingleOperandHolder):
                items.append(self._handle_permission(permission_class.op1_class))

            items.append(self._handle_permission(permission_class))

        return [i for i in items if i]

    def _get_permissions_description(self):
        permission_items = self._gather_permissions()

        if permission_items:
            return "\n\n**Permissions:**\n" + "\n".join(
                _render_permission_item(item) for item in permission_items
            )
        else:
            return None