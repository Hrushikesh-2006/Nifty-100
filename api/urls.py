from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CompanyViewSet, SectorViewSet, LeaderboardView, SearchView, ScreenerView, 
    CompareView, PowerBIDashboardView, LivePricingView, 
    RealtimeFinancialDataView, CompareWithRealtimeView, FetchRealtimeDataView
)

router = DefaultRouter()
router.register("companies", CompanyViewSet, basename="company")
router.register("sectors",   SectorViewSet,  basename="sector")

urlpatterns = [
    path("",                              include(router.urls)),
    path("leaderboard/",                  LeaderboardView.as_view(),           name="leaderboard"),
    path("search/",                       SearchView.as_view(),                name="search"),
    path("screener/",                     ScreenerView.as_view(),              name="screener"),
    path("compare/",                      CompareView.as_view(),               name="compare"),
    path("compare-realtime/",             CompareWithRealtimeView.as_view(),   name="compare_realtime"),
    path("powerbi/",                      PowerBIDashboardView.as_view(),      name="powerbi"),
    path("live-metrics/",                 LivePricingView.as_view(),           name="live_metrics"),
    path("realtime/<str:symbol>/",        RealtimeFinancialDataView.as_view(), name="realtime"),
    path("realtime/fetch/",               FetchRealtimeDataView.as_view(),     name="realtime_fetch"),
]

