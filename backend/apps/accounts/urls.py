from django.urls import path
from .views import CSRFTestView, CSRFTokenView, ResetPasswordView, RevokeSessionView, SessionsView, UserRegistrationView, LoginView, LogoutView, RefreshTokenView, LogoutAllView, MeView, ChangePasswordView, VerifyEmailView, ForgotPasswordView, ResendVerificationView


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
            "forgot-password/",
            ForgotPasswordView.as_view(),
            name="forgot-password"
        ),
    path(
        "reset-password/",
        ResetPasswordView.as_view(),
        name = "reset-password"
    ),
    path(
            "verify-email/",
            VerifyEmailView.as_view(),
            name="verify-email"
        ),
    path(
            "resend-verification/",
            ResendVerificationView.as_view(),
            name = "resend-verification"
        ),

     path("csrf/",CSRFTokenView.as_view(), name="csrf"),
     
    path(
        "csrf-test/",
        CSRFTestView.as_view(),
        name="csrf-test"
        ),

     path("sessions/",SessionsView.as_view(),    name="sessions",),
      path("sessions/<int:session_id>/", RevokeSessionView.as_view(),name="revoke-session",)
]