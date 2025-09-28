# core/views.py

from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .serializers import UserSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,) # Permite a cualquiera registrarse
    serializer_class = UserSerializer

class LoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({"token": token.key})
        else:
            return Response({"error": "Credenciales inválidas"}, status=400)

class ProfileView(APIView):
    print("pasa1")
    permission_classes = (IsAuthenticated,) # Solo usuarios autenticados
    print("pasa2")

    def get(self, request, *args, **kwargs):
        print("pasa3")
        return Response({
            "id": request.user.id,
            "username": request.user.username,
            "email": request.user.email,
        })