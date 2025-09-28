# users/serializers.py
from rest_framework import serializers
from .models import CustomUser

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        # 'last_name' lo usaremos como apellido_paterno
        fields = [
            'id', 
            'email', 
            'password', 
            'first_name', 
            'last_name', 
            'apellido_materno', 
            'rut', 
            'telefono', 
            'fecha_nacimiento', 
            'sexo'
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Usamos nuestro manager personalizado para crear el usuario
        user = CustomUser.objects.create_user(**validated_data)
        return user