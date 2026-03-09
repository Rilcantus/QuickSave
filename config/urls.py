from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import FileResponse
from django.views.generic import TemplateView
from accounts import views as account_views
import os


def service_worker(request):
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'sw.js')
    return FileResponse(open(sw_path, 'rb'), content_type='application/javascript')


admin.site.site_header = 'QuickSave Admin'
admin.site.site_title = 'QuickSave'
admin.site.index_title = 'Disrat Studios — QuickSave'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('sw.js', service_worker, name='service_worker'),
    path('', account_views.landing, name='landing'),
    path('accounts/', include('accounts.urls')),
    path('games/', include('games.urls')),
    path('journal/', include('journal.urls')),
    path('', include('play_sessions.urls')),

    # Legal pages
    path('legal/privacy/', TemplateView.as_view(template_name='legal/privacy.html'), name='privacy_policy'),
    path('legal/terms/', TemplateView.as_view(template_name='legal/terms.html'), name='terms_of_service'),
    path('legal/dmca/', TemplateView.as_view(template_name='legal/dmca.html'), name='dmca_policy'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)