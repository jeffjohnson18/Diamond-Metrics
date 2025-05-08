from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Pitcher, FavoritePitcher

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class PitcherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pitcher
        fields = '__all__'

class FavoritePitcherSerializer(serializers.ModelSerializer):
    pitcher = PitcherSerializer(read_only=True)
    pitcher_id = serializers.PrimaryKeyRelatedField(
        queryset=Pitcher.objects.all(),
        write_only=True,
        source='pitcher'
    )

    class Meta:
        model = FavoritePitcher
        fields = ('id', 'pitcher', 'pitcher_id', 'created_at') 