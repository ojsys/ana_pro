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
    path('payment/verification/', views.payment_verification, name='payment_verification'),
    path('payment/verification/login/<str:token>/', views.payment_verification_login, name='payment_verification_login'),
    path('payment/verification/logout/', views.payment_verification_logout, name='payment_verification_logout'),
    path('ticket/<str:ticket_id>/', views.ticket_verify, name='ticket_verify'),
    path('programme/', views.ProgramView.as_view(), name='program'),
    path('exhibitors/', views.ExhibitorsView.as_view(), name='exhibitors'),
    path('exhibitors/register/', views.ExhibitorRegistrationView.as_view(), name='exhibitor_register'),
    path('exhibitors/register/success/', views.ExhibitorRegistrationSuccessView.as_view(), name='exhibitor_register_success'),
    path('exhibitors/payment/verify/<uuid:token>/', views.exhibitor_payment_verify, name='exhibitor_payment_verify'),
    path('exhibitors/showcase/<uuid:token>/', views.ExhibitorShowcaseView.as_view(), name='exhibitor_showcase'),
    path('exhibitors/showcase/<uuid:token>/delete/<int:pk>/', views.exhibitor_showcase_delete, name='exhibitor_showcase_delete'),
    path('api/category-fee/<int:category_id>/', views.category_fee_api, name='category_fee_api'),
    path('content/save/', views.save_content_block, name='save_content'),
]
