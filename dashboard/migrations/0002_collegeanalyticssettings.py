# Generated manually for CollegeAnalyticsSettings

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CollegeAnalyticsSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('instagram_url', models.URLField(default='https://www.instagram.com/it_college_almaty/?hl=ru', verbose_name='Instagram')),
                ('gis_url', models.URLField(default='https://2gis.kz/almaty/search/%D0%B8%D0%BD%D0%BD%D0%BE%D0%B2%D0%B0%D1%86%D0%B8%D0%BE%D0%BD%D0%BD%D1%8B%D0%B9%20%D1%82%D0%B5%D1%85%D0%BD%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%B8%D0%B9%20%D0%BA%D0%BE%D0%BB%D0%BB%D0%B5%D0%B4%D0%B6/geo/9430047375184515/76.913463%2C43.238007/tab/reviews?m=76.914057%2C43.237709%2F18.21', verbose_name='2GIS (карточка / отзывы)')),
                ('instagram_followers', models.PositiveIntegerField(default=4200, verbose_name='Подписчики Instagram (для KPI)')),
                ('dashboard_year_label', models.CharField(default='2024 год', max_length=50, verbose_name='Период на дашборде')),
            ],
            options={
                'verbose_name': 'Настройки аналитики колледжа',
                'verbose_name_plural': 'Настройки аналитики колледжа',
            },
        ),
    ]
