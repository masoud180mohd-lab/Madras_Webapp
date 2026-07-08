from django.contrib import admin
from django.urls import path, include
from django.conf import settings 
from django.conf.urls.static import static 
from rest_framework.authtoken.views import obtain_auth_token
from django.http import HttpResponse 

# Hii ni kazi ndogo itakayojibu programu ya simu kuwa server ipo hai
def salamu_ya_api(request):
    return HttpResponse("Muunganisho umefanikiwa!", status=200)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('madrasa/', include('usimamizi.urls')),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path('', salamu_ya_api, name='home_ping'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)