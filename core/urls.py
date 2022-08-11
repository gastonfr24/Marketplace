from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from django.urls.conf import include
from .views import HomeView, UserProductListView, ProductUpdateView, ProductDetailView


urlpatterns = [
    path("admin/", admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('marketplace/', include('marketplace.urls', namespace= 'marketplace')),
    path('', HomeView.as_view(), name='home'),
    path('users/', include('accounts.urls', namespace='users')),
    path('my-products/', UserProductListView.as_view(), name='product-list'),
    path('product/<slug>/update/', ProductUpdateView.as_view(), name='product-update'),
    path('prodcut/<slug>/', ProductDetailView.as_view(), name='detail')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root= settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root= settings.STATIC_ROOT)