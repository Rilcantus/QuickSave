from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import FileResponse
import os


def service_worker(request):
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'sw.js')
    return FileResponse(open(sw_path, 'rb'), content_type='application/javascript')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('sw.js', service_worker, name='service_worker'),
    path('', account_views.landing, name='landing'),
    path('accounts/', include('accounts.urls')),
    path('games/', include('games.urls')),
    path('journal/', include('journal.urls')),
    path('', include('play_sessions.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)