from django.contrib import admin

from .models import NewsItem, Rating
from django import forms
from django.utils.html import format_html
from django.utils.safestring import mark_safe

class RatingInline(admin.TabularInline):
    model = Rating
    min_num = 0
    extra = 0  # determines number of empty elements for new objects


# custom forms to tweak how each field is displayed in the detail page
class NewsItemForm(forms.ModelForm):
    class Meta:
        model = NewsItem
        exclude = []
    target_url = forms.CharField(widget=forms.TextInput(attrs={'size':120}))
    title = forms.CharField(widget=forms.Textarea(attrs={'cols':120, 'rows':2}))
    image = forms.CharField(widget=forms.TextInput(attrs={'size': 120}))

    body = forms.CharField(widget=forms.Textarea(attrs={'cols': 120, 'rows': 20}))
    cached_page = forms.CharField(widget=forms.TextInput(attrs={'size': 120}))
    thumbnail = forms.CharField(widget=forms.TextInput(attrs={'size': 120}))
    summary = forms.CharField(widget=forms.Textarea(attrs={'cols': 120, 'rows': 10}))


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
    sentiment_icon.short_description = '🤖 ' # this is the title of the column

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

    def publication_state_short(self, obj):
        return obj.publication_state
    publication_state_short.short_description = 'P'

    date_hierarchy = 'date'
    list_display = ('date', 'publication_state', 'sentiment_icon', 'ratings_compact', 'submitter', 'source', 'title',
                    'clickable_target_url')

    publication_state = forms.CharField()

    list_filter = ('submitter', 'source', 'sentiment')

    # detail view (see NewsItemForm above)

    def image_preview(self, obj):
        return mark_safe(f'<img src="{obj.image}" width="250px"/>')

    def thumbnail_preview(self, obj):
        return mark_safe(f'<img src="{obj.thumbnail}" width="128px"/>')

    readonly_fields = ['image_preview', 'thumbnail_preview']

    fieldsets = (
        ('News Article', {
            'classes': 'wide',
            'fields': ('target_url', 'title', 'source', 'submitter', 'date', 'thumbnail', 'thumbnail_preview' )
        }),
        ('Fetched data', {
            'classes': 'wide',
            'fields': ('fetch_date', 'image', 'image_preview', 'type', 'body', 'cached_page', 'sentiment', 'summary'),
        }),
    )
