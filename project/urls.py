from django.contrib import admin
from django.urls import path

from flowers import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('catalog/', views.catalog, name='catalog'),
    path('flower/', views.flower_detail, name='flower_detail'),
    path('quiz/', views.quiz, name='quiz'),
    path('quiz-step/', views.quiz_step, name='quiz_step'),
    path('result/', views.result, name='result'),
    path('order/', views.order, name='order'),
    path('order-step/', views.order_step, name='order_step'),
    path('consultation/', views.consultation, name='consultation'),
    path('signup-consultation/', views.signup_consultation, name='signup_consultation'),
]
