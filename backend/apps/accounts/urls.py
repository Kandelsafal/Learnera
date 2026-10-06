from django.urls import path
from .views import UserRegistrationView, LoginView, LogoutView, RefreshTokenView


urlpatterns = [
    path(
        "register/",
        UserRegistrationView.as_view(),
        name="user-register"
    ),
    path(
        "login/",
        LoginView.as_view(),
        name= "user-login"
        )
        ,
    path(
        "logout/",
        LogoutView.as_view(),
        name= "user-logout"
        ),

    path(
        "refresh/",
        RefreshTokenView.as_view(),
        name= "refresh"
        )
]