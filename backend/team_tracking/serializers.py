from rest_framework import serializers

from .models import Team, LaunchRail, Bunker, SiteStatus, TeamStatus, RecoveryPiece


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
        status = TeamStatus.objects.filter(team=team).order_by('-timestamp').first()
        return status.status if status else None


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
                  'engine_type_display', 'status', 'pad_name']

    def get_status(self, team):
        status = TeamStatus.objects.filter(team=team).order_by('-timestamp').first()
        if not status:
            return None
        status_serializer = TeamStatusSerializer(status, context={'team': team})
        return status_serializer.data['status']

    def get_pad_name(self, team):
        status = TeamStatus.objects.filter(team=team).order_by('-timestamp').first()
        return status.pad_name if status else None

class TeamWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['name', 'university', 'team_identifier', 'category', 'engine_type', 'fuel_oxidizer', 'target_altitude']


class RecoveryPieceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecoveryPiece
        fields = ['name', 'timestamp', 'team', 'lat', 'lon']

