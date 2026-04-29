from django.db import models


class CollegeAnalyticsSettings(models.Model):

    instagram_url = models.URLField(
        'Instagram',
        default='https://www.instagram.com/it_college_almaty/?hl=ru',
    )
    gis_url = models.URLField(
        '2GIS (карточка / отзывы)',
        default='https://2gis.kz/almaty/search/%D0%B8%D0%BD%D0%BD%D0%BE%D0%B2%D0%B0%D1%86%D0%B8%D0%BE%D0%BD%D0%BD%D1%8B%D0%B9%20%D1%82%D0%B5%D1%85%D0%BD%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%B8%D0%B9%20%D0%BA%D0%BE%D0%BB%D0%BB%D0%B5%D0%B4%D0%B6/geo/9430047375184515/76.913463%2C43.238007/tab/reviews?m=76.914057%2C43.237709%2F18.21',
    )
    instagram_followers = models.PositiveIntegerField('Подписчики Instagram (для KPI)', default=4200)
    dashboard_year_label = models.CharField('Период на дашборде', max_length=50, default='2026 год')

    class Meta:
        verbose_name = 'Настройки аналитики колледжа'
        verbose_name_plural = 'Настройки аналитики колледжа'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                'instagram_url': 'https://www.instagram.com/it_college_almaty/?hl=ru',
                'gis_url': 'https://2gis.kz/almaty/search/%D0%B8%D0%BD%D0%BD%D0%BE%D0%B2%D0%B0%D1%86%D0%B8%D0%BE%D0%BD%D0%BD%D1%8B%D0%B9%20%D1%82%D0%B5%D1%85%D0%BD%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%B8%D0%B9%20%D0%BA%D0%BE%D0%BB%D0%BB%D0%B5%D0%B4%D0%B6/geo/9430047375184515/76.913463%2C43.238007/tab/reviews?m=76.914057%2C43.237709%2F18.21',
                'instagram_followers': 4200,
                'dashboard_year_label': '2026 год',
            },
        )
        return obj

    def __str__(self):
        return 'Настройки аналитики'


class Review(models.Model):
    SOURCE_CHOICES = [('2gis', '2GIS'), ('instagram', 'Instagram')]
    SENTIMENT_CHOICES = [('positive', 'Положительный'), ('negative', 'Отрицательный'), ('neutral', 'Нейтральный')]

    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    author = models.CharField(max_length=200)
    text = models.TextField()
    rating = models.FloatField(null=True, blank=True)
    sentiment = models.CharField(max_length=20, choices=SENTIMENT_CHOICES)
    date = models.DateField()
    likes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"[{self.source}] {self.author} - {self.sentiment}"


class InstagramPost(models.Model):
    post_id = models.CharField(max_length=100, unique=True)
    caption = models.TextField(blank=True)
    likes = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)
    date = models.DateField()
    image_url = models.URLField(blank=True)
    post_url = models.URLField(blank=True)
    hashtags = models.TextField(blank=True)
    engagement_rate = models.FloatField(default=0)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Post {self.post_id} - {self.date}"


class Competitor(models.Model):
    name = models.CharField(max_length=200)
    rating_2gis = models.FloatField(default=0)
    reviews_count = models.IntegerField(default=0)
    positive_percent = models.FloatField(default=0)
    instagram_followers = models.IntegerField(default=0)
    instagram_posts = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class MonthlyStats(models.Model):
    month = models.CharField(max_length=20)
    year = models.IntegerField()
    positive_reviews = models.IntegerField(default=0)
    negative_reviews = models.IntegerField(default=0)
    neutral_reviews = models.IntegerField(default=0)
    instagram_followers = models.IntegerField(default=0)
    avg_engagement = models.FloatField(default=0)

    class Meta:
        ordering = ['year', 'month']
        unique_together = ['month', 'year']

    def __str__(self):
        return f"{self.month} {self.year}"
