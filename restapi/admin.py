from django.contrib import admin
from django.contrib.auth.models import Permission
from . import models

from django import forms
from django.utils.html import format_html
from django.utils.safestring import mark_safe
import tldextract


class LastModifiedByMixin:
    """ Add this to an object that has a 'last_modified_by' datetime field, and it will be
    set to the currently logged user when saving """

    def save_model(self, request, obj, form, change):
        obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)


class SetOwnerMixin:
    """ Add this to an object that has an 'owner' field that is a fk to User, and it will be set
    to the currently logged user when creating it """

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            # Only set added_by during the first save.
            obj.owner = request.user
        super().save_model(request, obj, form, change)


class RatingInline(admin.TabularInline):
    model = models.Rating
    min_num = 0
    extra = 0  # determines number of empty elements for new objects
    readonly_fields = ["date"]
    # rating = forms.IntegerField(widget=forms.RadioSelect(choices=[-1, 1, 2, 3]))
    radio_fields = {"rating": admin.HORIZONTAL}


# custom forms to tweak how each field is displayed in the detail page
class NewsItemForm(forms.ModelForm):
    class Meta:
        model = models.NewsItem
        exclude = []

    body = forms.CharField(widget=forms.Textarea(attrs={"cols": 120, "rows": 3}))
    summary = forms.CharField(widget=forms.Textarea(attrs={"cols": 120, "rows": 10}))


@admin.register(models.NewsItem)
class NewsItemAdmin(admin.ModelAdmin):
    inlines = [RatingInline]
    exclude = ["ratings"]

    form = NewsItemForm

    # list view definition and helpers
    # -----------------------------------------------------------------------------------

    def make_discarded(modeladmin, request, queryset):
        queryset.update(publication_state=models.NewsItem.DISCARDED)

    make_discarded.short_description = "Mark as discarded"

    def make_approved(modeladmin, request, queryset):
        queryset.update(publication_state=models.NewsItem.APPROVED)

    make_approved.short_description = "Mark as approved"

    def sentiment_icon(self, obj):
        if obj.sentiment == "bad":
            return "👿"  # there's an emoji in there! angry devil - alternative: disapointed emoji= '😠'
        return obj.sentiment

    sentiment_icon.short_description = "🤖 "  # this is the title of the column

    def rating_count(self, obj):
        if obj.ratings and obj.ratings.count():
            return sum([r.rating for r in obj.ratings.all()])
        return 0

    rating_count.short_description = "Votes"

    def clickable_target_url(self, obj):
        domain = "Can't parse"
        try:
            extracted = tldextract.extract(obj.target_url)
            domain = f"{extracted.domain}.{extracted.suffix}"
        except:
            pass
        return format_html('<a href="{}">{}</a>', obj.target_url, domain,)

    clickable_target_url.short_description = "Link"

    def icon(self, obj):
        return format_html(
            '<a href="{}"><img src="{}"  width="32px" height="32px"/></a>',
            obj.target_url,
            obj.thumbnail
            if obj.thumbnail
            else "https://onlydognews.com/gfx/site/onlydognews-logo-main.png",
        )

    icon.short_description = "Thumb"

    actions = [make_approved, make_discarded]
    date_hierarchy = "date"
    ordering = ("date", "publication_state")
    list_display = (
        "icon",
        "title",
        "clickable_target_url",
        "date",
        "publication_state",
        "sentiment_icon",
        "rating_count",
        "user",
    )

    # class RatingCountFilter(admin.SimpleListFilter):
    #     title = 'rating'
    #     parameter_name = 'rating_count'
    #
    #     def lookups(self, request, model_admin):
    #         return (
    #             (0, 'Negative'),
    #             (1, 'No rating'),
    #             (2, 'Positive'),
    #             (3, 'Awesome'),
    #         )
    #
    #     def queryset(self, request, queryset):
    #         value = self.value()
    #         if value == 0:
    #             return queryset.filter(rating_count)
    #         elif value == 'No':
    #             return queryset.exclude(benevolence_factor__gt=75)
    #         return queryset

    list_filter = ("user", "source", "sentiment", "publication_state")
    list_display_links = ("date", "title")

    # detail view (uses NewsItemForm above)
    # -----------------------------------------------------------------------------------

    def thumbnail_preview(self, obj):
        return mark_safe(
            f'<a href="{obj.target_url}"><img src="{obj.thumbnail}" width="128px"/></a>'
        )

    def clickable_full_target_url(self, obj):
        return format_html('<a href="{}">{}</a>', obj.target_url, obj.target_url,)

    clickable_full_target_url.short_description = "Link"

    readonly_fields = [
        "date",
        "clickable_full_target_url",
        "thumbnail_preview",
        "clickable_target_url",
        "fetch_date",
    ]
    radio_fields = {"publication_state": admin.HORIZONTAL}

    fieldsets = (
        (
            "News Article",
            {
                "fields": (
                    "clickable_full_target_url",
                    "title",
                    "source",
                    "user",
                    "date",
                    "publication_state",
                    "body",
                    "thumbnail_preview",
                    "sentiment",
                ),
            },
        ),
        (
            "Fetched data",
            {
                "classes": ("collapse", "collapsed"),
                "fields": (
                    "fetch_date",
                    "thumbnail",
                    "image",
                    "type",
                    "summary",
                    "cached_page",
                ),
            },
        ),
    )
