# Reference: https://stackoverflow.com/a/34899874
from django import template

register = template.Library()


@register.inclusion_tag("news/custom_submit_line.html", takes_context=True)
def custom_submit_line(context):
    """
    Displays a row of custom action buttons
    """
    ctx = {
        "custom_actions": context.get("custom_actions", []),
    }
    if context["original"]:
        ctx["original"] = context["original"]
    return ctx

