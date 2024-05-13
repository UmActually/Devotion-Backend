from rest_framework import serializers
from devotion.serializers import CCModelSerializer
from .models import Widget, WidgetDisplayType, DataSource
from tasks.serializers import get_project_or_error

def get_data_source_or_error(data_source_id: str) -> DataSource:
    try:
        return DataSource.objects.get(id=data_source_id)
    except DataSource.DoesNotExist:
        raise serializers.ValidationError("La fuente de datos no existe.")

class WidgetSerializer(CCModelSerializer):
    class Meta:
        model = Widget
        fields = ("id", "name", "display_type", "data_source", "position", "unit")


class WidgetDeserializer(serializers.Serializer):
    name = serializers.CharField(max_length=64, required=True)
    display_type = serializers.IntegerField(required=True)
    data_source = serializers.CharField(required=True)
    project = serializers.CharField(required=True)
    position = serializers.IntegerField(required=True)
    unit = serializers.CharField(max_length=16, required=False)

    def validate(self, attrs):
        display_type = attrs["display_type"]
        if display_type not in WidgetDisplayType.values:
            raise serializers.ValidationError("Tipo de visualización inválido.")

        self.context["project"] = get_project_or_error(attrs["project"])
        self.context["data_source"] = get_data_source_or_error(attrs["data_source"])

        return attrs
    
    def create(self, validated_data):
        validated_data["project"] = self.context["project"]
        validated_data["data_source"] = self.context["data_source"]
        
        return Widget.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr in ("data_source", "project"):
                attr += "_id"
            setattr(instance, attr, value)

        instance.save()
        return instance
    

class DataSourceSerializer(CCModelSerializer):
    class Meta:
        model = DataSource
        fields = ("id", "name", "mqtt_topic")
    

class DataSourceDeserializer(serializers.Serializer):
    name = serializers.CharField(max_length=64, required=True)
    project = serializers.CharField(required=True)
    mqtt_topic = serializers.CharField(max_length=64, required=True)

    def validate(self, attrs):
        self.context["project"] = get_project_or_error(attrs["project"])
        return attrs

    def create(self, validated_data):
        validated_data["project"] = self.context["project"]
        return DataSource.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr in ("project"):
                attr += "_id"
            setattr(instance, attr, value)
        instance.save()
        return instance 