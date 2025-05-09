from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Pitcher, FavoritePitcher
from .serializers import UserSerializer, PitcherSerializer, FavoritePitcherSerializer

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
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'user': UserSerializer(user, context=self.get_serializer_context()).data,
                'message': 'User Created Successfully'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
