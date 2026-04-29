import json
import re

from django.contrib import messages
from django.db.models import Avg, Count
from django.shortcuts import redirect, render

from .models import (
    CollegeAnalyticsSettings,
    Competitor,
    InstagramPost,
    MonthlyStats,
    Review,
)

from .forms import ImportInstagramPostsForm, ImportReviewsForm
from .import_utils import import_instagram_posts_csv, import_reviews_csv


def _short_label(text: str, max_len: int = 34) -> str:
    value = (text or "").strip()
    if len(value) <= max_len:
        return value
    cut = value[:max_len].rstrip()
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0].rstrip()
    return f"{cut}..."


def _dashboard_year_int() -> int:
    settings = CollegeAnalyticsSettings.load()
    m = re.search(r"(\d{4})", settings.dashboard_year_label or "")
    return int(m.group(1)) if m else 2024


def _chart_context():
    settings = CollegeAnalyticsSettings.load()
    year = _dashboard_year_int()

    month_labels = ["Янв", "Фев", "Мар", "Апр", "Май", "Июн", "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]
    months_labels = month_labels
    positive_data = [0] * 12
    negative_data = [0] * 12
    followers_data = [settings.instagram_followers] * 12
    engagement_data = [0] * 12

    reviews_year = Review.objects.filter(date__year=year)

    monthly_reviews = (
        reviews_year.values("date__month", "sentiment")
        .annotate(cnt=Count("id"))
        .order_by("date__month")
    )
    for item in monthly_reviews:
        month_idx = int(item["date__month"]) - 1
        if item["sentiment"] == "positive":
            positive_data[month_idx] = item["cnt"]
        elif item["sentiment"] == "negative":
            negative_data[month_idx] = item["cnt"]

    monthly_stats = MonthlyStats.objects.filter(year=year)
    month_to_idx = {label: i for i, label in enumerate(month_labels)}
    for s in monthly_stats:
        if s.month in month_to_idx:
            followers_data[month_to_idx[s.month]] = s.instagram_followers

    monthly_engagement = (
        InstagramPost.objects.filter(date__year=year)
        .values("date__month")
        .annotate(avg_eng=Avg("engagement_rate"))
    )
    for item in monthly_engagement:
        month_idx = int(item["date__month"]) - 1
        engagement_data[month_idx] = float(item["avg_eng"] or 0)

    sentiment_pos = reviews_year.filter(sentiment="positive").count()
    sentiment_neg = reviews_year.filter(sentiment="negative").count()
    sentiment_neu = reviews_year.filter(sentiment="neutral").count()

    competitors = list(Competitor.objects.all().values())
    comp_names = [_short_label(c['name']) for c in competitors]
    comp_ratings = [c['rating_2gis'] for c in competitors]
    comp_reviews = [c['reviews_count'] for c in competitors]
    comp_positive = [c['positive_percent'] for c in competitors]
    comp_followers = [c['instagram_followers'] for c in competitors]

    ig_pos = reviews_year.filter(source="instagram", sentiment="positive").count()
    ig_neg = reviews_year.filter(source="instagram", sentiment="negative").count()
    ig_neu = reviews_year.filter(source="instagram", sentiment="neutral").count()

    gis_pos = reviews_year.filter(source="2gis", sentiment="positive").count()
    gis_neg = reviews_year.filter(source="2gis", sentiment="negative").count()
    gis_neu = reviews_year.filter(source="2gis", sentiment="neutral").count()

    return {
        'months_labels': json.dumps(months_labels, ensure_ascii=False),
        'positive_data': json.dumps(positive_data),
        'negative_data': json.dumps(negative_data),
        'followers_data': json.dumps(followers_data),
        'engagement_data': json.dumps(engagement_data),
        'sentiment_data': json.dumps([sentiment_pos, sentiment_neg, sentiment_neu]),
        'comp_names': json.dumps(comp_names, ensure_ascii=False),
        'comp_ratings': json.dumps(comp_ratings),
        'comp_reviews': json.dumps(comp_reviews),
        'comp_positive': json.dumps(comp_positive),
        'comp_followers': json.dumps(comp_followers),
        'ig_sentiment_data': json.dumps([ig_pos, ig_neg, ig_neu]),
        'gis_sentiment_data': json.dumps([gis_pos, gis_neg, gis_neu]),
        'ig_sentiment_counts': {'positive': ig_pos, 'negative': ig_neg, 'neutral': ig_neu},
        'gis_sentiment_counts': {'positive': gis_pos, 'negative': gis_neg, 'neutral': gis_neu},
        'all_sentiment_counts': {'positive': sentiment_pos, 'negative': sentiment_neg, 'neutral': sentiment_neu},
    }


def generate_recommendations(avg_rating, pos, neg, total, eng, followers):
    recs = []
    pos_pct = pos / total * 100 if total else 0

    if avg_rating < 4.5:
        recs.append({
            'icon_variant': 'rating', 'platform': '2GIS', 'priority': 'high',
            'title': 'Повысить средний рейтинг',
            'desc': f'Текущий рейтинг {avg_rating:.1f}/5. Стимулируйте довольных студентов оставлять отзывы. Цель: 4.7+',
            'actions': [
                'Отправить email рассылку выпускникам с просьбой об отзыве',
                'Добавить QR-код на рейтинг в холле колледжа',
                'Проводить опросы удовлетворённости еженедельно',
            ],
        })
    if neg > 0:
        recs.append({
            'icon_variant': 'reply', 'platform': '2GIS', 'priority': 'high',
            'title': 'Отвечать на негативные отзывы',
            'desc': f'Найдено {neg} негативных отзывов без ответа. Быстрый ответ повышает доверие.',
            'actions': [
                'Назначить ответственного за мониторинг 2GIS',
                'Отвечать на отзывы в течение 24 часов',
                'Предлагать решение проблемы публично',
            ],
        })
    if pos_pct < 80:
        recs.append({
            'icon_variant': 'trend', 'platform': '2GIS', 'priority': 'medium',
            'title': 'Увеличить долю положительных отзывов',
            'desc': f'Текущий показатель: {pos_pct:.0f}%. Рекомендуемый минимум: 80%.',
            'actions': [
                'Улучшить качество обслуживания в административных вопросах',
                'Организовать регулярные встречи студентов с руководством',
                'Внедрить программу обратной связи',
            ],
        })

    if eng < 5.0:
        recs.append({
            'icon_variant': 'mobile', 'platform': 'Instagram', 'priority': 'medium',
            'title': 'Повысить вовлечённость аудитории',
            'desc': f'Средний Engagement Rate: {eng:.1f}%. Норма для колледжей: 5-8%.',
            'actions': [
                'Публиковать истории (Stories) каждый день',
                'Проводить розыгрыши и конкурсы',
                'Использовать опросы и вопросы в Stories',
            ],
        })
    recs.append({
        'icon_variant': 'video', 'platform': 'Instagram', 'priority': 'medium',
        'title': 'Запустить Reels контент',
        'desc': 'Видео-контент получает в 3x больше охвата. Показывайте жизнь студентов.',
        'actions': [
            'Снимать короткие видео (15-30 сек) о студенческой жизни',
            'Делать Reels с советами по программированию',
            'Показывать behind-the-scenes уроков и мероприятий',
        ],
    })
    recs.append({
        'icon_variant': 'partner', 'platform': 'Instagram', 'priority': 'low',
        'title': 'Развивать партнёрства с инфлюенсерами',
        'desc': 'Сотрудничество с IT-блогерами увеличит охват на 40-60%.',
        'actions': [
            'Найти 3-5 IT-блогеров из Алматы',
            'Предложить бесплатное обучение в обмен на упоминание',
            'Организовать совместные прямые эфиры',
        ],
    })
    return recs


def _base_ctx(active_page='dashboard'):
    settings = CollegeAnalyticsSettings.load()
    return {
        'active_page': active_page,
        'settings': settings,
        'gis_url': settings.gis_url,
        'instagram_url': settings.instagram_url,
    }


def dashboard(request):
    year = _dashboard_year_int()
    settings = CollegeAnalyticsSettings.load()
    charts = _chart_context()

    total_reviews_2gis = Review.objects.filter(source='2gis', date__year=year).count()
    positive_2gis = Review.objects.filter(source='2gis', sentiment='positive', date__year=year).count()
    negative_2gis = Review.objects.filter(source='2gis', sentiment='negative', date__year=year).count()
    avg_rating = Review.objects.filter(source='2gis', date__year=year).aggregate(a=Avg('rating'))['a'] or 0
    total_ig_posts = InstagramPost.objects.filter(date__year=year).count()
    avg_likes = InstagramPost.objects.filter(date__year=year).aggregate(a=Avg('likes'))['a'] or 0
    avg_engagement = InstagramPost.objects.filter(date__year=year).aggregate(a=Avg('engagement_rate'))['a'] or 0
    followers = settings.instagram_followers

    competitors_qs = Competitor.objects.all()
    top_posts = InstagramPost.objects.filter(date__year=year).order_by('-likes')[:6]
    recent_positive = Review.objects.filter(source='2gis', sentiment='positive', date__year=year).order_by('-date')[:5]
    recent_negative = Review.objects.filter(source='2gis', sentiment='negative', date__year=year).order_by('-date')[:5]
    recent_ig = Review.objects.filter(source='instagram', date__year=year).order_by('-date')[:8]

    recommendations = generate_recommendations(
        avg_rating, positive_2gis, negative_2gis, total_reviews_2gis,
        avg_engagement, followers,
    )

    ctx = {
        **_base_ctx('dashboard'),
        'total_reviews_2gis': total_reviews_2gis,
        'positive_2gis': positive_2gis,
        'negative_2gis': negative_2gis,
        'avg_rating': round(avg_rating, 1),
        'total_ig_posts': total_ig_posts,
        'avg_likes': round(avg_likes),
        'avg_engagement': round(avg_engagement, 2),
        'followers': followers,
        'positive_pct': round(positive_2gis / total_reviews_2gis * 100) if total_reviews_2gis else 0,
        'competitors': competitors_qs,
        'top_posts': top_posts,
        'recent_positive': recent_positive,
        'recent_negative': recent_negative,
        'recent_ig_reviews': recent_ig,
        'recommendations': recommendations,
        **charts,
    }
    return render(request, 'dashboard.html', ctx)


def reviews_page(request):
    reviews = Review.objects.all()
    ctx = {
        **_base_ctx('reviews'),
        'reviews_2gis': reviews.filter(source='2gis'),
        'reviews_ig': reviews.filter(source='instagram'),
        **_chart_context(),
    }
    return render(request, 'reviews.html', ctx)


def instagram_page(request):
    settings = CollegeAnalyticsSettings.load()
    followers = settings.instagram_followers
    charts = _chart_context()
    top_posts = InstagramPost.objects.order_by('-likes')
    avg_eng = InstagramPost.objects.aggregate(a=Avg('engagement_rate'))['a'] or 0

    ctx = {
        **_base_ctx('instagram'),
        'top_posts': top_posts,
        'recent_ig_reviews': Review.objects.filter(source='instagram').order_by('-date'),
        'avg_engagement': round(avg_eng, 2),
        'followers': followers,
        **charts,
    }
    return render(request, 'instagram.html', ctx)


def competitors_page(request):
    ctx = {
        **_base_ctx('competitors'),
        'competitors': Competitor.objects.all(),
        **_chart_context(),
    }
    return render(request, 'competitors.html', ctx)


def recommendations_page(request):
    year = _dashboard_year_int()
    settings = CollegeAnalyticsSettings.load()
    total_reviews_2gis = Review.objects.filter(source='2gis', date__year=year).count()
    positive_2gis = Review.objects.filter(source='2gis', sentiment='positive', date__year=year).count()
    negative_2gis = Review.objects.filter(source='2gis', sentiment='negative', date__year=year).count()
    avg_rating = Review.objects.filter(source='2gis', date__year=year).aggregate(a=Avg('rating'))['a'] or 0
    avg_engagement = InstagramPost.objects.filter(date__year=year).aggregate(a=Avg('engagement_rate'))['a'] or 0

    recommendations = generate_recommendations(
        avg_rating, positive_2gis, negative_2gis, total_reviews_2gis,
        avg_engagement, settings.instagram_followers,
    )
    ctx = {
        **_base_ctx('recommendations'),
        'recommendations': recommendations,
    }
    return render(request, 'recommendations.html', ctx)


def import_instagram_posts(request):
    if request.method == "POST":
        form = ImportInstagramPostsForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data["csv_file"]
            delimiter = form.cleaned_data["delimiter"]
            mode = form.cleaned_data["mode"]

            result = import_instagram_posts_csv(
                csv_bytes=csv_file.read(),
                mode=mode,
                delimiter_choice=delimiter,
            )
            messages.success(
                request,
                f"Импорт Instagram-постов завершён. Добавлено: {result.get('imported', 0)} · Обновлено: {result.get('updated', 0)}.",
            )
            return redirect("import_instagram_posts")
        messages.error(request, "Проверьте CSV: ошибка формы или формат файла.")
    else:
        form = ImportInstagramPostsForm()

    return render(
        request,
        "import_instagram_posts.html",
        {
            "form": form,
            **_base_ctx("dashboard"),
        },
    )


def import_reviews_2gis(request):
    if request.method == "POST":
        form = ImportReviewsForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data["csv_file"]
            delimiter = form.cleaned_data["delimiter"]
            mode = form.cleaned_data["mode"]

            try:
                result = import_reviews_csv(
                    csv_bytes=csv_file.read(),
                    source="2gis",
                    mode=mode,
                    delimiter_choice=delimiter,
                )
                messages.success(
                    request,
                    f"Импорт отзывов 2GIS завершён. Добавлено: {result.get('imported', 0)} · Пропущено: {result.get('skipped', 0)}.",
                )
                return redirect("import_reviews_2gis")
            except Exception as e:
                messages.error(request, f"Ошибка импорта: {e}")
        else:
            messages.error(request, "Проверьте CSV: ошибка формы или формат файла.")
    else:
        form = ImportReviewsForm()

    return render(
        request,
        "import_reviews.html",
        {
            "form": form,
            "source_label": "2GIS",
            **_base_ctx("dashboard"),
        },
    )


def import_reviews_instagram(request):
    if request.method == "POST":
        form = ImportReviewsForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data["csv_file"]
            delimiter = form.cleaned_data["delimiter"]
            mode = form.cleaned_data["mode"]

            try:
                result = import_reviews_csv(
                    csv_bytes=csv_file.read(),
                    source="instagram",
                    mode=mode,
                    delimiter_choice=delimiter,
                )
                messages.success(
                    request,
                    f"Импорт отзывов Instagram завершён. Добавлено: {result.get('imported', 0)} · Пропущено: {result.get('skipped', 0)}.",
                )
                return redirect("import_reviews_instagram")
            except Exception as e:
                messages.error(request, f"Ошибка импорта: {e}")
        else:
            messages.error(request, "Проверьте CSV: ошибка формы или формат файла.")
    else:
        form = ImportReviewsForm()

    return render(
        request,
        "import_reviews.html",
        {
            "form": form,
            "source_label": "Instagram",
            **_base_ctx("dashboard"),
        },
    )
