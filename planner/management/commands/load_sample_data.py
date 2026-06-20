from django.core.management.base import BaseCommand
from planner.models import UserProject, ProjectAnalysis


class Command(BaseCommand):
    help = "Populates the database with a high-quality sample project and analysis."

    def handle(self, *args, **options):
        idea_name = "Eco-friendly Grocery Delivery App"

        # Check if project already exists to avoid duplication
        if UserProject.objects.filter(idea_name=idea_name).exists():
            self.stdout.write(
                self.style.SUCCESS("Sample project already exists in the database.")
            )
            return

        self.stdout.write("Creating sample project...")

        project = UserProject.objects.create(
            idea_name=idea_name,
            description="A hyper-local grocery delivery service that sources organic produce directly from local farms and delivers them using zero-waste, reusable packaging.",
            time_available=15,
            budget=1000.00,
            skills="Python, basic HTML/CSS, local marketing",
            goal="Secure 50 recurring local beta testers in 90 days.",
        )

        ProjectAnalysis.objects.create(
            project=project,
            problem_statement="Traditional grocery supply chains rely heavily on single-use plastic packaging and generate massive carbon emissions through centralized distribution and long-haul transport.",
            target_audience="Eco-conscious urban residents, busy parents who prefer zero-waste lifestyles, and small sustainable farming operations looking for direct-to-consumer sales.",
            value_proposition="A convenient delivery service that provides fresh, local organic produce in sanitized, reusable glass and textile packaging, delivered with optimized carbon-neutral routing.",
            key_assumptions=[
                "Local consumers are willing to pay a 10% premium for certified zero-waste packaging options.",
                "Small local farms can maintain reliable stock availability and quality standards without distributors.",
                "Reusable packaging return rates will exceed 85% to maintain profitable unit economics.",
            ],
            feasibility_score={
                "time_score": 7,
                "time_rationale": "15 hours/week is plenty of time to set up web pages and manually coordinate deliveries for the first 15-20 customers, though manual fulfillment will cap scaling.",
                "budget_score": 8,
                "budget_rationale": "$1,000 is sufficient to purchase initial glass jars, run local social ads, and cover domain and server costs, provided the founder handles all tech setup.",
                "skill_score": 7,
                "skill_rationale": "Your Python/HTML skills allow building a working mock website. Lack of logistics experience is mitigated by launching in a very narrow geographic zone.",
                "overall_score": 7,
                "overall_rationale": "Highly viable. The idea leverages existing tech skills and requires very low initial capital, enabling the business to run as a concierge MVP before scaling.",
            },
            risks={
                "technical": {
                    "description": "Building a custom multi-farm inventory and automatic route planning software with basic coding skills.",
                    "mitigation": "Avoid building complex custom features. Use a simple Django order form and manually map routes using Google Maps for the first 50 testers.",
                },
                "resource": {
                    "description": "High upfront packaging costs and packaging losses (customers keeping containers).",
                    "mitigation": "Charge a small, refundable container deposit of $5 at signup, which is credited back when they exchange empty jars on delivery.",
                },
                "market": {
                    "description": "Supply chain disruption due to seasonal changes or bad weather affecting farm yields.",
                    "mitigation": "Partner with at least 3 local farms and offer customer substitutions or a flexible 'seasonal box' menu model.",
                },
                "skills": {
                    "description": "Lack of experience in sanitary handling laws and food delivery regulations.",
                    "mitigation": "Obtain basic local food handler certificates and start exclusively with raw, uncut agricultural crops which face fewer regulatory hurdles.",
                },
            },
            scenarios={
                "optimistic": {
                    "outcome": "Reach 50 beta testers in 6 weeks. Reusable container return rates reach 95%. Positive feedback triggers local eco-blog press.",
                    "probability": 75,
                    "factors": [
                        "High demand in local neighborhood hubs",
                        "Active partnerships with community environmental groups",
                    ],
                },
                "realistic": {
                    "outcome": "Reach 50 beta testers in 12 weeks. Safe operations, steady growth, container return rate floats at 88%.",
                    "probability": 55,
                    "factors": [
                        "Word of mouth recommendations",
                        "Consistent flyer distribution at local farmer markets",
                    ],
                },
                "pessimistic": {
                    "outcome": "Only 12 customers signed up by day 90. Packaging costs eat up budget due to poor return rates (under 60%).",
                    "probability": 20,
                    "factors": [
                        "Fierce competition from standard delivery apps",
                        "High customer attrition due to container deposit friction",
                    ],
                },
            },
            roadmap={
                "day_30": {
                    "milestone": "Setup Landing Page & Sign 2 Farmer Partners",
                    "tasks": [
                        "Create a simple landing page in Django with a registration waitlist.",
                        "Visit local farmer markets to present terms and secure supply agreements.",
                        "Run a local Facebook/Instagram poll to measure interest in zero-waste packaging.",
                    ],
                },
                "day_60": {
                    "milestone": "Launch Concierge Beta for 15 Users",
                    "tasks": [
                        "Purchase 100 glass packaging jars and 50 organic cotton delivery bags.",
                        "Coordinate weekly delivery runs manually via WhatsApp orders and sheets.",
                        "Verify packaging return logistics and sanitation routines.",
                    ],
                },
                "day_90": {
                    "milestone": "Expand to 50 Recurring Beta Testers",
                    "tasks": [
                        "Integrate a basic Django order cart and credit card processing (Stripe checkout).",
                        "Optimize delivery routes using geographic clustering to minimize fuel costs.",
                        "Establish a referral program offering delivery discounts to active members.",
                    ],
                },
            },
            first_action="Visit your nearest farmer's market this weekend, introduce yourself to two local farm owners, and ask if they would support a zero-waste reseller.",
            confidence_level="High",
        )

        self.stdout.write(
            self.style.SUCCESS("Sample project and analysis successfully loaded!")
        )
