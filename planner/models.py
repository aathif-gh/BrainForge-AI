from django.db import models


class UserProject(models.Model):
    idea_name = models.CharField(max_length=255)
    description = models.TextField()
    time_available = models.PositiveIntegerField(help_text="Available hours per week")
    budget = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Available budget in USD"
    )
    skills = models.TextField(
        help_text="Comma-separated or plain text of existing skills"
    )
    goal = models.TextField(help_text="Goal or outcome")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.idea_name

    class Meta:
        ordering = ["-created_at"]


class ProjectAnalysis(models.Model):
    project = models.OneToOneField(
        UserProject, on_delete=models.CASCADE, related_name="analysis"
    )

    # Idea Clarification
    problem_statement = models.TextField()
    target_audience = models.TextField()
    value_proposition = models.TextField()
    key_assumptions = models.JSONField(help_text="Key assumptions list")

    # Feasibility Analysis
    # Contains: time_score, budget_score, skill_score, overall_score, and rationales
    feasibility_score = models.JSONField()

    # Risk Assessment
    # Contains: technical, resource, market, and skills gaps risks with mitigations
    risks = models.JSONField()

    # Scenario Simulation
    # Contains: optimistic, realistic, pessimistic outcomes with success probabilities and success factors
    scenarios = models.JSONField()

    # Roadmap Generator
    # Contains: 30, 60, 90 day milestones and tasks
    roadmap = models.JSONField()

    # First Action Recommendation
    first_action = models.TextField()

    # Responsible AI Section
    confidence_level = models.CharField(
        max_length=10,
        choices=[("High", "High"), ("Medium", "Medium"), ("Low", "Low")],
        default="Medium",
    )

    is_fallback = models.BooleanField(default=False)

    # NEW HACKATHON UPGRADE FIELDS
    readiness_score = models.PositiveIntegerField(
        default=0, help_text="Weighted overall readiness score 0-100"
    )
    readiness_interpretation = models.TextField(
        blank=True, default="", help_text="AI rationale for readiness score"
    )
    risk_level = models.PositiveIntegerField(
        default=5, help_text="Overall risk level out of 10"
    )
    confidence_score = models.PositiveIntegerField(
        default=50, help_text="Confidence percentage 0-100"
    )
    confidence_reasoning = models.TextField(
        blank=True, default="", help_text="AI confidence explanation"
    )
    assumptions = models.JSONField(
        blank=True, null=True, help_text="Hidden assumptions validation recommendations"
    )
    what_if_results = models.JSONField(
        blank=True, null=True, help_text="Sandbox cached simulation results"
    )
    generated_pdf_history = models.JSONField(
        blank=True, null=True, help_text="Log of generated PDF downloads"
    )

    # NEW SECOND BRAIN FIELDS
    mentor_debate_results = models.JSONField(
        blank=True,
        null=True,
        help_text="Expert debate viewpoints from Builder, Investor, and Engineer",
    )
    blind_spot_analysis = models.JSONField(
        blank=True,
        null=True,
        help_text="Weakness analysis highlighting cognitive blind spots and validation recommendations",
    )
    opportunity_cost_analysis = models.JSONField(
        blank=True,
        null=True,
        help_text="Sacrifices vs benefits analysis, net score, and text summary",
    )

    def __str__(self):
        return f"Analysis for {self.project.idea_name}"


class ProjectChatMessage(models.Model):
    project = models.ForeignKey(
        UserProject, on_delete=models.CASCADE, related_name="chat_messages"
    )
    role = models.CharField(
        max_length=10, choices=[("user", "User"), ("coach", "Coach")]
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.role.capitalize()} message for {self.project.idea_name} at {self.timestamp}"
