from django.contrib import admin

from .models import NewsItem, Rating
from django import forms
from django.utils.html import format_html

class RatingInline(admin.TabularInline):
    model = Rating
    min_num = 0
    extra = 0  # determines number of empty elements for new objects


# custom forms to tweak how each field is displayed in the detail page
class NewsItemForm(forms.ModelForm):
    class Meta:
        model = NewsItem
        exclude = []
    summary = forms.CharField(widget=forms.Textarea())

@admin.register(NewsItem)
class NewsItemAdmin(admin.ModelAdmin):
    inlines = [
        RatingInline
    ]
    exclude = [ 'ratings' ]

    form = NewsItemForm

    # list view definition and helpers

    def sentiment_icon(self, obj):
        if obj.sentiment == 'bad':
            return '😠'
        return obj.sentiment
    sentiment_icon.short_description = '😃' # this is the title of the column

    def ratings_compact(self, obj):
        if obj.ratings and obj.ratings.count():
            return ','.join([f'{r.rating}' for r in obj.ratings.all()])
        return ''
    ratings_compact.short_description = 'R'

    def clickable_target_url(self, obj):
        return format_html(
            '<a href="{}">{}</span>',
            obj.target_url,
            obj.target_url,
        )

    date_hierarchy = 'date'
    list_display = ('date', 'ratings_compact', 'submitter', 'source', 'sentiment_icon', 'title', 'clickable_target_url')

    list_filter = ('submitter', 'source', 'sentiment')

    # detail view (see NewsItemForm above)

    fieldsets = (
        ('News Article', {
            'classes': 'wide',
            'fields': ('target_url', 'title', 'source', 'submitter', 'date')
        }),
        ('Fetched data', {
            'classes': 'wide',
            'fields': ('fetch_date', 'image', 'type', 'body', 'cached_page', 'thumbnail', 'sentiment', 'summary'),
        }),
    )
