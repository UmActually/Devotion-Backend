from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from devotion.serializers import CCModelSerializer
from .models import User


class UserSerializer(CCModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "first_names", "last_names")
        extra_kwargs = {
            "password": {"write_only": True},
            "is_staff": {"read_only": True}
        }


class UserMinimalSerializer(CCModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "name")

    def get_name(self, obj):
        return f"{obj.first_names} {obj.last_names}"


class UserDeserializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)
    first_names = serializers.CharField(max_length=64, required=True)
    last_names = serializers.CharField(max_length=64, required=True)

    def validate(self, attrs):
        if "email" in attrs and User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError("Este correo ya está registrado.")
        return attrs

    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data["password"])
        return User.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
