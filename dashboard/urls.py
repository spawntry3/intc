from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('otzyvy/', views.reviews_page, name='reviews'),
    path('instagram/', views.instagram_page, name='instagram'),
    path('konkurenty/', views.competitors_page, name='competitors'),
    path('rekomendacii/', views.recommendations_page, name='recommendations'),
    path('import/instagram-posts/', views.import_instagram_posts, name='import_instagram_posts'),
    path('import/reviews/2gis/', views.import_reviews_2gis, name='import_reviews_2gis'),
    path('import/reviews/instagram/', views.import_reviews_instagram, name='import_reviews_instagram'),
]
