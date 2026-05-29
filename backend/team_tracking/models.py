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

class SiteStatus(models.Model):
    class SiteStatusChoice(models.TextChoices):
        GREEN = 'G', _('Green Flag')
        YELLOW = 'Y', _('Yellow Flag')
        RED = 'R', _('Red Flag')
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=1, choices=SiteStatusChoice.choices)
