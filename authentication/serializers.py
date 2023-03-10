from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = get_user_model()
        fields = (
            "email",
            "email_verified",
        )
        read_only_fields = ("email_verified",)


class ChangeEmailSerializer(serializers.HyperlinkedModelSerializer):
    new_email = serializers.EmailField(
        write_only=True,
        required=True,
        help_text=_("New email"),
    )

    class Meta:
        model = get_user_model()
        fields = ("password", "new_email")
        extra_kwargs = {"password": {"write_only": True}}

    def validate_password(self, password):
        request = self.context["request"]
        if not request.user.check_password(password):
            raise serializers.ValidationError(_("Password doesn't match"))
        return password

    def validate_new_email(self, new_email):
        if get_user_model().objects.filter(email=new_email).exists():
            raise serializers.ValidationError(_("Email already registered"))
        return new_email

    def update(self, user, validated_data):
        user.email = validated_data["new_email"]
        user.email_verified = False
        user.save()
        return user


class ChangePasswordSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        help_text=_("New password"),
        style={"input_type": "password"},
    )

    class Meta:
        model = get_user_model()
        fields = ("password", "new_password")
        extra_kwargs = {"password": {"write_only": True}}

    def validate_password(self, password):
        request = self.context["request"]
        if not request.user.check_password(password):
            raise serializers.ValidationError(_("Password doesn't match"))
        return password

    def validate_new_password(self, new_password):
        validate_password(new_password)
        return new_password

    def update(self, user, validated_data):
        user.set_password(validated_data["new_password"])
        user.save()
        return user


class EmailAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(label=_("Email"), write_only=True)
    password = serializers.CharField(
        label=_("Password"),
        style={"input_type": "password"},
        trim_whitespace=False,
        write_only=True,
    )
    token = serializers.CharField(label=_("Token"), read_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        user = authenticate(
            request=self.context.get("request"), email=email, password=password
        )
        attrs["user"] = user
        return attrs
