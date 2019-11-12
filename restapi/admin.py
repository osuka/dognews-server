from django.contrib import admin

from .models import NewsItem, Rating


class RatingInline(admin.StackedInline):
    model = Rating
    min_num = 0
    extra = 0  # determines number of empty elements for new objects


@admin.register(NewsItem)
class NewsItemAdmin(admin.ModelAdmin):
    inlines = [
        RatingInline
    ]

