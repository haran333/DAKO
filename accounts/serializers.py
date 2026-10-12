from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="first_name", read_only=True)

    class Meta:
        model = User
        fields = ["id", "supabase_id", "email", "name", "avatar_url", "date_joined"]
        read_only_fields = fields
