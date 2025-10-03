from rest_framework import serializers
from .models import MCSTCAnalysis, MCSTCCoordinationPair
from projects.models import Project


class MCSTCAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for MC-STC Analysis"""
    
    project_name = serializers.CharField(source='project.name', read_only=True)
    project_repo_url = serializers.CharField(source='project.repo_url', read_only=True)
    duration_minutes = serializers.SerializerMethodField()
    role_distribution = serializers.SerializerMethodField()
    
    class Meta:
        model = MCSTCAnalysis
        fields = [
            'id', 'project', 'project_name', 'project_repo_url', 'analysis_date',
            'is_completed', 'monte_carlo_iterations', 'functional_roles_used',
            'mcstc_value', 'inter_class_coordination_score', 'intra_class_coordination_score',
            'developer_security_coordination', 'developer_ops_coordination', 'security_ops_coordination',
            'branch_analyzed', 'total_contributors_analyzed', 'developer_count', 'security_count', 'ops_count',
            'duration_minutes', 'role_distribution', 'error_message'
        ]
        read_only_fields = [
            'id', 'analysis_date', 'project_name', 'project_repo_url', 'duration_minutes', 'role_distribution'
        ]
    
    def get_duration_minutes(self, obj):
        """Calculate analysis duration in minutes"""
        # This would be calculated based on start/end times if we track them
        return None
    
    def get_role_distribution(self, obj):
        """Get role distribution summary"""
        return {
            'developer': obj.developer_count,
            'security': obj.security_count,
            'ops': obj.ops_count,
            'total': obj.total_contributors_analyzed
        }


class MCSTCAnalysisCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating MC-STC Analysis"""
    
    class Meta:
        model = MCSTCAnalysis
        fields = ['project', 'monte_carlo_iterations', 'functional_roles_used']
        
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
    
    def validate_functional_roles_used(self, value):
        """Validate functional roles"""
        valid_roles = ['developer', 'security', 'ops', 'unclassified']
        for role in value:
            if role not in valid_roles:
                raise serializers.ValidationError(f"Invalid functional role: {role}")
        return value


class MCSTCCoordinationPairSerializer(serializers.ModelSerializer):
    """Serializer for MC-STC Coordination Pairs"""
    
    coordination_type = serializers.SerializerMethodField()
    coordination_status = serializers.SerializerMethodField()
    
    class Meta:
        model = MCSTCCoordinationPair
        fields = [
            'id', 'contributor1_id', 'contributor1_role', 'contributor1_email',
            'contributor2_id', 'contributor2_role', 'contributor2_email',
            'coordination_requirement', 'actual_coordination', 'coordination_gap',
            'impact_score', 'is_inter_class', 'is_missed_coordination', 'is_unnecessary_coordination',
            'shared_files', 'coordination_files', 'coordination_type', 'coordination_status'
        ]
        read_only_fields = ['id', 'coordination_type', 'coordination_status']
    
    def get_coordination_type(self, obj):
        """Get coordination type description"""
        if obj.is_inter_class:
            return f"{obj.contributor1_role}-{obj.contributor2_role}"
        else:
            return f"{obj.contributor1_role}-{obj.contributor1_role}"
    
    def get_coordination_status(self, obj):
        """Get coordination status"""
        if obj.is_missed_coordination:
            return "missed"
        elif obj.is_unnecessary_coordination:
            return "unnecessary"
        else:
            return "adequate"


class MCSTCResultSerializer(serializers.Serializer):
    """Serializer for MC-STC calculation results"""
    
    mcstc_value = serializers.FloatField()
    inter_class_score = serializers.FloatField()
    intra_class_score = serializers.FloatField()
    role_coordination_matrix = serializers.DictField()
    top_coordination_pairs = MCSTCCoordinationPairSerializer(many=True, read_only=True)
    analysis_summary = serializers.DictField()
    recommendations = serializers.ListField(child=serializers.CharField(), read_only=True)


class MCSTCStatsSerializer(serializers.Serializer):
    """Serializer for MC-STC statistics"""
    
    project_id = serializers.UUIDField()
    project_name = serializers.CharField()
    total_analyses = serializers.IntegerField()
    completed_analyses = serializers.IntegerField()
    average_mcstc_value = serializers.FloatField()
    latest_mcstc_value = serializers.FloatField()
    trend_direction = serializers.CharField()  # 'improving', 'declining', 'stable'
    role_distribution = serializers.DictField()
    coordination_health = serializers.CharField()  # 'excellent', 'good', 'fair', 'poor'


class MCSTCComparisonSerializer(serializers.Serializer):
    """Serializer for comparing MC-STC results across projects or time periods"""
    
    project_id = serializers.UUIDField()
    project_name = serializers.CharField()
    analysis_date = serializers.DateTimeField()
    mcstc_value = serializers.FloatField()
    role_coordination_scores = serializers.DictField()
    top_issues = serializers.ListField(child=serializers.DictField())
    improvement_suggestions = serializers.ListField(child=serializers.CharField())
