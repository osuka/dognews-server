"""
 Add extra parameters on submit
 Reference: https://stackoverflow.com/a/34899874
"""
from django import template

register = template.Library()


@register.inclusion_tag(
    "custom_admin_actions/custom_submit_line.html", takes_context=True
)
def custom_submit_line(context):
    """
    Displays a row of custom action buttons
    """
    ctx = {
        "custom_admin_actions": context.get("custom_admin_actions", []),
        "custom_admin_actions_prefix": context.get(
            "custom_admin_actions_prefix", "custom_admin_actions_"
        ),
    }
    if context["original"]:
        ctx["original"] = context["original"]
    return ctx
