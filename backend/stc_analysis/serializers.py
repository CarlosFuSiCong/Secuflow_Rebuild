from rest_framework import serializers
from .models import STCAnalysis
from projects.models import Project


class STCAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for STC Analysis model"""
    
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_repo_url = serializers.CharField(source='project.repo_url', read_only=True)
    
    class Meta:
        model = STCAnalysis
        fields = [
            'id', 'project', 'project_name', 'project_repo_url',
            'analysis_date', 'is_completed', 'use_monte_carlo',
            'monte_carlo_iterations', 'stc_value', 'branch_analyzed',
            'contributors_count', 'coordination_requirements_total',
            'coordination_actuals_total', 'missed_coordination_count',
            'unnecessary_coordination_count', 'results_file', 'error_message'
        ]
        read_only_fields = ['id', 'analysis_date', 'project_name', 'project_repo_url']


class STCAnalysisCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating STC Analysis"""
    
    class Meta:
        model = STCAnalysis
        fields = ['project', 'use_monte_carlo', 'monte_carlo_iterations']
        
    def validate_project(self, value):
        """Validate project exists"""
        if not Project.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Project does not exist")
        return value
    
    def validate_monte_carlo_iterations(self, value):
        """Validate monte carlo iterations range"""
        if value < 100:
            raise serializers.ValidationError("Monte Carlo iterations must be at least 100")
        if value > 10000:
            raise serializers.ValidationError("Monte Carlo iterations cannot exceed 10000")
        return value


class STCResultSerializer(serializers.Serializer):
    """Serializer for STC calculation results"""
    
    node_id = serializers.CharField()
    contributor_login = serializers.CharField(required=False, allow_null=True)
    stc_value = serializers.FloatField()
    rank = serializers.IntegerField()


class STCAnalysisResultsSerializer(serializers.Serializer):
    """Serializer for complete STC analysis results"""
    
    analysis_id = serializers.IntegerField()
    project_id = serializers.UUIDField()
    project_name = serializers.CharField()
    analysis_date = serializers.DateTimeField()
    use_monte_carlo = serializers.BooleanField()
    total_nodes = serializers.IntegerField()
    total_spanning_trees = serializers.FloatField(required=False, allow_null=True)
    results = STCResultSerializer(many=True)
    
    
class STCComparisonSerializer(serializers.Serializer):
    """Serializer for comparing STC values between contributors"""
    
    contributor_login = serializers.CharField()
    contributor_id = serializers.IntegerField()
    stc_value = serializers.FloatField()
    total_modifications = serializers.IntegerField()
    files_modified = serializers.IntegerField()
    functional_role = serializers.CharField()
    is_core_contributor = serializers.BooleanField()

