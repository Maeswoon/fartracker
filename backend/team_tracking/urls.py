from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("teams", views.TeamView.as_view(), name="teams"),
    path("teams/abbreviated", views.TeamAbbreviatedView.as_view(), name="team_abbreviated"),
    path("teams/<str:team_id>", views.TeamDetailedView.as_view(), name="team_details"),
    path("teams/<str:team_id>/status", views.TeamStatusView.as_view(), name="team_statuses"),
    path("teams/<str:team_id>/recovery/trajectory", views.update_team_recovery_trajectory, name="trajectory"),
    path("teams/<str:team_id>/recovery", views.RecoveryPieceView.as_view(), name="recovery_piece"),
    path("recovery", views.RecoveringTeamsAbbreviatedView.as_view(), name="recovery"),
    path('frequencies', views.get_frequency_information, name="frequencies"),
    path('teams/<str:team_id>/frequencies', views.update_team_frequencies, name="team_frequencies"),
    path('current-user', views.current_user, name='current_user'),
    path("site_status", views.SiteStatusView.as_view(), name="site_status")
]
