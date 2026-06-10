from django.db import models
from django.utils.translation import gettext_lazy as _

"""
Bunker information
"""

class Bunker(models.Model):
    name = models.TextField()
    location = models.JSONField(default=list)

"""
Rail information
"""

class LaunchRail(models.Model):  # Named "Pad" in the LC model
    class RailType(models.TextChoices):
        FIFTY_FOOT_1515 = '50-foot 1515'
        TWENTY_FOOT_1515 = '20-foot 1515'
        TEN_FOOT_1010 = '10-foot 1010'
        TEN_FOOT_1515 = '10-foot 1515'
        AULEY = 'Auley'
        MICROCOSM = 'Microcosm'
        NEWMAN = 'Newman'
        BAXTER = 'Baxter'
        SELF = 'Own Rail'

    name = models.CharField(max_length=200)
    rail_type = models.CharField(
        max_length=15,
        choices=RailType.choices
    )
    location = models.JSONField(default=list)

    def __str__(self):
        return self.name

class RailStatus(models.Model):  # Named "PadStatus" in the LC model
    class RailStatusChoice(models.TextChoices):
        IN_USE = 'IU', _('In Use')
        FREE = 'FR', _('Free')

    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=2,
        choices=RailStatusChoice.choices,
    )
    launch_rail = models.ForeignKey(LaunchRail, on_delete=models.CASCADE)

"""
Team information
"""

class Team(models.Model):
    class EngineType(models.TextChoices):
        HYBRID = 'H', _('Hybrid')
        LIQUID = 'L', _('Liquid')

    class Category(models.TextChoices):
        CATEGORY_A = 'A', _('Category A')
        CATEGORY_B = 'B', _('Category B')
        CATEGORY_C = 'C', _('Category C')
        CATEGORY_EX = 'E', _('Category Ex')

    # Naming information
    name = models.CharField(max_length=200)
    university = models.CharField(max_length=200)
    team_identifier = models.CharField(max_length=10)
    bunker = models.ForeignKey(Bunker, on_delete=models.CASCADE, related_name='teams', blank=True, null=True)

    category = models.CharField(
        max_length=1,
        choices=Category.choices
    )

    engine_type = models.CharField(
        max_length=1,
        choices=EngineType.choices
    )

    fuel_oxidizer = models.TextField(blank=True, null=True)

    target_altitude = models.IntegerField(blank=True, null=True)

    fill_to_fire = models.FloatField(default=0.0, help_text='Fill-to-fire time in minutes')
    hold_time = models.FloatField(default=0.0, help_text='Hold time in minutes')
    salvo_time = models.IntegerField(default=0, help_text='Assigned time-slot index (0=0min, 1=2min, …)')

    # Other information
    gps_frequencies = models.JSONField(default=list, blank=True, null=True)
    recovery_coordinates = models.JSONField(default=list, blank=True, null=True)
    launch_rail = models.ForeignKey(LaunchRail, on_delete=models.CASCADE, related_name='teams', blank=True, null=True)

    def __str__(self):
        return self.name

class TeamStatus(models.Model):
    class TeamStatusChoice(models.TextChoices):
        ABSENT = 'AS', _('Absent')
        ON_SITE = 'OS', _('Onsite')
        AT_RAIL = 'AR', _('At rail')
        IN_SALVO = 'IS', _('In salvo')
        IN_RECOVERY = 'IR', _('In recovery')
        RECOVERED = 'RD', _('Recovered')
    timestamp = models.DateTimeField(auto_now_add=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='statuses')
    status = models.CharField(
        max_length=2,
        choices=TeamStatusChoice.choices,
    )
    pad_name = models.CharField(max_length=100, blank=True, null=True)

"""
Recovery
"""

class RecoveryPiece(models.Model):
    name = models.CharField(max_length=30)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    lon = models.DecimalField(max_digits=10, decimal_places=6)
    lat = models.DecimalField(max_digits=10, decimal_places=6)

    def __str__(self):
        return self.name

class Trajectory(models.Model):
    team = models.OneToOneField(Team, on_delete=models.CASCADE, related_name='trajectory')
    points = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Trajectory for {self.team.name}'

class SiteStatus(models.Model):
    class SiteStatusChoice(models.TextChoices):
        GREEN = 'G', _('Green Flag')
        YELLOW = 'Y', _('Yellow Flag')
        RED = 'R', _('Red Flag')
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=1, choices=SiteStatusChoice.choices)


class SalvoSchedule(models.Model):
    lane_definitions = models.JSONField(default=list)
    lane_teams = models.JSONField(default=dict)
    team_data = models.JSONField(default=dict)
    salvo_timer_started = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Salvo Schedule (updated {self.updated_at.isoformat()})"


class ScheduleChangeLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    team_identifier = models.CharField(max_length=10)
    data = models.JSONField(default=dict)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Change for {self.team_identifier} at {self.timestamp.isoformat()}"


class Vote(models.Model):
    title = models.CharField(max_length=300)
    created_by = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='votes')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    duration_minutes = models.PositiveSmallIntegerField(default=10)
    is_active = models.BooleanField(default=True)
    eligible_voters = models.JSONField(default=list)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Vote: {self.title} (active={self.is_active})"


class VoteBallot(models.Model):
    vote = models.ForeignKey(Vote, on_delete=models.CASCADE, related_name='ballots')
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='ballots')
    choice = models.BooleanField()
    cast_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['vote', 'user'], name='unique_ballot_per_vote'),
        ]

    def __str__(self):
        return f"Ballot by {self.user.username} on {self.vote.title}"
