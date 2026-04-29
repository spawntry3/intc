# IT College Almaty — Аналитика Соцсетей

Django-проект для мониторинга 2GIS и Instagram.

## Установка

```bash
pip install django
cd college_analytics
python manage.py migrate
python manage.py seed_data   
python manage.py runserver
```

Открыть: http://127.0.0.1:8000/

## Структура дашборда
- KPI карточки: рейтинг 2GIS, кол-во отзывов, подписчики IG, Engagement Rate
- График динамики отзывов по месяцам (Chart.js)
- Pie-чарт тональности отзывов
- Графики роста подписчиков и вовлечённости
- Таблица сравнения с конкурентами + bar charts
- Блок положительных и отрицательных отзывов
- Топ-6 публикаций Instagram
- Автогенерация рекомендаций по улучшению

## Подключение реальных данных
Файл `dashboard/data_seed.py` — замените mock-данные на результаты парсинга:
- 2GIS API / scrapy для отзывов
- Instagram Basic Display API или apify для постов
