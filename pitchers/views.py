from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Pitcher, FavoritePitcher
from .serializers import UserSerializer, PitcherSerializer, FavoritePitcherSerializer
import logging
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

# Create your views here.

class UserInfoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            logger.info(f"Retrieved user info for {user.username}")
            return Response({
                'user_id': user.id,
                'username': user.username,
                'email': user.email
            })
        except Exception as e:
            logger.error(f"Error retrieving user info: {str(e)}", exc_info=True)
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        try:
            logger.info(f"Attempting to create user with data: {request.data}")
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                logger.info(f"Successfully created user: {user.username}")
                return Response({
                    'user': UserSerializer(user, context=self.get_serializer_context()).data,
                    'message': 'User Created Successfully'
                }, status=status.HTTP_201_CREATED)
            logger.error(f"Validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}", exc_info=True)
            return Response({
                'error': str(e),
                'detail': 'An error occurred while creating the user'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PitcherViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Pitcher.objects.all()
    serializer_class = PitcherSerializer
    permission_classes = [permissions.IsAuthenticated]

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
        try:
            username = request.query_params.get('username')
            if not username:
                return Response(
                    {'detail': 'username parameter is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response(
                    {'detail': f'User {username} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            pitcher_names = request.data.get('pitcher_names', [])
            if not pitcher_names:
                return Response(
                    {'detail': 'pitcher_names array cannot be empty'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            logger.info(f"Attempting to save favorites for user {username}: {pitcher_names}")
            
            # Clear existing favorites
            FavoritePitcher.objects.filter(user=user).delete()
            logger.info("Cleared existing favorites")

            # Create new favorites
            saved_favorites = []
            for name in pitcher_names:
                try:
                    pitcher = Pitcher.objects.get(player_name__iexact=name)
                    favorite = FavoritePitcher.objects.create(
                        user=user,
                        pitcher=pitcher
                    )
                    saved_favorites.append({
                        'pitcher_name': pitcher.player_name
                    })
                    logger.info(f"Created favorite for {pitcher.player_name}")
                except Pitcher.DoesNotExist:
                    logger.warning(f"Pitcher not found: {name}")
                    continue

            logger.info(f"Successfully saved {len(saved_favorites)} favorites")
            return Response({
                'favorites': saved_favorites,
                'count': len(saved_favorites)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error saving favorites: {str(e)}", exc_info=True)
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def my_favorites(self, request):
        try:
            username = request.query_params.get('username')
            if not username:
                return Response(
                    {'detail': 'username parameter is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response(
                    {'detail': f'User {username} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            favorites = FavoritePitcher.objects.filter(user=user)
            serializer = self.get_serializer(favorites, many=True)
            logger.info(f"Retrieved {len(favorites)} favorites for user {username}")
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving favorites: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def get_all_favorites(self, request):
        try:
            username = request.query_params.get('username')
            if not username:
                return Response(
                    {'detail': 'username parameter is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response(
                    {'detail': f'User {username} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            favorites = FavoritePitcher.objects.filter(user=user)
            serializer = self.get_serializer(favorites, many=True)
            logger.info(f"Retrieved {len(favorites)} favorites for user {username}")
            return Response({
                'favorites': serializer.data,
                'count': len(favorites)
            })
        except Exception as e:
            logger.error(f"Error retrieving favorites: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        try:
            username = request.query_params.get('username')
            if not username:
                return Response(
                    {'detail': 'username parameter is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response(
                    {'detail': f'User {username} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            count = FavoritePitcher.objects.filter(user=user).count()
            FavoritePitcher.objects.filter(user=user).delete()
            logger.info(f"Successfully deleted all {count} favorites for user {username}")
            return Response(
                {'message': f'Successfully deleted all {count} favorites'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error clearing favorites: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['delete'])
    def delete_by_name(self, request):
        try:
            player_name = request.query_params.get('player_name')
            if not player_name:
                return Response(
                    {'error': 'player_name parameter is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

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
                return Response(
                    {'error': f'No favorite found for player: {player_name}'},
                    status=status.HTTP_404_NOT_FOUND
                )

            favorite.delete()
            logger.info(f"Successfully deleted favorite for player: {player_name}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting favorite: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            logger.info(f"Attempting to delete favorite {instance.id} for user {request.user.username}")
            self.perform_destroy(instance)
            logger.info("Successfully deleted favorite")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting favorite: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
