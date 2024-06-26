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


class UserRoleSerializer(CCModelSerializer):
    name = serializers.SerializerMethodField()
    is_leader = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "email", "name", "is_leader", "profile_picture")

    def get_name(self, obj):
        return f"{obj.first_names} {obj.last_names}"

    def get_is_leader(self, obj):
        return obj in self.context["project"].leaders.all()


class UserDeserializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)
    first_names = serializers.CharField(max_length=64, required=True)
    last_names = serializers.CharField(max_length=64, required=True)
    profile_picture = serializers.URLField(required=False)

    def validate(self, attrs):
        if "email" in attrs and User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError("Este correo ya está registrado.")
        if "profile_picture" in attrs \
                and not attrs["profile_picture"].startswith("https://lh3.googleusercontent.com/"):
            raise serializers.ValidationError("La URL de la imagen de perfil debe ser válida.")
        return attrs

    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data["password"])
        return User.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
