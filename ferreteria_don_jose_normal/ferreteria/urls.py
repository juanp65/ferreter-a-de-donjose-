from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve


urlpatterns = [
    # Administración de Django
    path("admin/", admin.site.urls),

    # Rutas de la tienda
    path("", include("tienda.urls")),

    # Imágenes de productos guardadas en la carpeta media
    re_path(
        r"^media/(?P<path>.*)$",
        serve,
        {
            "document_root": settings.MEDIA_ROOT,
        },
    ),
]
