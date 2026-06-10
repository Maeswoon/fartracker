# Create your views here.
from typing import Dict, Optional, List
from datetime import datetime

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Count, Q
from .auth import IsAdmin, IsTeamMember, IsAdminOrTeamOwner
from rest_framework.response import Response
from rest_framework.views import APIView
import rest_framework.status as drf_status

from .serializers import TeamSerializer, SiteStatusSerializer, TeamStatusSerializer, TeamAbbreviatedSerializer, \
    TeamDetailedSerializer, TeamWriteSerializer, RecoveryPieceSerializer, TrajectorySerializer, VoteSerializer
from .models import SalvoSchedule, Team, TeamStatus, RecoveryPiece, SiteStatus, Trajectory, Vote, VoteBallot
from django.contrib.auth.models import User

@extend_schema(auth=[])
def index(request):
    """Health check endpoint."""
    return HttpResponse("Hello, world. You're at the polls index.")

@extend_schema(auth=[])
class TeamAbbreviatedView(APIView):
    """List all teams with name, identifier, and current status only."""
    throttle_classes = []

    def get(self, request) -> Response:
        """Return abbreviated team list."""
        teams = Team.objects.all()
        serializer = TeamAbbreviatedSerializer(teams, many=True)
        return Response(serializer.data)

class TeamDetailedView(APIView):
    """Retrieve or update a single team by identifier."""
    def get_permissions(self):
        return [AllowAny()] if self.request.method == 'GET' else [IsAdmin()]

    def get_throttles(self):
        if self.request.method == 'GET':
            return []
        return super().get_throttles()

    def get(self, request, team_id: str) -> Response:
        """Return full team details including fuel, bunker, pad, and target altitude."""
        team = Team.objects.filter(team_identifier=team_id).select_related('launch_rail', 'bunker').first()
        serializer = TeamDetailedSerializer(team)
        return Response(serializer.data)

    @extend_schema(auth=[{'cookieAuth': []}])
    def patch(self, request, team_id: str) -> Response:
        """Update team fields. Requires admin."""
        team = Team.objects.filter(team_identifier=team_id).first()
        if not team:
            return Response({'error': 'Team not found'}, status=drf_status.HTTP_404_NOT_FOUND)
        serializer = TeamWriteSerializer(team, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=drf_status.HTTP_400_BAD_REQUEST)

class TeamView(APIView):
    """List all teams or create a new team."""
    def get_permissions(self):
        return [AllowAny()] if self.request.method == 'GET' else [IsAdmin()]

    def get_throttles(self):
        if self.request.method == 'GET':
            return []
        return super().get_throttles()

    def get(self, request) -> Response:
        """Return all teams with status, category, engine type, and pad name."""
        teams = Team.objects.all()
        serializer = TeamSerializer(teams, many=True)
        return Response(serializer.data)

    @extend_schema(auth=[{'cookieAuth': []}])
    def post(self, request) -> Response:
        """Create a new team. Requires admin."""
        serializer = TeamWriteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=drf_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=drf_status.HTTP_400_BAD_REQUEST)

class TeamStatusView(APIView):
    """Get status history or post a new status for a team."""
    def get_permissions(self):
        return [AllowAny()] if self.request.method == 'GET' else [IsAdmin()]

    def get_throttles(self):
        if self.request.method == 'GET':
            return []
        return super().get_throttles()

    def get(self, request, team_id: str):
        """Return status history for a team, newest first."""
        team = Team.objects.filter(team_identifier=team_id).first()
        team_statuses = TeamStatus.objects.filter(team=team).order_by('-timestamp')
        serializer = TeamStatusSerializer(team_statuses, many=True, context={'team': team})
        return Response(serializer.data)

    @extend_schema(auth=[{'cookieAuth': []}])
    def post(self, request, team_id: str):
        """Post a new status. Requires admin. Body: {"status": "At rail", "pad_name": "Rail 3"}."""
        team = Team.objects.filter(team_identifier=team_id).first()
        latest_team_status = TeamStatus.objects.filter(team=team).order_by('-timestamp').first()
        if latest_team_status is not None:
            if latest_team_status.status == TeamStatus.TeamStatusChoice.AT_RAIL:
                pass
            if request.data.get('status') == TeamStatus.TeamStatusChoice.AT_RAIL:
                if latest_team_status.status is not TeamStatus.TeamStatusChoice.IN_SALVO:
                    pass
                else:
                    pass
        serializer = TeamStatusSerializer(data=request.data, context={'team': team})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=drf_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=drf_status.HTTP_400_BAD_REQUEST)

@extend_schema(auth=[])
class AllRecoveryPiecesView(APIView):
    """Return all recovery pieces and recovery paths."""
    throttle_classes = []

    def get(self, request) -> Response:
        """Return all recovery pieces with team info and recovery path coordinates."""
        pieces = RecoveryPiece.objects.select_related('team').all()
        pieces_data = RecoveryPieceSerializer(pieces, many=True).data

        teams_with_coords = Team.objects.exclude(recovery_coordinates__coords__isnull=True)
        paths = []
        for t in teams_with_coords:
            coords = (t.recovery_coordinates or {}).get('coords', [])
            if coords:
                paths.append({
                    'team_identifier': t.team_identifier,
                    'name': t.name,
                    'coords': coords,
                })

        return Response({
            'pieces': pieces_data,
            'paths': paths,
        })

class RecoveryPieceView(APIView):
    """List or add recovery pieces for a team."""
    def get_permissions(self):
        return [AllowAny()] if self.request.method == 'GET' else [IsAdmin()]

    def get_throttles(self):
        if self.request.method == 'GET':
            return []
        return super().get_throttles()

    def get(self, request, team_id) -> Response:
        """Return recovery pieces for a team."""
        team = Team.objects.filter(team_identifier=team_id).first()
        recovery_pieces = RecoveryPiece.objects.filter(team=team)
        serializer = RecoveryPieceSerializer(recovery_pieces, many=True)
        return Response(serializer.data)

    @extend_schema(auth=[{'cookieAuth': []}])
    def post(self, request, team_id) -> Response:
        """Add a recovery piece. Requires admin. Body: {"object_name": "...", "lat": 35.3, "lon": -117.8}."""
        team = Team.objects.filter(team_identifier=team_id).first()
        if not team:
            return Response({'error': 'Team not found'}, status=drf_status.HTTP_404_NOT_FOUND)
        data = {**request.data, 'team': team.pk}
        serializer = RecoveryPieceSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=drf_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=drf_status.HTTP_400_BAD_REQUEST)

@extend_schema(auth=[{'cookieAuth': []}])
@api_view(['DELETE', 'PATCH'])
@permission_classes([IsAdmin])
def delete_recovery_piece(request, team_id: str, piece_id: int):
    """Delete or update a recovery piece. Requires admin."""
    team = Team.objects.filter(team_identifier=team_id).first()
    if not team:
        return Response({'error': 'Team not found'}, status=drf_status.HTTP_404_NOT_FOUND)
    piece = RecoveryPiece.objects.filter(id=piece_id, team=team).first()
    if not piece:
        return Response({'error': 'Piece not found'}, status=drf_status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        piece.delete()
        return Response({"deleted": True})

    # PATCH — update fields
    if 'object_name' in request.data:
        piece.name = request.data['object_name']
    for field in ('lat', 'lon'):
        if field in request.data:
            setattr(piece, field, request.data[field])
    piece.save()
    serializer = RecoveryPieceSerializer(piece)
    return Response(serializer.data)

@extend_schema(auth=[{'cookieAuth': []}])
@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsAdmin])
def update_team_recovery_path(request, team_id: str):
    """Manage a team's recovery path. Requires admin.
    GET  — return the team's recovery path coords.
    POST — append a coordinate. Body: {"lat": 35.3, "lon": -117.8}.
    PUT  — replace all coords. Body: {"coords": [{"lat": ..., "lon": ...}, ...]}."""
    team = Team.objects.filter(team_identifier=team_id).first()
    if not team:
        return Response({'error': 'Team not found'}, status=drf_status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        coords = (team.recovery_coordinates or {}).get('coords', [])
        return Response({'coords': coords})

    if request.method == 'PUT':
        coords = request.data.get('coords')
        if coords is None:
            return Response({'error': 'coords is required'}, status=drf_status.HTTP_400_BAD_REQUEST)
        if not isinstance(coords, list):
            return Response({'error': 'coords must be a list'}, status=drf_status.HTTP_400_BAD_REQUEST)
        team.recovery_coordinates = {'coords': coords}
        team.save()
        return Response({'coords': coords})

    # POST — append
    lon = request.data.get('lon')
    lat = request.data.get('lat')
    if lon is None or lat is None:
        return Response({'error': 'lon and lat are required'}, status=drf_status.HTTP_400_BAD_REQUEST)
    try:
        lon = float(lon)
        lat = float(lat)
    except (ValueError, TypeError):
        return Response({'error': 'lon and lat must be numbers'}, status=drf_status.HTTP_400_BAD_REQUEST)
    timestamp = datetime.now().isoformat()
    if not isinstance(team.recovery_coordinates, dict):
        team.recovery_coordinates = {}
    team.recovery_coordinates.setdefault('coords', []).append({"lon": lon, "lat": lat, "timestamp": timestamp})
    team.save()
    return Response({'coords': team.recovery_coordinates.get('coords', [])})


@extend_schema(auth=[{'cookieAuth': []}])
@api_view(['DELETE'])
@permission_classes([IsAdmin])
def delete_recovery_path_point(request, team_id: str, index: int):
    """Delete a recovery path point by index. Requires admin."""
    team = Team.objects.filter(team_identifier=team_id).first()
    if not team:
        return Response({'error': 'Team not found'}, status=drf_status.HTTP_404_NOT_FOUND)
    coords = (team.recovery_coordinates or {}).get('coords', [])
    if index < 0 or index >= len(coords):
        return Response({'error': 'Index out of range'}, status=drf_status.HTTP_400_BAD_REQUEST)
    coords.pop(index)
    team.recovery_coordinates['coords'] = coords
    team.save()
    return Response({'coords': coords})

def get_pads(request):
    """Return pad statuses (not yet implemented)."""
    ...

class SiteStatusView(APIView):
    """Get or set the current site flag status (Green/Yellow/Red)."""
    def get_permissions(self):
        return [AllowAny()] if self.request.method == 'GET' else [IsAdmin()]

    def get_throttles(self):
        if self.request.method == 'GET':
            return []
        return super().get_throttles()

    def get(self, request) -> Response:
        """Return the current site status and timestamp."""
        latest_status = SiteStatus.objects.order_by('-timestamp').first()
        resp = SiteStatusSerializer(latest_status)
        return Response(resp.data)

    @extend_schema(auth=[{'cookieAuth': []}])
    def post(self, request) -> Response:
        """Set the site status. Requires admin. Body: {"status": "Green Flag"}."""
        serializer = SiteStatusSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=drf_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=drf_status.HTTP_400_BAD_REQUEST)

EXPECTED_FREQ_KEYS = {'avionics', 'gse', 'team_comms'}

@extend_schema(auth=[{'cookieAuth': []}])
@api_view(['PATCH'])
@permission_classes([IsAdmin])
def update_team_frequencies(request, team_id: str):
    """Update a team's GPS frequencies. Requires admin. Body: {"avionics": "433.5 MHz", "gse": "915.0 MHz", "team_comms": "462.5625 MHz"}."""
    team = Team.objects.filter(team_identifier=team_id).first()
    if not team:
        return Response({'error': 'Team not found'}, status=drf_status.HTTP_404_NOT_FOUND)
    sanitized = {}
    for key in EXPECTED_FREQ_KEYS:
        val = request.data.get(key)
        if val is not None:
            sanitized[key] = str(val)[:100]
    team.gps_frequencies = sanitized
    team.save()
    return Response(team.gps_frequencies)

@extend_schema(auth=[{'cookieAuth': []}])
@api_view(['GET'])
@permission_classes([IsAdmin])
@throttle_classes([])
def get_frequency_information(request) -> JsonResponse:
    """Return GPS frequencies for all teams. Requires admin."""
    teams = Team.objects.all().values('name', 'team_identifier', 'gps_frequencies')
    teams_json = list(teams)
    return JsonResponse(teams_json, safe=False)

@extend_schema(auth=[{'cookieAuth': []}])
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([])
def current_user(request):
    """Return the authenticated user's info and permission claims."""
    user = request.user
    token = request.auth
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_admin': bool(token and token.get('is_admin')),
        'is_team_member': bool(token and token.get('is_team_member')),
    })

@extend_schema(auth=[])
@api_view(['POST'])
def logout_view(request):
    """Clear authentication cookies."""
    response = Response({'detail': 'Logged out'})
    response.delete_cookie('access_token', path='/', samesite='Lax')
    response.delete_cookie('refresh_token', path='/', samesite='Lax')
    return response

def _broadcast_trajectory(trajectory):
    serializer = TrajectorySerializer(trajectory)
    async_to_sync(get_channel_layer().group_send)(
        'trajectories',
        {'type': 'trajectory_update', 'data': serializer.data},
    )

@extend_schema(auth=[])
class TrajectoryListView(APIView):
    """List all flight trajectories."""
    permission_classes = [AllowAny]
    throttle_classes = []

    def get(self, request) -> Response:
        """Return all trajectories with team info. Points are [lat, lon, altitude_agl_ft]."""
        trajectories = Trajectory.objects.select_related('team').all()
        serializer = TrajectorySerializer(trajectories, many=True)
        return Response(serializer.data)

class TrajectoryDetailView(APIView):
    """Get, replace, or append to a team's flight trajectory.

    Points are arrays of [latitude, longitude, altitude_agl_feet].
    PUT replaces the entire trajectory (max 10k points).
    POST appends points to the existing trajectory (total max 10k).
    GET is public; PUT and POST require admin or team ownership.
    """
    def get_permissions(self):
        return [AllowAny()] if self.request.method == 'GET' else [IsAdminOrTeamOwner()]

    def get_throttles(self):
        if self.request.method == 'GET':
            return []
        return super().get_throttles()

    def _get_team(self, team_id):
        team = Team.objects.filter(team_identifier=team_id).first()
        if not team:
            return None
        return team

    def _validate_points(self, data):
        pts = data.get('points')
        if not isinstance(pts, list) or any(not isinstance(p, list) or len(p) != 3 for p in pts):
            return None
        return pts

    def get(self, request, team_id: str) -> Response:
        """Return a single team's trajectory."""
        trajectory = Trajectory.objects.filter(team__team_identifier=team_id).select_related('team').first()
        if not trajectory:
            return Response({'error': 'Trajectory not found'}, status=drf_status.HTTP_404_NOT_FOUND)
        serializer = TrajectorySerializer(trajectory)
        return Response(serializer.data)

    @extend_schema(auth=[{'cookieAuth': []}])
    def put(self, request, team_id: str) -> Response:
        """Replace the entire trajectory. Body: {"points": [[lat, lon, alt], ...]}. Max 10k points."""
        team = self._get_team(team_id)
        if not team:
            return Response({'error': 'Team not found'}, status=drf_status.HTTP_404_NOT_FOUND)
        pts = self._validate_points(request.data)
        if pts is None:
            return Response({'error': 'points must be [[lat, lon, alt], ...]'}, status=drf_status.HTTP_400_BAD_REQUEST)
        if len(pts) > 10000:
            return Response({'error': 'Trajectory exceeds 10,000 point limit'}, status=drf_status.HTTP_400_BAD_REQUEST)
        trajectory, _ = Trajectory.objects.update_or_create(team=team, defaults={'points': pts})
        _broadcast_trajectory(trajectory)
        serializer = TrajectorySerializer(trajectory)
        return Response(serializer.data)

    @extend_schema(auth=[{'cookieAuth': []}])
    def post(self, request, team_id: str) -> Response:
        """Append points to the trajectory. Body: {"points": [[lat, lon, alt], ...]}. Total max 10k."""
        team = self._get_team(team_id)
        if not team:
            return Response({'error': 'Team not found'}, status=drf_status.HTTP_404_NOT_FOUND)
        pts = self._validate_points(request.data)
        if pts is None:
            return Response({'error': 'points must be [[lat, lon, alt], ...]'}, status=drf_status.HTTP_400_BAD_REQUEST)
        trajectory, _ = Trajectory.objects.get_or_create(team=team)
        if len(trajectory.points) + len(pts) > 10000:
            return Response({'error': 'Trajectory exceeds 10,000 point limit'}, status=drf_status.HTTP_400_BAD_REQUEST)
        trajectory.points.extend(pts)
        trajectory.save()
        _broadcast_trajectory(trajectory)
        serializer = TrajectorySerializer(trajectory)
        return Response(serializer.data)


DEFAULT_LANE_DEFINITIONS = [
    {'id': 'pending', 'label': 'Pending', 'short_label': 'Pending'},
    {'id': 'salvo', 'label': 'Salvo', 'short_label': 'In Salvo'},
    {'id': 'in-recovery', 'label': 'In Recovery', 'short_label': 'Recovering'},
    {'id': 'recovered', 'label': 'Recovered', 'short_label': 'Recovered'},
]


def _build_lanes_response(schedule: SalvoSchedule) -> dict:
    """Return raw schedule pieces so the frontend can assemble lanes
    using the same merge logic for both the Yjs WebSocket path and
    the REST polling path."""
    return {
        'lane_definitions': schedule.lane_definitions or DEFAULT_LANE_DEFINITIONS,
        'lane_teams': schedule.lane_teams if isinstance(schedule.lane_teams, dict) else {},
        'team_data': schedule.team_data if isinstance(schedule.team_data, dict) else {},
        'salvo_timer_started': schedule.salvo_timer_started.isoformat() if schedule.salvo_timer_started else None,
        'teams': [{
            'team_identifier': t.team_identifier,
            'name': t.name,
            'university': t.university,
            'category': t.category,
            'engine_type': t.get_engine_type_display(),
            'fill_to_fire': t.fill_to_fire,
            'hold_time': t.hold_time,
            'salvo_time': t.salvo_time,
        } for t in Team.objects.all()],
    }


class ScheduleView(APIView):
    throttle_classes = []

    def get(self, request) -> Response:
        schedule = SalvoSchedule.objects.first()
        if not schedule:
            return Response({
                'lane_definitions': DEFAULT_LANE_DEFINITIONS,
                'lane_teams': {},
                'team_data': {},
                'salvo_timer_started': None,
                'teams': [{
                    'team_identifier': t.team_identifier,
                    'name': t.name,
                    'university': t.university,
                    'category': t.category,
                    'engine_type': t.get_engine_type_display(),
                    'fill_to_fire': t.fill_to_fire,
                    'hold_time': t.hold_time,
                    'salvo_time': t.salvo_time,
                } for t in Team.objects.all()],
            })
        return Response(_build_lanes_response(schedule))

    def post(self, request) -> Response:
        self.permission_classes = [IsAdmin]
        self.check_permissions(request)
        schedule, _ = SalvoSchedule.objects.get_or_create(pk=1)
        if 'lane_definitions' in request.data:
            schedule.lane_definitions = request.data['lane_definitions']
        if 'lane_teams' in request.data:
            schedule.lane_teams = request.data['lane_teams']
        schedule.save()
        return Response(_build_lanes_response(schedule))


class ScheduleTimerView(APIView):
    throttle_classes = []

    def post(self, request) -> Response:
        self.permission_classes = [IsAdmin]
        self.check_permissions(request)
        schedule, _ = SalvoSchedule.objects.get_or_create(pk=1)
        action = request.data.get('action', '')
        if action == 'start':
            schedule.salvo_timer_started = timezone.now()
        elif action == 'clear':
            schedule.salvo_timer_started = None
        else:
            return Response({'error': 'Invalid action'}, status=400)
        schedule.save()
        return Response({
            'salvo_timer_started': schedule.salvo_timer_started.isoformat() if schedule.salvo_timer_started else None,
        })


def _broadcast_vote_update(vote):
    """Serialize a Vote and broadcast to the 'votes' channel group."""
    serializer = VoteSerializer(vote)
    async_to_sync(get_channel_layer().group_send)(
        'votes',
        {'type': 'vote_update', 'data': serializer.data},
    )


class VoteListCreateView(APIView):
    """List all votes or create a new vote. Requires authentication."""
    permission_classes = [IsAuthenticated]
    throttle_classes = []

    def get(self, request) -> Response:
        """Return all votes: active first, then by creation date."""
        active = request.query_params.get('active')
        if active == 'true':
            votes = Vote.objects.filter(is_active=True).order_by('-created_at')
        elif active == 'false':
            votes = Vote.objects.filter(is_active=False).order_by('-created_at')
        else:
            votes = Vote.objects.all().order_by('-is_active', '-created_at')
        serializer = VoteSerializer(votes, many=True)
        return Response(serializer.data)

    def post(self, request) -> Response:
        """Create a new vote. Body: {"title": "...", "duration_minutes": 10}."""
        title = request.data.get('title', '').strip()
        if not title:
            return Response({'error': 'title is required'}, status=drf_status.HTTP_400_BAD_REQUEST)
        is_admin = bool(request.auth and request.auth.get('is_admin'))
        duration = 10
        if is_admin:
            duration = int(request.data.get('duration_minutes', 10))
            if duration < 1:
                duration = 10
        eligible_ids = list(
            User.objects.filter(is_superuser=False).values_list('id', flat=True)
        )
        expires_at = timezone.now() + timezone.timedelta(minutes=duration)
        vote = Vote.objects.create(
            title=title,
            created_by=request.user,
            expires_at=expires_at,
            duration_minutes=duration,
            eligible_voters=eligible_ids,
        )
        _broadcast_vote_update(vote)
        serializer = VoteSerializer(vote)
        return Response(serializer.data, status=drf_status.HTTP_201_CREATED)


class VoteDetailView(APIView):
    """Retrieve a single vote by ID. Requires authentication."""
    permission_classes = [IsAuthenticated]
    throttle_classes = []

    def get(self, request, vote_id: int) -> Response:
        """Return a single vote with ballots."""
        try:
            vote = Vote.objects.get(id=vote_id)
        except Vote.DoesNotExist:
            return Response({'error': 'Vote not found'}, status=drf_status.HTTP_404_NOT_FOUND)
        serializer = VoteSerializer(vote)
        return Response(serializer.data)


class VoteBallotView(APIView):
    """Cast a ballot on a vote. Requires authentication."""
    permission_classes = [IsAuthenticated]
    throttle_classes = []

    def post(self, request, vote_id: int) -> Response:
        """Cast a ballot. Body: {"choice": true} for Yes, {"choice": false} for No."""
        try:
            vote = Vote.objects.get(id=vote_id)
        except Vote.DoesNotExist:
            return Response({'error': 'Vote not found'}, status=drf_status.HTTP_404_NOT_FOUND)

        if not vote.is_active:
            return Response({'error': 'Voting has closed'}, status=drf_status.HTTP_400_BAD_REQUEST)

        if timezone.now() >= vote.expires_at:
            vote.is_active = False
            vote.save()
            _broadcast_vote_update(vote)
            return Response({'error': 'Voting has expired'}, status=drf_status.HTTP_400_BAD_REQUEST)

        if VoteBallot.objects.filter(vote=vote, user=request.user).exists():
            return Response({'error': 'You have already voted'}, status=drf_status.HTTP_409_CONFLICT)

        choice = request.data.get('choice')
        if not isinstance(choice, bool):
            return Response({'error': 'choice must be a boolean'}, status=drf_status.HTTP_400_BAD_REQUEST)

        ballot = VoteBallot.objects.create(vote=vote, user=request.user, choice=choice)

        # Check if all eligible voters have voted
        eligible = vote.eligible_voters if isinstance(vote.eligible_voters, list) else []
        voted_ids = set(VoteBallot.objects.filter(vote=vote).values_list('user_id', flat=True))
        if all(uid in voted_ids for uid in eligible):
            vote.is_active = False
            vote.save()

        _broadcast_vote_update(vote)
        return Response(
            VoteSerializer(vote).data,
            status=drf_status.HTTP_201_CREATED,
        )
