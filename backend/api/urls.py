from django.urls import path
from .views import UploadView, SummaryView, HistoryView, LoginView, ReportView, ClearHistoryView

urlpatterns = [
    path('upload/', UploadView.as_view()),
    path('summary/', SummaryView.as_view()),
    path('history/', HistoryView.as_view()),
    path('login/', LoginView.as_view()),
    path('report/', ReportView.as_view()),
    path('clear/', ClearHistoryView.as_view()),
]
