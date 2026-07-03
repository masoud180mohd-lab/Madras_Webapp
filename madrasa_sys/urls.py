from django.contrib import admin
from django.urls import path, include
from django.conf import settings # Tumeongeza hii
from django.conf.urls.static import static # Tumeongeza hii

urlpatterns = [
    path('admin/', admin.site.urls),
    path('madrasa/', include('usimamizi.urls')),
    path('mashindano/', include('mashindano.urls')),
]

# Tumeongeza mstari huu chini kuruhusu picha kuonekana
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)