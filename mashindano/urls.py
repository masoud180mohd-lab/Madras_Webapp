from django.urls import path
from . import views

urlpatterns = [
    path('jaji/', views.dashbodi_jaji, name='dashbodi_jaji'),
    path('jaji/alama/<int:mshiriki_id>/', views.weka_alama, name='weka_alama'),
]