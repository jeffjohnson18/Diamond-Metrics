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
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def my_favorites(self, request):
        favorites = self.get_queryset()
        serializer = self.get_serializer(favorites, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
