from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("company/<str:symbol>/", views.company_detail, name="company_detail"),
    path("sector/<str:name>/", views.sector_view, name="sector_view"),
    path("compare/", views.compare, name="compare"),
    path("screener/", views.screener, name="screener"),
    path("powerbi/", views.powerbi_view, name="powerbi_view"),
]
