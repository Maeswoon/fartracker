from functools import lru_cache
from rest_framework import serializers
from .models import Team, LaunchRail, Bunker, SiteStatus, TeamStatus, RecoveryPiece, Trajectory

def _get_lane_of_team(team_identifier: str) -> str | None:
    """Return the short_label of the lane a team is in, defaulting to 'Pending'."""
    from .models import SalvoSchedule
    from .views import DEFAULT_LANE_DEFINITIONS

    schedule = SalvoSchedule.objects.first()
    lane_teams = schedule.lane_teams if schedule else {}
    if not isinstance(lane_teams, dict):
        lane_teams = {}
    lane_defs = schedule.lane_definitions if schedule else None
    lane_defs = lane_defs or DEFAULT_LANE_DEFINITIONS

    # Check if team is explicitly placed in a lane
    for lane_id, team_ids in lane_teams.items():
        if team_identifier in team_ids:
            for ld in lane_defs:
                if ld['id'] == lane_id:
                    return ld.get('short_label', ld['label'])
            return lane_id  # lane exists but not in definitions

    # Not in any lane — default to Pending
    for ld in lane_defs:
        if ld['id'] == 'pending':
            return ld.get('short_label', ld['label'])
    return 'Pending'

class BunkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bunker
        fields = ['name', 'location']

class LaunchRailSerializer(serializers.ModelSerializer):
    rail_type_display = serializers.CharField(source='get_rail_type_display', read_only=True)

    class Meta:
        model = LaunchRail
        fields = ['name', 'rail_type_display', 'location']

class VerboseChoiceField(serializers.ChoiceField):
    def to_internal_value(self, data):
        # Map verbose label to actual value
        for key, label in self.choices.items():
            if label == data or key == data:
                return key
        self.fail("invalid_choice", input=data)

    def to_representation(self, value):
        # Optionally return verbose name in response
        return self.choices.get(value, value)

class SiteStatusSerializer(serializers.ModelSerializer):
    status = VerboseChoiceField(SiteStatus.SiteStatusChoice.choices)

    class Meta:
        model = SiteStatus
        fields = ['status', 'timestamp']

class TeamAbbreviatedSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    class Meta:
        model = Team
        fields = ['name', 'team_identifier', 'status']

    def get_status(self, team):
        return _get_lane_of_team(team.team_identifier)

class TeamStatusSerializer(serializers.ModelSerializer):
    team_name = serializers.SerializerMethodField()
    status = VerboseChoiceField(TeamStatus.TeamStatusChoice.choices)

    class Meta:
        model = TeamStatus
        fields = ['status', 'team_name', 'timestamp', 'pad_name']
        read_only_fields = ['timestamp']

    def get_team_name(self, status):
        return self.context['team'].name

    def validate_team(self, team_id):
        try:
            return Team.objects.get(team_identifier=team_id)
        except Team.DoesNotExist:
            raise serializers.ValidationError(f"Team with identifier '{team_id}' does not exist.")

    def create(self, validated_data):
        team = self.context['team']
        status = TeamStatus.objects.create(team=team, **validated_data)
        return status

class RecoveringTeamsSerializer(serializers.Serializer):
    team_name = serializers.CharField()

    def to_representation(self, instance: Team):
        return {
            'team_name': instance.name

        }

class TeamDetailedSerializer(serializers.ModelSerializer):
    engine_type_display = serializers.CharField(source='get_engine_type_display', read_only=True)
    launch_rail = LaunchRailSerializer(read_only=True)
    bunker = BunkerSerializer(read_only=True)

    class Meta:
        model = Team
        fields = ['name', 'university', 'team_identifier', 'category', 'engine_type', 'fuel_oxidizer', 'gps_frequencies',
                  'engine_type_display', 'recovery_coordinates', 'launch_rail', 'bunker', 'target_altitude']

class TeamSerializer(serializers.ModelSerializer):
    engine_type_display = serializers.CharField(source='get_engine_type_display', read_only=True)
    status = serializers.SerializerMethodField()
    pad_name = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ['name', 'university', 'team_identifier', 'category', 'fuel_oxidizer',
                  'engine_type_display', 'status', 'pad_name', 'fill_to_fire', 'hold_time', 'salvo_time']

    def get_status(self, team):
        return _get_lane_of_team(team.team_identifier)

    def get_pad_name(self, team):
        return None  # pad_name was from TeamStatus, now unused

class TeamWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['name', 'university', 'team_identifier', 'category', 'engine_type', 'fuel_oxidizer', 'target_altitude', 'fill_to_fire', 'hold_time', 'salvo_time']

class RecoveryPieceSerializer(serializers.ModelSerializer):
    object_name = serializers.CharField(source='name', max_length=30)
    team_identifier = serializers.CharField(source='team.team_identifier', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)

    class Meta:
        model = RecoveryPiece
        fields = ['id', 'object_name', 'timestamp', 'team', 'lat', 'lon', 'team_identifier', 'team_name']
        read_only_fields = ['id', 'timestamp']

class TrajectorySerializer(serializers.ModelSerializer):
    team_identifier = serializers.CharField(source='team.team_identifier', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)

    class Meta:
        model = Trajectory
        fields = ['id', 'team_identifier', 'team_name', 'points', 'updated_at']
        read_only_fields = ['id', 'updated_at']

