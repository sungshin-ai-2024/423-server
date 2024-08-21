# serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, Profile, Guardian
import logging

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['signup_name', 'phone_number', 'birth_date', 'sex', 'zipcode', 'address', 'detailed_address']


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ('signup_id', 'password', 'profile')
        extra_kwargs = {
            'signup_id': {'required': True},  # signup_id 필드를 필수 입력으로 설정
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', None)
        if not profile_data:
            raise serializers.ValidationError("Profile data is required.")

        user = User.objects.create_user(**validated_data)
        Profile.objects.create(user=user, **profile_data)
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)

        profile = instance.profile
        if profile_data:
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        password = validated_data.get('password')
        if password:
            instance.set_password(password)

        instance.save()

        return instance

class LoginSerializer(serializers.Serializer):
    signup_id = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        signup_id = data.get("signup_id")
        password = data.get("password")

        if signup_id and password:
            user = authenticate(signup_id=signup_id, password=password)
            if user:
                data["user"] = user
            else:
                raise serializers.ValidationError("Unable to log in with provided credentials.")
        else:
            raise serializers.ValidationError("Must include 'signup_id' and 'password'.")
        return data

class GuardianSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guardian
        fields = ['name', 'relationship', 'phone_number']
        read_only_fields = ['user']  # user 필드는 읽기 전용으로 설정

    def create(self, validated_data):
        # 요청에서 user를 가져와 설정
        user = self.context['request'].user
        guardian = Guardian.objects.create(user=user, **validated_data)
        return guardian