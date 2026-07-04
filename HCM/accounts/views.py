from django.shortcuts import render

# Create your views here.

from dotenv import load_dotenv
import os

from supabase import create_client, Client

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny

load_dotenv()

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
)


class CreateUserView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):

        employee_id = request.data.get("employee_id")
        full_name = request.data.get("full_name")
        email = request.data.get("email")
        phone = request.data.get("phone")
        password = request.data.get("password")
        role = request.data.get("role")
        district_id = request.data.get("district_id")
        center_id = request.data.get("center_id")
        specialization = request.data.get("specialization")
        is_active = request.data.get("is_active", True)
        created_by = request.data.get("created_by")

        if not all([employee_id, full_name, email, password, role, district_id]):
            return Response(
                {"error": "Required fields are missing."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:

            auth_user = supabase.auth.admin.create_user(
                {
                    "email": email,
                    "password": password,
                    "email_confirm": True,
                }
            )

            user_id = auth_user.user.id

            supabase.table("Users").insert(
                {
                    "id": user_id,
                    "employee_id": employee_id,
                    "full_name": full_name,
                    "email": email,
                    "phone": phone,
                    "role": role,
                    "district_id": district_id,
                    "center_id": center_id,
                    "is_active": is_active,
                    "created_by": created_by,
                    "specialization": specialization,
                }
            ).execute()

            return Response(
                {
                    "message": "User created successfully."
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:

            return Response(
                {
                    "error": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )