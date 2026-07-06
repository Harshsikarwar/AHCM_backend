from django.contrib import admin
from django.urls import path, include
from accounts import urls
from .views import StockPredictionAPIView, PatientFootfallAnalysisView, ResourceRedistributionView
urlpatterns = [
    path('stockprediction/',StockPredictionAPIView.as_view(), name="stock_prediction"),
    path('patientfootfall/<str:lang>/',PatientFootfallAnalysisView.as_view(), name="PatientFootfall"),
    path('resourceredistribution/<str:lang>/',ResourceRedistributionView.as_view(), name="resourceredistribution")
]