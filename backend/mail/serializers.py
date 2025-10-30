from rest_framework import serializers


class MailSerializer(serializers.Serializer):
    pass


class LandlordMailSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField()
    message = serializers.CharField()
    agentMail = serializers.EmailField()
