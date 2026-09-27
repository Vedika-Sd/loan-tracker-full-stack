from rest_framework import serializers

from .models import ApplicationTimeline, LoanApplication, LoanDocument


class LoanDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanDocument
        fields = ['id', 'document_type', 'original_name', 'content_type', 'status', 'rejection_reason', 'created_at', 'updated_at']


class TimelineSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source='actor.username', read_only=True, allow_null=True)

    class Meta:
        model = ApplicationTimeline
        fields = ['id', 'status', 'message', 'actor_name', 'created_at']


class LoanApplicationSerializer(serializers.ModelSerializer):
    documents = LoanDocumentSerializer(many=True, read_only=True)
    timeline = TimelineSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.username', read_only=True)

    class Meta:
        model = LoanApplication
        fields = ['id', 'customer_name', 'loan_type', 'amount', 'tenure_months', 'status', 'rejection_reason', 'documents', 'timeline', 'created_at', 'updated_at']
        read_only_fields = ['loan_type', 'status', 'rejection_reason']


class LoanApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanApplication
        fields = ['amount', 'tenure_months']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Amount must be greater than zero.')
        return value

    def validate_tenure_months(self, value):
        if value <= 0:
            raise serializers.ValidationError('Tenure must be greater than zero.')
        return value