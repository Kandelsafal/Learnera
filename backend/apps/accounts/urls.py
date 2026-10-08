from django.urls import path
from .views import UserRegistrationView, LoginView, LogoutView, RefreshTokenView, LogoutAllView, MeView, ChangePasswordView, VerifyEmailView


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
            "logout-all/",
            LogoutAllView.as_view(),
            name= "user-logout-all-sessions"
            ),

    path(
        "refresh/",
        RefreshTokenView.as_view(),
        name= "refresh"
        ),

    path(
            "me/",
            MeView.as_view(),
            name= "me"
            ),
    path(
                "change-password/",
                ChangePasswordView.as_view(),
                name= "change-password"
                ),

        path(
        "verify-email/",
        VerifyEmailView.as_view(),
        name="verify-email"
    ),
    
]