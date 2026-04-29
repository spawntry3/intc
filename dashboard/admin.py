from django.contrib import admin

from .models import (
    CollegeAnalyticsSettings,
    Competitor,
    InstagramPost,
    MonthlyStats,
    Review,
)


@admin.register(CollegeAnalyticsSettings)
class CollegeAnalyticsSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'instagram_followers', 'dashboard_year_label')

    def has_add_permission(self, request):
        return not CollegeAnalyticsSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('source', 'author', 'sentiment', 'rating', 'date', 'likes')
    list_filter = ('source', 'sentiment', 'date')
    search_fields = ('author', 'text')
    date_hierarchy = 'date'
    ordering = ('-date',)


@admin.register(InstagramPost)
class InstagramPostAdmin(admin.ModelAdmin):
    list_display = ('post_id', 'date', 'likes', 'comments', 'engagement_rate')
    search_fields = ('post_id', 'caption', 'hashtags')
    date_hierarchy = 'date'
    ordering = ('-date',)


@admin.register(Competitor)
class CompetitorAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'rating_2gis',
        'reviews_count',
        'positive_percent',
        'instagram_followers',
        'instagram_posts',
    )
    search_fields = ('name',)
    ordering = ('-rating_2gis',)


@admin.register(MonthlyStats)
class MonthlyStatsAdmin(admin.ModelAdmin):
    list_display = (
        'month',
        'year',
        'positive_reviews',
        'negative_reviews',
        'neutral_reviews',
        'instagram_followers',
        'avg_engagement',
    )
    list_filter = ('year',)
    ordering = ('year', 'month')


admin.site.site_header = 'Аналитика IT College Almaty'
admin.site.site_title = 'Админ-панель'
admin.site.index_title = 'Управление данными 2GIS и Instagram'
