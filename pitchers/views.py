from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Pitcher, FavoritePitcher
from .serializers import UserSerializer, PitcherSerializer, FavoritePitcherSerializer
import logging

logger = logging.getLogger(__name__)

# Create your views here.

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
        return FavoritePitcher.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        try:
            logger.info(f"Attempting to create favorite with data: {self.request.data}")
            serializer.save(user=self.request.user)
            logger.info("Successfully created favorite")
        except Exception as e:
            logger.error(f"Error creating favorite: {str(e)}", exc_info=True)
            raise

    @action(detail=False, methods=['get'])
    def my_favorites(self, request):
        try:
            favorites = self.get_queryset()
            serializer = self.get_serializer(favorites, many=True)
            logger.info(f"Retrieved {len(favorites)} favorites for user {request.user.username}")
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving favorites: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['delete'])
    def clear_all(self, request):
        try:
            count = self.get_queryset().count()
            self.get_queryset().delete()
            logger.info(f"Successfully deleted all {count} favorites for user {request.user.username}")
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
