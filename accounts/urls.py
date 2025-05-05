from django.urls import path, include
from . import views


urlpatterns=[
    path('register/', views.register,name="register" ),
    path('login/', views.login, name="login"),
    path('logout/', views.logout_view, name="logout"),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.dashboard, name="dashboard"),
    path('activate/<uidb64>/<token>/', views.activate, name="activate"),
    path('forgotPassword/', views.forgotPassword, name='forgotPassword'),
    path('ResetPassword/', views.Resetpassword, name='ResetPassword'),
    path('resetpassword_validate/<uidb64>/<token>/', views.resetpassword_validate, name="resetpassword_validate"),
]