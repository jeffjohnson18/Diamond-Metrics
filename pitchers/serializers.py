from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Pitcher, FavoritePitcher
import logging

logger = logging.getLogger(__name__)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            logger.warning(f"Email {value} already exists")
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            logger.warning(f"Username {value} already exists")
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def create(self, validated_data):
        try:
            logger.info(f"Creating user with username: {validated_data.get('username')}")
            user = User.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                password=validated_data['password']
            )
            logger.info(f"Successfully created user: {user.username}")
            return user
        except Exception as e:
            logger.error(f"Error in create method: {str(e)}", exc_info=True)
            raise

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

    def validate(self, data):
        logger.info(f"Validating data: {data}")
        if 'pitcher_id' not in data:
            raise serializers.ValidationError(
                "pitcher_id is required"
            )
        return data

    def create(self, validated_data):
        try:
            logger.info(f"Creating favorite with data: {validated_data}")
            pitcher_id = validated_data.pop('pitcher_id')
            try:
                pitcher = Pitcher.objects.get(id=pitcher_id)
                validated_data['pitcher'] = pitcher
                return super().create(validated_data)
            except Pitcher.DoesNotExist:
                raise serializers.ValidationError({'pitcher_id': f'Pitcher with id {pitcher_id} does not exist'})
        except Exception as e:
            logger.error(f"Error creating favorite: {str(e)}", exc_info=True)
            raise 