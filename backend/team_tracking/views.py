# Create your views here.
from typing import Dict, Optional, List
from datetime import datetime

from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
import rest_framework.status as drf_status

from .serializers import TeamSerializer, SiteStatusSerializer, TeamStatusSerializer, TeamAbbreviatedSerializer, \
    TeamDetailedSerializer, TeamWriteSerializer, RecoveryPieceSerializer
from .models import Team, TeamStatus, RecoveryPiece, SiteStatus


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


"""
Team CRUD
"""


class TeamAbbreviatedView(APIView):
    throttle_classes = []

    def get(self, request) -> Response:
        teams = Team.objects.all()
        serializer = TeamAbbreviatedSerializer(teams, many=True)
        return Response(serializer.data)


class TeamDetailedView(APIView):
    def get_permissions(self):
        return [AllowAny()] if self.request.method == 'GET' else [IsAuthenticated()]

    def get_throttles(self):
        if self.request.method == 'GET':
            return []
        return super().get_throttles()

    # Returns status, team info, recovery info, rail info, list of statuses
    def get(self, request, team_id: str) -> Response:
        team = Team.objects.filter(team_identifier=team_id).select_related('launch_rail', 'bunker').first()
        serializer = TeamDetailedSerializer(team)
        return Response(serializer.data)

    def patch(self, request, team_id: str) -> Response:
        team = Team.objects.filter(team_identifier=team_id).first()
        if not team:
            return Response({'error': 'Team not found'}, status=drf_status.HTTP_404_NOT_FOUND)
        serializer = TeamWriteSerializer(team, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=drf_status.HTTP_400_BAD_REQUEST)


class TeamView(APIView):
    def get_permissions(self):
        return [AllowAny()] if self.request.method == 'GET' else [IsAuthenticated()]

    def get_throttles(self):
        if self.request.method == 'GET':
            return []
        return super().get_throttles()

    def get(self, request) -> Response:
        teams = Team.objects.all()
        serializer = TeamSerializer(teams, many=True)
        return Response(serializer.data)

    def post(self, request) -> Response:
        serializer = TeamWriteSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=drf_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=drf_status.HTTP_400_BAD_REQUEST)



class TeamStatusView(APIView):
    def get_permissions(self):
        return [AllowAny()] if self.request.method == 'GET' else [IsAuthenticated()]

    def get_throttles(self):
        if self.request.method == 'GET':
            return []
        return super().get_throttles()

    def get(self, request, team_id: str):
        team = Team.objects.filter(team_identifier=team_id).first()
        team_statuses = TeamStatus.objects.filter(team=team).order_by('-timestamp')
        serializer = TeamStatusSerializer(team_statuses, many=True, context={'team': team})
        return Response(serializer.data)

    def post(self, request, team_id: str):
        """
        :param request: Request which should have team_identifier: str, status: str, rail_name: Optional[str]
        :param team_id: str as part of path
        :return: Response
        """
        team = Team.objects.filter(team_identifier=team_id).first()
        latest_team_status = TeamStatus.objects.filter(team=team).order_by('-timestamp').first()
        if latest_team_status is not None:
            if latest_team_status.status == TeamStatus.TeamStatusChoice.AT_RAIL:
                # Update the RailStatus for the given Launch Rail to "Free"
                pass
            if request.data.get('status') == TeamStatus.TeamStatusChoice.AT_RAIL:
                if latest_team_status.status is not TeamStatus.TeamStatusChoice.IN_SALVO:
                    # If they did not launch in their most recent launch attempt, increment their launch attempt counter
                    pass
                else:
                    # Otherwise, they just got on the rail. Update RailStatus to occupied and add Team
                    pass
        serializer = TeamStatusSerializer(data=request.data, context={'team': team})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=drf_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=drf_status.HTTP_400_BAD_REQUEST)


class AllRecoveryPiecesView(APIView):
    throttle_classes = []

    def get(self, request) -> Response:
        pieces = RecoveryPiece.objects.select_related('team').all()
        pieces_data = []
        for p in pieces:
            item = RecoveryPieceSerializer(p).data
            item['team_name'] = p.team.name
            item['team_identifier'] = p.team.team_identifier
            pieces_data.append(item)

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


"""
RecoveryPiece CRUD
"""

class RecoveryPieceView(APIView):
    def get_permissions(self):
        return [AllowAny()] if self.request.method == 'GET' else [IsAuthenticated()]

    def get_throttles(self):
        if self.request.method == 'GET':
            return []
        return super().get_throttles()

    def get(self, request, team_id) -> Response:
        team = Team.objects.filter(team_identifier=team_id).first()
        recovery_pieces = RecoveryPiece.objects.filter(team=team)
        serializer = RecoveryPieceSerializer(recovery_pieces, many=True)
        return Response(serializer.data)

    def post(self, request, team_id) -> Response:
        team = Team.objects.filter(team_identifier=team_id).first()
        if not team:
            return Response({'error': 'Team not found'}, status=drf_status.HTTP_404_NOT_FOUND)
        data = {**request.data, 'team': team.pk}
        serializer = RecoveryPieceSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=drf_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=drf_status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_recovery_piece(request, team_id: str, piece_id: int):
    team = Team.objects.filter(team_identifier=team_id).first()
    if not team:
        return Response({'error': 'Team not found'}, status=drf_status.HTTP_404_NOT_FOUND)
    deleted_count, _ = RecoveryPiece.objects.filter(id=piece_id, team=team).delete()
    if not deleted_count:
        return Response({'error': 'Piece not found'}, status=drf_status.HTTP_404_NOT_FOUND)
    return Response({"deleted": deleted_count})


# For when a team is telling you their position
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_team_recovery_path(request, team_id: str):
    team = Team.objects.filter(team_identifier=team_id).first()
    if not team:
        return Response({'error': 'Team not found'}, status=drf_status.HTTP_404_NOT_FOUND)
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
    serializer = TeamDetailedSerializer(team)
    return Response(serializer.data)

# Get the rails and their pad statuses. Which team is on there?
def get_pads(request):
    ...


class SiteStatusView(APIView):
    def get_permissions(self):
        return [AllowAny()] if self.request.method == 'GET' else [IsAuthenticated()]

    def get_throttles(self):
        if self.request.method == 'GET':
            return []
        return super().get_throttles()

    def get(self, request) -> Response:
        latest_status = SiteStatus.objects.order_by('-timestamp').first()
        resp = SiteStatusSerializer(latest_status)
        return Response(resp.data)

    def post(self, request) -> Response:
        serializer = SiteStatusSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=drf_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=drf_status.HTTP_400_BAD_REQUEST)


EXPECTED_FREQ_KEYS = {'avionics', 'gse', 'team_comms'}

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_team_frequencies(request, team_id: str):
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([])
def get_frequency_information(request) -> JsonResponse:
    teams = Team.objects.all().values('name', 'team_identifier', 'gps_frequencies')
    teams_json = list(teams)
    return JsonResponse(teams_json, safe=False)


# User Info
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@throttle_classes([])
def current_user(request):
    user = request.user
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
    })


@api_view(['POST'])
def logout_view(request):
    response = Response({'detail': 'Logged out'})
    response.delete_cookie('access_token', path='/api/', samesite='Lax')
    response.delete_cookie('refresh_token', path='/api/', samesite='Lax')
    return response

