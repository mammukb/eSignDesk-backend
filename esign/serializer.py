#serializer.py

from rest_framework import serializers
from .models import *

class StudentSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(required=False, allow_blank=True)
    regno = serializers.CharField()
    email = serializers.EmailField(required=False, allow_blank=True)
    course = serializers.CharField(required=False, allow_blank=True)
    year = serializers.IntegerField(required=False)
    phone_no = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField()
    

    def create(self, validated_data):
        from .models import Student
        return Student(**validated_data).save()

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance

class DepartmentSerializer(serializers.Serializer):
    name = serializers.CharField()
    code = serializers.CharField()

    def create(self, validated_data):
        from .models import Department
        return Department(**validated_data).save()
    
    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance

# ---- FormTemplate ----
class FieldDefinitionSerializer(serializers.Serializer):
    label = serializers.CharField()
    type = serializers.ChoiceField(choices=["text", "textarea", "radio", "dropdown"])
    name = serializers.CharField(required=False, allow_blank=True)
    placeholder = serializers.CharField(required=False, allow_blank=True)
    required = serializers.BooleanField(default=False)
    options = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )
    order = serializers.IntegerField(required=False)

class FormTemplateSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    title = serializers.CharField()
    issued_by = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(default=True)
    fields = FieldDefinitionSerializer(many=True)

    def create(self, validated_data):
        fields_data = validated_data.pop("fields", [])
        form = FormTemplate(**validated_data)
        form.fields = [FieldDefinition(**fd) for fd in fields_data]
        form.save()
        return form

    def update(self, instance, validated_data):
        fields_data = validated_data.pop("fields", [])
        for k, v in validated_data.items():
            setattr(instance, k, v)
        if fields_data:
            instance.fields = [FieldDefinition(**fd) for fd in fields_data]
        instance.save()
        return instance
    
# ---- Staff Serializer ----

class StaffSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    staffid = serializers.CharField()
    name = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField()
    designation = serializers.CharField(required=False, allow_blank=True)
    department = serializers.CharField(required=False, allow_blank=True)
    signature_imageurl = serializers.CharField(required=False, allow_blank=True, default="")

    def create(self, validated_data):
        from .models import Staff
        if "signature_imageurl" not in validated_data:  # enforce empty when not provided
            validated_data["signature_imageurl"] = ""
        return Staff(**validated_data).save()

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        if "signature_imageurl" not in validated_data:
            instance.signature_imageurl = instance.signature_imageurl or ""
        instance.save()
        return instance
