from django.urls import path
from . import views

app_name = 'conference'

urlpatterns = [
    path('', views.ConferenceLandingView.as_view(), name='landing'),
    path('speakers/', views.SpeakersView.as_view(), name='speakers'),
    path('abstract/submit/', views.AbstractSubmissionView.as_view(), name='abstract_submit'),
    path('abstract/submitted/', views.AbstractSuccessView.as_view(), name='abstract_success'),
    path('register/', views.RegistrationView.as_view(), name='register'),
    path('register/success/', views.RegistrationSuccessView.as_view(), name='registration_success'),
    path('payment/verify/<str:ticket_id>/', views.payment_verify, name='payment_verify'),
    path('ticket/<str:ticket_id>/', views.ticket_verify, name='ticket_verify'),
    path('programme/', views.ProgramView.as_view(), name='program'),
    path('api/category-fee/<int:category_id>/', views.category_fee_api, name='category_fee_api'),
    path('content/save/', views.save_content_block, name='save_content'),
]
