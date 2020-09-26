"""
Abstract ModelAdmin class that extends admin pages with a line of extra actions
provided by derived classes
"""
import abc
from django.contrib import admin
from django.contrib.admin.models import LogEntry, ContentType, CHANGE


class CustomActionsModelAdmin(admin.ModelAdmin):
    """A ModelAdmin that adds a row of custom actions to change pages"""

    __metaclass__ = abc.ABCMeta

    SUBMIT_ACTION_PREFIX = "custom_admin_action_"
    change_form_template = "custom_admin_actions/custom_change_form.html"

    @abc.abstractmethod
    def get_custom_admin_actions(  # pylint: disable=too-many-arguments
        self,
        request,
        context,
        add=False,
        change=False,
        form_url="",
        obj=None,
    ):
        """Return a dictionary of action_code:Description, eg "{ "reject":"Reject Submission" }" """

    @abc.abstractmethod
    def custom_action_called(self, request, custom_action_code, obj=None):
        """One of the buttons was pressed, custom_action_code contains the key, obj the instance if any.
        You can return None to proceed with the default action (go to the list page) or return an
        HttpResponse"""

    # overrides
    def render_change_form(  # pylint: disable=too-many-arguments
        self,
        request,
        context,
        add=False,
        change=False,
        form_url="",
        obj=None,
    ):
        custom_admin_actions = self.get_custom_admin_actions(
            request, context, add, change, form_url, obj
        )
        context.update(
            {
                "custom_admin_actions": custom_admin_actions,
                "custom_admin_actions_prefix": CustomActionsModelAdmin.SUBMIT_ACTION_PREFIX,
            }
        )
        return super().render_change_form(
            request,
            context,
            add=add,
            change=change,
            form_url=form_url,
            obj=obj,
        )

    # overrides
    def response_change(self, request, obj):
        for param in request.POST:
            if param.startswith(CustomActionsModelAdmin.SUBMIT_ACTION_PREFIX):
                action = param[len(CustomActionsModelAdmin.SUBMIT_ACTION_PREFIX) :]
                # link into the django admin history
                LogEntry.objects.log_action(
                    user_id=request.user.pk,
                    content_type_id=ContentType.objects.get_for_model(obj).pk,
                    object_id=obj.pk,
                    object_repr=str(obj),
                    action_flag=CHANGE,
                    change_message=action,
                )
                response = self.custom_action_called(request, action, obj)
                if response:
                    return response
        return super().response_change(request, obj)

    class Media:
        css = {"all": ("custom_admin_actions/css/custom_admin_actions.css",)}
