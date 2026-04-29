from django.core.management.base import BaseCommand
from datetime import date, timedelta
import random
from dashboard.models import (
    CollegeAnalyticsSettings,
    Competitor,
    InstagramPost,
    MonthlyStats,
    Review,
)
from dashboard.data_seed import (
    POSITIVE_REVIEWS_2GIS,
    NEGATIVE_REVIEWS_2GIS,
    INSTAGRAM_POSTS,
    INSTAGRAM_REVIEWS,
    COMPETITORS,
    MONTHLY_DATA,
)


class Command(BaseCommand):
    help = 'Seed demo data'

    def handle(self, *args, **kwargs):
        Review.objects.all().delete()
        InstagramPost.objects.all().delete()
        Competitor.objects.all().delete()
        MonthlyStats.objects.all().delete()

        settings = CollegeAnalyticsSettings.load()
        settings.dashboard_year_label = '2026 год'
        settings.save()

        base_date = date(2026, 1, 1)
        for i, (author, text, rating) in enumerate(POSITIVE_REVIEWS_2GIS):
            Review.objects.create(source='2gis', author=author, text=text, rating=rating,
                sentiment='positive', date=base_date + timedelta(days=i*14), likes=random.randint(2,15))
        for i, (author, text, rating) in enumerate(NEGATIVE_REVIEWS_2GIS):
            Review.objects.create(source='2gis', author=author, text=text, rating=rating,
                sentiment='negative', date=base_date + timedelta(days=i*20+5), likes=random.randint(0,5))

        for i, (author, text, sentiment, rating) in enumerate(INSTAGRAM_REVIEWS):
            Review.objects.create(
                source='instagram',
                author=author,
                text=text,
                rating=rating,
                sentiment=sentiment,
                date=base_date + timedelta(days=i * 11 + 3),
                likes=random.randint(0, 120),
            )

        followers = 4200
        base_date2 = date(2026, 1, 15)
        for i, (pid, caption, likes, comments, img) in enumerate(INSTAGRAM_POSTS):
            eng = round((likes + comments) / followers * 100, 2)
            InstagramPost.objects.create(post_id=pid, caption=caption, likes=likes, comments=comments,
                date=base_date2 + timedelta(days=i*45), image_url=img,
                post_url=f"https://www.instagram.com/p/{pid}/",
                hashtags=' '.join([w for w in caption.split() if w.startswith('#')]),
                engagement_rate=eng)

        for name, rating, rev_count, pos_pct, foll, posts in COMPETITORS:
            Competitor.objects.create(name=name, rating_2gis=rating, reviews_count=rev_count,
                positive_percent=pos_pct, instagram_followers=foll, instagram_posts=posts)

        for month, year, pos, neg, neu, foll, eng in MONTHLY_DATA:
            MonthlyStats.objects.create(month=month, year=year, positive_reviews=pos,
                negative_reviews=neg, neutral_reviews=neu, instagram_followers=foll, avg_engagement=eng)

        self.stdout.write(self.style.SUCCESS('Data seeded!'))
