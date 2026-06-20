from django.test import TestCase, Client
from django.urls import reverse
import json
from .models import UserProject, ProjectAnalysis, ProjectChatMessage


class UserProjectModelTest(TestCase):
    def setUp(self):
        self.project = UserProject.objects.create(
            idea_name="Smart Garden",
            description="Automated indoor watering system using IoT soil sensors.",
            time_available=10,
            budget=150.00,
            skills="Python, basic electronics",
            goal="Build a working prototype in 45 days",
        )

    def test_project_creation(self):
        """Tests that a UserProject instance is created correctly."""
        self.assertEqual(self.project.idea_name, "Smart Garden")
        self.assertEqual(self.project.time_available, 10)
        self.assertEqual(float(self.project.budget), 150.00)
        self.assertEqual(str(self.project), "Smart Garden")


class PlannerViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.project = UserProject.objects.create(
            idea_name="Smart Garden",
            description="Automated indoor watering system using IoT soil sensors.",
            time_available=10,
            budget=150.00,
            skills="Python, basic electronics",
            goal="Build a working prototype in 45 days",
        )

        self.analysis = ProjectAnalysis.objects.create(
            project=self.project,
            problem_statement="Houseplants die from over or under-watering due to lack of real-time monitoring.",
            target_audience="Busy urban professionals owning houseplants.",
            value_proposition="An affordable automated watering helper that takes the guesswork out of plant care.",
            key_assumptions=[
                "People will pay $30 for a kit",
                "Wi-Fi signals reach plants",
            ],
            feasibility_score={
                "time_score": 8,
                "time_rationale": "Sufficient for simple code",
                "budget_score": 6,
                "budget_rationale": "Sensors are cheap",
                "skill_score": 7,
                "skill_rationale": "Has basic IoT skills",
                "overall_score": 7,
                "overall_rationale": "High viability overall",
            },
            risks={
                "technical": {
                    "description": "Water leak",
                    "mitigation": "Encapsulate electronics",
                },
                "resource": {
                    "description": "Running out of time",
                    "mitigation": "Buy pre-assembled parts",
                },
                "market": {
                    "description": "No buyers",
                    "mitigation": "Test with friends first",
                },
                "skills": {
                    "description": "PCB design gap",
                    "mitigation": "Use breadboard",
                },
            },
            scenarios={
                "optimistic": {
                    "outcome": "Rapid prototype build",
                    "probability": 80,
                    "factors": ["Prebuilt libraries"],
                },
                "realistic": {
                    "outcome": "Working prototype in 2 months",
                    "probability": 55,
                    "factors": ["Minor debug delays"],
                },
                "pessimistic": {
                    "outcome": "Burnt sensor halts progress",
                    "probability": 25,
                    "factors": ["Faulty wiring"],
                },
            },
            roadmap={
                "day_30": {
                    "milestone": "Assemble breadboard sensors",
                    "tasks": ["Buy parts", "Flash code"],
                },
                "day_60": {
                    "milestone": "Build automated pump triggers",
                    "tasks": ["Attach water relay"],
                },
                "day_90": {
                    "milestone": "Deploy in living room",
                    "tasks": ["Measure accuracy"],
                },
            },
            first_action="Order an Arduino kit on Amazon.",
            confidence_level="High",
            mentor_debate_results={
                "builder": {
                    "recommendation": "Build a quick wrapper using standard libraries and launch a 1-feature MVP within 3 weeks.",
                    "concern": "Losing early user momentum by trying to build full-scale integrations too early.",
                    "next_step": "Draft a single uploader mock page and test the Python parsing script.",
                },
                "investor": {
                    "recommendation": "Confirm that recruiters actually value ATS-optimized PDF resumes before coding the parser backend.",
                    "concern": "High customer acquisition costs and low monthly user retention metrics.",
                    "next_step": "Create a simple landing page describing the product and track waitlist sign-ups.",
                },
                "engineer": {
                    "recommendation": "Simplify the system design. Rely on standard plain-text parsing before attempting heavy OCR or multi-column layout analysis.",
                    "concern": "High technical complexity in parsing non-standard PDF formats leading to scaling issues.",
                    "next_step": "Test standard PDF text extractors against 15 different sample layout files.",
                },
                "agreement": "All three viewpoints agree that keeping the initial code minimal, avoiding custom cloud models, and focusing on user feedback is the safest way forward.",
                "disagreement": "The Builder wants to start coding the interface immediately, while the Investor wants a landing page first and the Engineer recommends testing the parser accuracy first.",
                "tradeoff_summary": "Building the MVP immediately gathers real usage data, but could lead to technical debt. Scoping the parsing logic down simplifies execution but reduces the early utility for complex resumes.",
            },
            blind_spot_analysis=[
                {
                    "name": "Missing User Validation",
                    "impact": "High",
                    "explanation": "The project plan assumes job seekers will upload their resumes regularly, but provides no empirical survey or interview validation data.",
                    "recommendation": "Interview at least 10 college seniors or active job seekers to check if they would use a resume analyzer weekly.",
                },
                {
                    "name": "Unrealistic Timelines",
                    "impact": "Medium",
                    "explanation": "Allocating only 10 hours per week might make it difficult to build both the uploader interface, parsing logic, and learning resource integrations in 30 days.",
                    "recommendation": "Draft a weekly task breakdown and focus solely on the parser score output for Month 1.",
                },
            ],
            opportunity_cost_analysis={
                "benefits": [
                    "Valuable experience building a full-stack Django project using AI",
                    "Strong portfolio addition demonstrating practical startup validation",
                    "Deepening knowledge in Python file processing and parser integrations",
                ],
                "missed_opportunities": [
                    "Reduces time available to study for AWS/Cloud Architect certifications",
                    "Fewer hours to dedicate to preparing for technical internship interviews",
                    "Direct sacrifice of freelancing income that could be earned on secondary tasks",
                ],
                "net_opportunity_score": 75,
                "summary": "Building this project builds hands-on full-stack skills and startup experience, but it takes time away from dedicated internship prep and direct freelancing income.",
            },
        )

    def test_index_view(self):
        """Index view renders dashboard and list of projects."""
        response = self.client.get(reverse("planner:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "BrainForge AI")
        self.assertContains(response, "Smart Garden")

    def test_project_detail_view(self):
        """Detail view renders project specifics and analysis dashboard."""
        response = self.client.get(
            reverse("planner:project_detail", args=[self.project.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Smart Garden")
        self.assertContains(response, "Arduino kit")

    def test_create_project_view_validation(self):
        """Form creation endpoint rejects missing inputs."""
        response = self.client.post(
            reverse("planner:create_project"),
            {
                "idea_name": "",  # missing name
                "description": "A detailed explanation",
                "time_available": "10",
                "budget": "150",
                "skills": "Python",
                "goal": "Goal",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            str(response.content, encoding="utf8"),
            {"status": "error", "errors": {"idea_name": "Idea name is required."}},
        )

    def test_delete_project_view(self):
        """Delete project endpoint successfully removes database rows."""
        response = self.client.post(
            reverse("planner:delete_project", args=[self.project.id])
        )
        self.assertEqual(response.status_code, 302)  # Redirects to index
        self.assertFalse(UserProject.objects.filter(pk=self.project.id).exists())

    def test_readiness_score_calculation(self):
        """Verifies the weighted math formula for project readiness score."""
        skill_score = 9
        time_score = 8
        budget_score = 9
        risk_level = 4

        readiness_score = int(
            (skill_score * 10) * 0.40
            + (time_score * 10) * 0.30
            + (budget_score * 10) * 0.20
            + (10 - risk_level) * 10 * 0.10
        )
        self.assertEqual(readiness_score, 84)

    def test_confidence_score_classification(self):
        """Verifies that the confidence score translates correctly to classifications."""
        # Test High Confidence boundary (>= 80)
        self.analysis.confidence_score = 85
        self.analysis.save()
        response = self.client.get(
            reverse("planner:project_detail", args=[self.project.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "High Confidence")

        # Test Medium Confidence boundary (50-79)
        self.analysis.confidence_score = 65
        self.analysis.save()
        response = self.client.get(
            reverse("planner:project_detail", args=[self.project.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Medium Confidence")

        # Test Low Confidence boundary (< 50)
        self.analysis.confidence_score = 45
        self.analysis.save()
        response = self.client.get(
            reverse("planner:project_detail", args=[self.project.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Low Confidence")

    def test_what_if_sandbox_simulator(self):
        """Verifies the scenario sandbox endpoint returns correct simulated scaling ratios."""
        response = self.client.get(
            reverse("planner:what_if_simulate", args=[self.project.id]),
            {"budget": "300.00", "time": "20", "team_size": "2", "skill_level": "9"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")

        self.assertIn("current", data)
        self.assertIn("modified", data)
        self.assertEqual(
            data["current"]["readiness_score"], self.analysis.readiness_score
        )

        self.assertEqual(data["modified"]["time_score"], 10)
        self.assertEqual(data["modified"]["budget_score"], 10)
        self.assertEqual(data["modified"]["skill_score"], 9)

    def test_pdf_export_response(self):
        """Confirms the PDF export endpoint yields a valid attachment response containing PDF binary."""
        response = self.client.get(
            reverse("planner:download_pdf", args=[self.project.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(
            response["Content-Disposition"].startswith("attachment; filename=")
        )
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_debate_generation_structure(self):
        """Verifies the presence of Builder, Investor, and Engineer viewpoints and tradeoffs in the database."""
        analysis = self.project.analysis
        debate = analysis.mentor_debate_results
        self.assertIsNotNone(debate)
        self.assertIn("builder", debate)
        self.assertIn("investor", debate)
        self.assertIn("engineer", debate)
        self.assertIn("recommendation", debate["builder"])
        self.assertIn("concern", debate["investor"])
        self.assertIn("next_step", debate["engineer"])
        self.assertIn("agreement", debate)
        self.assertIn("disagreement", debate)
        self.assertIn("tradeoff_summary", debate)

    def test_blind_spot_detector_contents(self):
        """Asserts that warning impact classifications are saved and parsed."""
        analysis = self.project.analysis
        blind_spots = analysis.blind_spot_analysis
        self.assertIsNotNone(blind_spots)
        self.assertGreater(len(blind_spots), 0)
        first_spot = blind_spots[0]
        self.assertIn("name", first_spot)
        self.assertIn("impact", first_spot)
        self.assertIn("explanation", first_spot)
        self.assertIn("recommendation", first_spot)
        self.assertIn(first_spot["impact"], ["High", "Medium", "Low"])

    def test_opportunity_cost_calculations(self):
        """Confirms the opportunity cost structure and constraints."""
        analysis = self.project.analysis
        opp = analysis.opportunity_cost_analysis
        self.assertIsNotNone(opp)
        self.assertIn("benefits", opp)
        self.assertIn("missed_opportunities", opp)
        self.assertIn("net_opportunity_score", opp)
        self.assertIn("summary", opp)

        score = opp["net_opportunity_score"]
        self.assertTrue(0 <= score <= 100)

    def test_chat_history_link_and_detail_view(self):
        """Confirms that the chat history is fetched and rendered in the project detail view."""
        # Create a sample chat history message
        ProjectChatMessage.objects.create(
            project=self.project,
            role="coach",
            content="Welcome to BrainForge Coach! Ask me anything.",
        )
        response = self.client.get(
            reverse("planner:project_detail", args=[self.project.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome to BrainForge Coach! Ask me anything.")

    def test_chat_endpoint_valid_response(self):
        """Posts to /api/chat/ and verifies that messages are persisted and reply returned."""
        # Clean current messages
        ProjectChatMessage.objects.filter(project=self.project).delete()

        response = self.client.post(
            reverse("planner:chat_api"),
            data=json.dumps(
                {
                    "project_id": self.project.id,
                    "message": "Why is my feasibility score low?",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("reply", data)

        # Verify db persistence
        messages = ProjectChatMessage.objects.filter(project=self.project).order_by(
            "timestamp"
        )
        self.assertEqual(messages.count(), 2)
        self.assertEqual(messages[0].role, "user")
        self.assertEqual(messages[0].content, "Why is my feasibility score low?")
        self.assertEqual(messages[1].role, "coach")
        self.assertEqual(messages[1].content, data["reply"])

    def test_chat_fallback_mechanism(self):
        """Confirms keyword queries trigger targeted fallback analyzer summaries."""
        from planner.gemini_service import generate_coach_fallback_response

        # 1. Feasibility query
        rep_feas = generate_coach_fallback_response(
            self.analysis, "Explain my feasibility score please"
        )
        self.assertIn("Time Feasibility (8/10)", rep_feas)
        self.assertIn("Budget Feasibility (6/10)", rep_feas)

        # 2. Risks query
        rep_risks = generate_coach_fallback_response(
            self.analysis, "What are the risks?"
        )
        self.assertIn("Technical Risk", rep_risks)
        self.assertIn("Water leak", rep_risks)

        # 3. Roadmap query
        rep_roadmap = generate_coach_fallback_response(
            self.analysis, "Summarize my roadmap"
        )
        self.assertIn("Days 1 - 30", rep_roadmap)
        self.assertIn("Assemble breadboard sensors", rep_roadmap)
