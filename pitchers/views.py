from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Pitcher, FavoritePitcher
from .serializers import UserSerializer, PitcherSerializer, FavoritePitcherSerializer
import logging
from rest_framework.views import APIView
import json

logger = logging.getLogger(__name__)

def log_request(request, view_name):
    """Helper function to log request details"""
    logger.info(f"=== {view_name} Request ===")
    logger.info(f"Method: {request.method}")
    logger.info(f"Path: {request.path}")
    logger.info(f"User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
    logger.info(f"Headers: {dict(request.headers)}")
    if request.data:
        logger.info(f"Body: {json.dumps(request.data, indent=2)}")
    if request.query_params:
        logger.info(f"Query Params: {dict(request.query_params)}")

def log_response(response, view_name):
    """Helper function to log response details"""
    logger.info(f"=== {view_name} Response ===")
    logger.info(f"Status: {response.status_code}")
    if hasattr(response, 'data'):
        logger.info(f"Response Data: {json.dumps(response.data, indent=2)}")

# Create your views here.

class UserInfoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        log_request(request, "UserInfoView")
        try:
            user = request.user
            response_data = {
                'user_id': user.id,
                'username': user.username,
                'email': user.email
            }
            response = Response(response_data)
            log_response(response, "UserInfoView")
            return response
        except Exception as e:
            logger.error(f"Error retrieving user info: {str(e)}", exc_info=True)
            response = Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            log_response(response, "UserInfoView")
            return response

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        log_request(request, "UserViewSet.create")
        try:
            logger.info(f"Attempting to create user with data: {request.data}")
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                logger.info(f"Successfully created user: {user.username}")
                response = Response({
                    'user': UserSerializer(user, context=self.get_serializer_context()).data,
                    'message': 'User Created Successfully'
                }, status=status.HTTP_201_CREATED)
                log_response(response, "UserViewSet.create")
                return response
            logger.error(f"Validation errors: {serializer.errors}")
            response = Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            log_response(response, "UserViewSet.create")
            return response
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}", exc_info=True)
            response = Response({
                'error': str(e),
                'detail': 'An error occurred while creating the user'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            log_response(response, "UserViewSet.create")
            return response

class PitcherViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Pitcher.objects.all()
    serializer_class = PitcherSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        log_request(request, "PitcherViewSet.list")
        response = super().list(request, *args, **kwargs)
        log_response(response, "PitcherViewSet.list")
        return response

    def retrieve(self, request, *args, **kwargs):
        log_request(request, "PitcherViewSet.retrieve")
        response = super().retrieve(request, *args, **kwargs)
        log_response(response, "PitcherViewSet.retrieve")
        return response

class FavoritePitcherViewSet(viewsets.ModelViewSet):
    serializer_class = FavoritePitcherSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        username = self.request.query_params.get('username')
        if username:
            try:
                user = User.objects.get(username=username)
                return FavoritePitcher.objects.filter(user=user)
            except User.DoesNotExist:
                return FavoritePitcher.objects.none()
        return FavoritePitcher.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        log_request(self.request, "FavoritePitcherViewSet.perform_create")
        try:
            username = self.request.query_params.get('username')
            if username:
                try:
                    user = User.objects.get(username=username)
                    serializer.save(user=user)
                except User.DoesNotExist:
                    raise serializers.ValidationError({'username': 'User not found'})
            else:
                serializer.save(user=self.request.user)
            logger.info("Successfully created favorite")
        except Exception as e:
            logger.error(f"Error creating favorite: {str(e)}", exc_info=True)
            raise

    @action(detail=False, methods=['post'])
    def save_favorites(self, request):
        log_request(request, "FavoritePitcherViewSet.save_favorites")
        try:
            username = request.query_params.get('username')
            logger.info(f"Processing request for username: {username}")
            
            if not username:
                response = Response(
                    {'detail': 'username parameter is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                log_response(response, "FavoritePitcherViewSet.save_favorites")
                return response

            try:
                user = User.objects.get(username=username)
                logger.info(f"Found user: {user.username} (ID: {user.id})")
            except User.DoesNotExist:
                logger.error(f"User not found: {username}")
                response = Response(
                    {'detail': f'User {username} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
                log_response(response, "FavoritePitcherViewSet.save_favorites")
                return response

            pitcher_names = request.data.get('pitcher_names', [])
            logger.info(f"Received pitcher names: {pitcher_names}")
            
            # Clear existing favorites
            deleted_count = FavoritePitcher.objects.filter(user=user).delete()
            logger.info(f"Cleared existing favorites. Deleted count: {deleted_count}")

            # If pitcher_names is null or empty, just return empty response
            if not pitcher_names:
                logger.info("No pitcher names provided, returning empty favorites list")
                response = Response({
                    'favorites': [],
                    'count': 0
                }, status=status.HTTP_200_OK)
                log_response(response, "FavoritePitcherViewSet.save_favorites")
                return response

            # Create new favorites
            saved_favorites = []
            for name in pitcher_names:
                try:
                    logger.info(f"Processing pitcher: {name}")
                    # Try to get existing pitcher or create new one with default values
                    pitcher, created = Pitcher.objects.get_or_create(
                        player_name=name,
                        defaults={
                            'player_name': name,
                            'player_image': 'https://example.com/default.jpg',
                            'team_name': 'Unknown Team',
                            'team_logo': 'https://example.com/default_logo.jpg',
                            'stand_side': 'R',
                            'pitch_type': 'FB',
                            'velocity_range': '90-95',
                            'usage_rate': '0%',
                            'zone_rate': '0%',
                            'avg_spin_rate': 0.0,
                            'avg_horz_break': 0.0,
                            'avg_induced_vert_break': 0.0,
                            'arm_angle': 0.0,
                            'throws': 'R',
                            'heatmap_path': '/default/heatmap.png'
                        }
                    )
                    if created:
                        logger.info(f"Created new pitcher record for {name} (ID: {pitcher.id})")
                    else:
                        logger.info(f"Found existing pitcher record for {name} (ID: {pitcher.id})")
                    
                    favorite = FavoritePitcher.objects.create(
                        user=user,
                        pitcher=pitcher
                    )
                    logger.info(f"Created favorite record (ID: {favorite.id}) for {pitcher.player_name}")
                    
                    saved_favorites.append({
                        'pitcher_name': pitcher.player_name
                    })
                except Exception as e:
                    logger.error(f"Error creating favorite for {name}: {str(e)}", exc_info=True)
                    continue

            logger.info(f"Successfully saved {len(saved_favorites)} favorites")
            response = Response({
                'favorites': saved_favorites,
                'count': len(saved_favorites)
            }, status=status.HTTP_200_OK)
            log_response(response, "FavoritePitcherViewSet.save_favorites")
            return response

        except Exception as e:
            logger.error(f"Error saving favorites: {str(e)}", exc_info=True)
            response = Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            log_response(response, "FavoritePitcherViewSet.save_favorites")
            return response

    @action(detail=False, methods=['get'])
    def my_favorites(self, request):
        log_request(request, "FavoritePitcherViewSet.my_favorites")
        try:
            username = request.query_params.get('username')
            if not username:
                response = Response(
                    {'detail': 'username parameter is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                log_response(response, "FavoritePitcherViewSet.my_favorites")
                return response

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                response = Response(
                    {'detail': f'User {username} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
                log_response(response, "FavoritePitcherViewSet.my_favorites")
                return response

            favorites = FavoritePitcher.objects.filter(user=user)
            serializer = self.get_serializer(favorites, many=True)
            logger.info(f"Retrieved {len(favorites)} favorites for user {username}")
            response = Response(serializer.data)
            log_response(response, "FavoritePitcherViewSet.my_favorites")
            return response
        except Exception as e:
            logger.error(f"Error retrieving favorites: {str(e)}", exc_info=True)
            response = Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            log_response(response, "FavoritePitcherViewSet.my_favorites")
            return response

    @action(detail=False, methods=['get'])
    def get_all_favorites(self, request):
        log_request(request, "FavoritePitcherViewSet.get_all_favorites")
        try:
            username = request.query_params.get('username')
            if not username:
                response = Response(
                    {'detail': 'username parameter is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                log_response(response, "FavoritePitcherViewSet.get_all_favorites")
                return response

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                response = Response(
                    {'detail': f'User {username} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
                log_response(response, "FavoritePitcherViewSet.get_all_favorites")
                return response

            favorites = FavoritePitcher.objects.filter(user=user)
            serializer = self.get_serializer(favorites, many=True)
            logger.info(f"Retrieved {len(favorites)} favorites for user {username}")
            response = Response({
                'favorites': serializer.data,
                'count': len(favorites)
            })
            log_response(response, "FavoritePitcherViewSet.get_all_favorites")
            return response
        except Exception as e:
            logger.error(f"Error retrieving favorites: {str(e)}", exc_info=True)
            response = Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            log_response(response, "FavoritePitcherViewSet.get_all_favorites")
            return response

    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        log_request(request, "FavoritePitcherViewSet.clear_all")
        try:
            username = request.query_params.get('username')
            if not username:
                response = Response(
                    {'detail': 'username parameter is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                log_response(response, "FavoritePitcherViewSet.clear_all")
                return response

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                response = Response(
                    {'detail': f'User {username} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
                log_response(response, "FavoritePitcherViewSet.clear_all")
                return response

            count = FavoritePitcher.objects.filter(user=user).count()
            FavoritePitcher.objects.filter(user=user).delete()
            logger.info(f"Successfully deleted all {count} favorites for user {username}")
            response = Response(
                {'message': f'Successfully deleted all {count} favorites'},
                status=status.HTTP_200_OK
            )
            log_response(response, "FavoritePitcherViewSet.clear_all")
            return response
        except Exception as e:
            logger.error(f"Error clearing favorites: {str(e)}", exc_info=True)
            response = Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
            log_response(response, "FavoritePitcherViewSet.clear_all")
            return response

    @action(detail=False, methods=['delete'])
    def delete_by_name(self, request):
        log_request(request, "FavoritePitcherViewSet.delete_by_name")
        try:
            player_name = request.query_params.get('player_name')
            if not player_name:
                response = Response(
                    {'error': 'player_name parameter is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                log_response(response, "FavoritePitcherViewSet.delete_by_name")
                return response

            logger.info(f"Attempting to delete favorite for player: {player_name}")
            
            # First try exact match
            favorite = self.get_queryset().filter(pitcher__player_name=player_name).first()
            
            # If no exact match, try case-insensitive match
            if not favorite:
                logger.info(f"No exact match found, trying case-insensitive match")
                favorite = self.get_queryset().filter(pitcher__player_name__iexact=player_name).first()
            
            # If still no match, try removing any extra spaces
            if not favorite:
                logger.info(f"No case-insensitive match found, trying with normalized spaces")
                normalized_name = ' '.join(player_name.split())
                favorite = self.get_queryset().filter(pitcher__player_name__iexact=normalized_name).first()

            if not favorite:
                logger.warning(f"No favorite found for player: {player_name}")
                response = Response(
                    {'error': f'No favorite found for player: {player_name}'},
                    status=status.HTTP_404_NOT_FOUND
                )
                log_response(response, "FavoritePitcherViewSet.delete_by_name")
                return response

            favorite.delete()
            logger.info(f"Successfully deleted favorite for player: {player_name}")
            response = Response(status=status.HTTP_204_NO_CONTENT)
            log_response(response, "FavoritePitcherViewSet.delete_by_name")
            return response
        except Exception as e:
            logger.error(f"Error deleting favorite: {str(e)}", exc_info=True)
            response = Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
            log_response(response, "FavoritePitcherViewSet.delete_by_name")
            return response

    def destroy(self, request, *args, **kwargs):
        log_request(request, "FavoritePitcherViewSet.destroy")
        try:
            instance = self.get_object()
            logger.info(f"Attempting to delete favorite {instance.id} for user {request.user.username}")
            self.perform_destroy(instance)
            logger.info("Successfully deleted favorite")
            response = Response(status=status.HTTP_204_NO_CONTENT)
            log_response(response, "FavoritePitcherViewSet.destroy")
            return response
        except Exception as e:
            logger.error(f"Error deleting favorite: {str(e)}", exc_info=True)
            response = Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
            log_response(response, "FavoritePitcherViewSet.destroy")
            return response
