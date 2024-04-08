from rest_framework import serializers


def camel_case(snake_str: str) -> str:
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


class CCModelSerializer(serializers.ModelSerializer):
    """Model Serializer abstracto que convierte las claves de los campos a camelCase."""
    def to_representation(self, instance):
        data = super(serializers.ModelSerializer, self).to_representation(instance)
        return {camel_case(key): value for key, value in data.items()}
