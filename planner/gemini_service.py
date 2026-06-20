import google.generativeai as genai
from django.conf import settings
import json
import logging
import warnings

# Suppress all FutureWarning alerts
warnings.filterwarnings("ignore", category=FutureWarning)

logger = logging.getLogger(__name__)


def generate_project_analysis(
    idea_name, description, time_available, budget, skills, goal
):
    """
    Calls the Gemini API to analyze a project idea and return structured planning data.
    """
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise ValueError(
            "Gemini API Key is not configured. Please set a valid GEMINI_API_KEY in the .env file."
        )

    genai.configure(api_key=api_key)

    # Use gemini-3.5-flash as the default model
    model = genai.GenerativeModel("gemini-3.5-flash")

    prompt = f"""
You are an expert startup advisor, venture strategist, and project management master.
Analyze the following user project idea and constraints, then output a structured analysis report in JSON format.

=== USER INPUTS ===
1. Idea Name: {idea_name}
2. Description: {description}
3. Time Available per Week: {time_available} hours
4. Budget: ${budget}
5. Existing Skills: {skills}
6. Goal/Outcome: {goal}

=== INSTRUCTIONS ===
Perform a detailed planning analysis based on these inputs. Your response must be a single, valid JSON object containing exactly the following structure.

JSON Structure:
{{
  "problem_statement": "A clear, concise definition of the problem being solved.",
  "target_audience": "Specific groups of people who face this problem and will use this solution.",
  "value_proposition": "The unique value this idea offers to solve the problem for the target audience.",
  "key_assumptions": [
    "Assumption 1: Core assumption about user behavior or need.",
    "Assumption 2: Technical or feasibility assumption.",
    "Assumption 3: Market or commercial assumption."
  ],
  "readiness_interpretation": "A professional Venture Strategist explanation explaining the readiness viability based on budget, skills, and weekly time.",
  "risk_level": 4,
  "confidence_score": 85,
  "confidence_reasoning": "A summary explaining the reasoning behind the confidence percentage score.",
  "assumptions": [
    {{
      "category": "User",
      "assumption": "User behavior assumption (e.g. users will upload files).",
      "risk": "Medium",
      "explanation": "Explanation of why this assumption holds risk.",
      "validation_recommendation": "Validation Step (e.g. Conduct a survey)."
    }},
    {{
      "category": "Market",
      "assumption": "Market demand assumption.",
      "risk": "High",
      "explanation": "Explanation of potential market risks.",
      "validation_recommendation": "Validation Step (e.g. Build a landing page)."
    }},
    {{
      "category": "Technical",
      "assumption": "Technical requirement assumption.",
      "risk": "Low",
      "explanation": "Explanation of complexity.",
      "validation_recommendation": "Validation Step."
    }},
    {{
      "category": "Resource",
      "assumption": "Resource availability assumption.",
      "risk": "Medium",
      "explanation": "Explanation of cost/time risks.",
      "validation_recommendation": "Validation Step."
    }}
  ],
  "feasibility": {{
    "time_score": 8,
    "time_rationale": "Explanation of why this score was given based on available hours vs project scale.",
    "budget_score": 5,
    "budget_rationale": "Explanation based on budget vs resource/hosting/development costs.",
    "skill_score": 6,
    "skill_rationale": "Explanation based on existing skills vs skill gap required for this project.",
    "overall_score": 6,
    "overall_rationale": "Synthesized feasibility score representing overall viability."
  }},
  "risks": {{
    "technical": {{
      "description": "Primary technical risk (e.g. database scaling, complex APIs, offline sync).",
      "mitigation": "How to mitigate this technical risk (e.g. use simple Django views, SQLite, start small)."
    }},
    "resource": {{
      "description": "Resource constraint risk (e.g. running out of time, server costs, software licensing).",
      "mitigation": "How to mitigate this resource risk."
    }},
    "market": {{
      "description": "Market adoption or user interest risk.",
      "mitigation": "How to mitigate this market risk (e.g. release a landing page first, run interviews)."
    }},
    "skills": {{
      "description": "Gaps between existing skills and skills needed for the project.",
      "mitigation": "Specific mitigation for learning/outsourcing the gaps."
    }}
  }},
  "scenarios": {{
    "optimistic": {{
      "outcome": "What happens if things go exceptionally well (e.g. rapid MVP build, high early conversion).",
      "probability": 80,
      "factors": ["Dedicated time allocation", "Prompt feedback from initial users", "Stable API usage"]
    }},
    "realistic": {{
      "outcome": "Most likely progress timeline and milestones achieved.",
      "probability": 55,
      "factors": ["Typical development delays", "Balancing with other life commitments", "Small budget adjustments"]
    }},
    "pessimistic": {{
      "outcome": "What happens if roadblocks occur (e.g. API changes, severe time crunch, database corruption).",
      "probability": 25,
      "factors": ["Unexpected system outages", "Loss of motivation", "Scope creep beyond MVP"]
    }}
  }},
  "roadmap": {{
    "day_30": {{
      "milestone": "Core Milestone 1 (e.g., Working Wireframe & Core DB Schema)",
      "tasks": [
        "Task 1 for the first 30 days.",
        "Task 2 for the first 30 days.",
        "Task 3 for the first 30 days."
      ]
    }},
    "day_60": {{
      "milestone": "Core Milestone 2 (e.g., MVP Core Flow & Mock Integrations)",
      "tasks": [
        "Task 1 for the second month.",
        "Task 2 for the second month.",
        "Task 3 for the second month."
      ]
    }},
    "day_90": {{
      "milestone": "Core Milestone 3 (e.g., Deploy to Beta & Collect Feedback)",
      "tasks": [
        "Task 1 for the third month.",
        "Task 2 for the third month.",
        "Task 3 for the third month."
      ]
    }}
  }},
  "first_action": "Generate exactly ONE immediate action the user should take today. Make it highly action-oriented and concrete.",
  "confidence_level": "High",
  "mentor_debate": {{
    "builder": {{
      "recommendation": "Builder's recommendation (Focus: speed, execution, MVP creation, learning by doing)",
      "concern": "Builder's main concern",
      "next_step": "Builder's suggested next step"
    }},
    "investor": {{
      "recommendation": "Investor's recommendation (Focus: market validation, viability, scalability, financial risk)",
      "concern": "Investor's main concern",
      "next_step": "Investor's suggested next step"
    }},
    "engineer": {{
      "recommendation": "Engineer's recommendation (Focus: technical feasibility, architectural complexity, resource requirements, risks)",
      "concern": "Engineer's main concern",
      "next_step": "Engineer's suggested next step"
    }},
    "agreement": "Core areas where all three experts agree",
    "disagreement": "Core areas where the experts disagree",
    "tradeoff_summary": "Tradeoff summary highlighting the conflict between speed, risk, and viability"
  }},
  "blind_spots": [
    {{
      "name": "One of: Confirmation Bias, Overconfidence, Unrealistic Timelines, Missing User Validation, Ignored Competition, Underestimated Technical Complexity, Resource Constraints",
      "impact": "High, Medium, or Low",
      "explanation": "Detailed explanation of why this blind spot exists in the project setup",
      "recommendation": "Actionable, concrete recommendation to validate or mitigate"
    }}
  ],
  "opportunity_cost": {{
    "benefits": [
      "Benefit 1 (e.g. portfolio growth, skill development, startup experience)",
      "Benefit 2",
      "Benefit 3"
    ],
    "missed_opportunities": [
      "Missed Opportunity 1 (e.g. internship preparation, certification study, freelancing income, alternative projects)",
      "Missed Opportunity 2",
      "Missed Opportunity 3"
    ],
    "net_opportunity_score": 75,
    "summary": "Summary of what opportunities are being sacrificed vs gained by choosing this project"
  }}
}}

Ensure all scores are integers between 1 and 10.
Ensure risk_level is an integer between 1 and 10.
Ensure confidence_score is an integer between 0 and 100.
Ensure success probabilities are integers between 0 and 100.
Ensure confidence_level is exactly one of 'High', 'Medium', 'Low'.
Keep rationales and descriptions concise but professional and realistic. Output ONLY valid JSON.
"""

    generation_config = {"response_mime_type": "application/json"}

    try:
        response = model.generate_content(prompt, generation_config=generation_config)
        result_text = response.text.strip()
        analysis_data = json.loads(result_text)
        analysis_data["is_fallback"] = False
        return analysis_data
    except json.JSONDecodeError as e:
        logger.error(
            f"Failed to parse Gemini JSON output: {e}. Output was: {response.text}"
        )
        raise ValueError(
            "The AI model returned an invalid response format. Please try again."
        )
    except Exception as e:
        logger.error(
            f"Error communicating with Gemini API: {e}. Falling back to mock generator."
        )
        # Check if the key is missing entirely, in which case we raise it to force configuration,
        # otherwise we fallback for quota/network errors.
        if "API Key is not configured" in str(e):
            raise ValueError(str(e))

        fallback_data = generate_mock_fallback_analysis(
            idea_name, description, time_available, budget, skills, goal
        )
        fallback_data["is_fallback"] = True
        return fallback_data


def generate_mock_fallback_analysis(
    idea_name, description, time_available, budget, skills, goal
):
    """
    Generates a high-quality, customized mock analysis when the Gemini API is rate-limited or out of quota.
    """
    return {
        "problem_statement": f"Friction and inefficiencies in executing '{idea_name}' due to high entry barriers, resource limitations, and planning complexity.",
        "target_audience": f"Early adopters and consumers of '{idea_name}' who experience the core frustration of: '{description[:80]}...'",
        "value_proposition": f"A streamlined approach to '{idea_name}' leveraging your existing skills ('{skills}') to achieve the milestone of '{goal}' efficiently.",
        "key_assumptions": [
            f"Target users are actively looking for a simplified solution like '{idea_name}'.",
            f"The goal of '{goal}' can be successfully prototyped within a budget of ${budget}.",
            f"Allocating {time_available} hours per week is sufficient to construct and test the initial core flow.",
        ],
        "readiness_interpretation": f"Your project shows moderate readiness. Leveraging skills like '{skills}' provides a strong head start, but the constraints of {time_available} hours/week and a budget of ${budget} will require disciplined scoping to launch in a reasonable timeframe.",
        "risk_level": 5,
        "confidence_score": 78,
        "confidence_reasoning": f"Based on the alignment of skills ('{skills}') and budget constraints (${budget}), standard parameters indicate moderate execution confidence.",
        "assumptions": [
            {
                "category": "User",
                "assumption": f"Target users will actively engage with '{idea_name}' on a weekly basis.",
                "risk": "Medium",
                "explanation": "Retention can drop off rapidly if the user onboarding is complex or lacks immediate value.",
                "validation_recommendation": f"Conduct user interviews with 5 potential adopters of '{idea_name}' to map their expectations.",
            },
            {
                "category": "Market",
                "assumption": f"There is sufficient commercial demand to validate the budget of ${budget}.",
                "risk": "Medium",
                "explanation": "Competitors might satisfy the general need, making user acquisition costly.",
                "validation_recommendation": "Publish a landing page describing the product and track the email sign-up conversion rate.",
            },
            {
                "category": "Technical",
                "assumption": f"Your current skills ('{skills}') are sufficient to implement the core product.",
                "risk": "Low",
                "explanation": f"The core components align with your skills ('{skills}'). Minimal third-party API dependencies keep complexity low.",
                "validation_recommendation": "Draft a system architecture map and test connections to necessary external API services.",
            },
            {
                "category": "Resource",
                "assumption": f"Allocating {time_available} hours/week is sufficient to build and launch the project.",
                "risk": "High",
                "explanation": "Balancing execution with other professional or personal commitments frequently causes milestone delays.",
                "validation_recommendation": "Break the first month down into 4 weekly sub-milestones and track hours spent on each.",
            },
        ],
        "feasibility": {
            "time_score": 7 if time_available >= 10 else 4,
            "time_rationale": f"An allocation of {time_available} hours per week allows steady progress for a solo builder, though scaling will require operations optimization.",
            "budget_score": 8 if budget >= 1000 else (5 if budget >= 250 else 3),
            "budget_rationale": f"A budget of ${budget} is sufficient to buy hosting, glass packaging or standard APIs, but limits outsourcing custom developer labor.",
            "skill_score": 7,
            "skill_rationale": f"Leveraging your skills ('{skills}') provides a strong setup. Online code repositories or templates will fill initial technical gaps.",
            "overall_score": 7,
            "overall_rationale": "Viability is positive. Commencing with a manual concierge service or a mockup fits your constraints perfectly and minimizes early risks.",
        },
        "risks": {
            "technical": {
                "description": f"Over-engineering the technical structure of '{idea_name}' beyond the required prototype scope.",
                "mitigation": "Launch as a single-page responsive web app first, using standard templates and manual database records.",
            },
            "resource": {
                "description": f"Running out of cash within the ${budget} budget or burning out with only {time_available} hours/week.",
                "mitigation": "Define a strict list of features and focus solely on the most important core capability.",
            },
            "market": {
                "description": f"Lack of demand or failure to interest the target audience in '{idea_name}'.",
                "mitigation": "Before coding, conduct interviews with 5 potential users to validate the primary value proposition.",
            },
            "skills": {
                "description": f"Gaps in technical implementation for '{description[:40]}...'",
                "mitigation": "Use no-code automation integrations (e.g., Zapier) to handle database workflows initially.",
            },
        },
        "scenarios": {
            "optimistic": {
                "outcome": f"Successfully launch the prototype, securing '{goal}' within the first 6 weeks.",
                "probability": 75,
                "factors": [
                    "High demand in local networks",
                    "Flawless tool integrations",
                    "Zero critical bugs",
                ],
            },
            "realistic": {
                "outcome": f"Achieve '{goal}' in 10-12 weeks with typical learning delays and adjustments.",
                "probability": 50,
                "factors": [
                    "Balancing commitments with secondary work",
                    "Step-by-step user feedback integration",
                ],
            },
            "pessimistic": {
                "outcome": f"Slow onboarding and high friction, resulting in under 10% of '{goal}' completed by day 90.",
                "probability": 25,
                "factors": [
                    "Scope creep beyond basic prototype",
                    "High user drop-off during onboarding",
                ],
            },
        },
        "roadmap": {
            "day_30": {
                "milestone": "Define Core Concept & Launch Landing Page",
                "tasks": [
                    f"Create a simple landing page explaining the core benefits of '{idea_name}'.",
                    "Share the signup link with 10 potential users in your target audience.",
                    "Collect feedback and compile a prioritised list of feature requests.",
                ],
            },
            "day_60": {
                "milestone": "Implement Core Functionality & Test Run",
                "tasks": [
                    f"Assemble a manual mockup of '{idea_name}' using basic Django and SQLite.",
                    "Onboard the first 5 beta users to test the delivery loop.",
                    "Manually resolve errors and adjust layout based on active usage.",
                ],
            },
            "day_90": {
                "milestone": f"Scale & Achieve Primary Goal: '{goal}'",
                "tasks": [
                    "Integrate payment links or feedback forms on the active dashboard.",
                    "Run marketing campaigns in niche communities where target users hang out.",
                    "Analyze conversion metrics to determine whether to pivot or scale up.",
                ],
            },
        },
        "first_action": f"Draft a simple layout document outlining target features of '{idea_name}' and share it with 3 peers today.",
        "confidence_level": "Medium",
        "mentor_debate": {
            "builder": {
                "recommendation": f"Start building the MVP for '{idea_name}' immediately using standard templates and tools you already know.",
                "concern": "Losing momentum by spending too much time on planning and market research.",
                "next_step": "Draft a single core flow wireframe and write a basic repository script today.",
            },
            "investor": {
                "recommendation": f"Validate that users will actually pay or sign up for '{idea_name}' before writing any code.",
                "concern": "Low market size, high user drop-off, or spending resources on a product that nobody wants.",
                "next_step": "Create a landing page describing your value proposition and track email signups.",
            },
            "engineer": {
                "recommendation": f"Simplify the technical architecture to fit your existing skills ('{skills}') and budget (${budget}).",
                "concern": "Underestimating integration complexity or building custom features that could be resolved with simpler APIs.",
                "next_step": "Select hosting options and test basic API integrations.",
            },
            "agreement": "All three perspectives agree that starting small, minimizing early costs, and focusing on a single core feature is critical for an MVP.",
            "disagreement": "The Builder wants to start coding immediately; the Investor insists on market validation first; the Engineer wants to focus on architectural scoping and testing first.",
            "tradeoff_summary": "Starting coding immediately helps you learn faster, but carries the risk of building the wrong features. Taking time to validate the market reduces financial risk but delays your prototype launch.",
        },
        "blind_spots": [
            {
                "name": "Missing User Validation",
                "impact": "High",
                "explanation": f"The description of '{idea_name}' assumes target users will download and use the product regularly, but provides no active validation evidence.",
                "recommendation": "Interview at least 5 target users about their current workflow and frustrations before coding.",
            },
            {
                "name": "Unrealistic Timelines",
                "impact": "Medium",
                "explanation": f"Building '{idea_name}' with only {time_available} hours per week could lead to launch delays if you don't scope down features aggressively.",
                "recommendation": "List all features and remove 50% of them to build a strict 1-feature MVP.",
            },
        ],
        "opportunity_cost": {
            "benefits": [
                "Hands-on experience building a real product in Django",
                "Developing startup logic and business validation skills",
                "Adding a functional startup project to your professional portfolio",
            ],
            "missed_opportunities": [
                "Time sacrificed that could be spent preparing for technical internship interviews",
                "Fewer hours available to study for structured professional certifications",
                "Potential direct loss of freelancing or side-gig hourly income",
            ],
            "net_opportunity_score": 70,
            "summary": f"Pursuing '{idea_name}' offers a fantastic way to develop entrepreneurial skills and a practical portfolio piece, but it will consume time that could be spent on immediate certification study or internship prep.",
        },
    }


def generate_coach_response(project, message, history):
    """
    Calls the Gemini API using complete project analysis context to chat with the user.
    """
    analysis = getattr(project, "analysis", None)
    if not analysis:
        return "I do not have access to any analysis for this project yet. Please generate the project analysis first."

    # Construct complete analysis context for the AI Coach
    context = f"""You are "BrainForge Coach", an experienced, encouraging, and highly professional startup advisor and project management coach.
You are helping the user with their project idea: "{project.idea_name}".
Provide context-aware, actionable, and friendly guidance. Always write in simple, clear language.

PROJECT UNDERSTANDING:
- Description: {project.description}
- Weekly Hours Available: {project.time_available} hrs
- Cash Budget: ${project.budget} USD
- Target Goal: {project.goal}
- Skills: {project.skills}

AI VIABILITY ANALYSIS:
- Problem Statement: {analysis.problem_statement}
- Value Proposition: {analysis.value_proposition}
- Readiness Score: {analysis.readiness_score}/100
- Readiness Interpretation: {analysis.readiness_interpretation}
- Confidence Rating: {analysis.confidence_score}% ({analysis.confidence_level})
- Confidence Reasoning: {analysis.confidence_reasoning}
- Feasibility Ratios (1-10):
  * Overall: {analysis.feasibility_score.get('overall_score', 5)} ({analysis.feasibility_score.get('overall_rationale', '')})
  * Time: {analysis.feasibility_score.get('time_score', 5)} ({analysis.feasibility_score.get('time_rationale', '')})
  * Budget: {analysis.feasibility_score.get('budget_score', 5)} ({analysis.feasibility_score.get('budget_rationale', '')})
  * Skills: {analysis.feasibility_score.get('skill_score', 5)} ({analysis.feasibility_score.get('skill_rationale', '')})

RISKS & MITIGATIONS:
- Technical Risk: {analysis.risks.get('technical', {}).get('description', '')}
  * Mitigation: {analysis.risks.get('technical', {}).get('mitigation', '')}
- Resource Risk: {analysis.risks.get('resource', {}).get('description', '')}
  * Mitigation: {analysis.risks.get('resource', {}).get('mitigation', '')}
- Market Risk: {analysis.risks.get('market', {}).get('description', '')}
  * Mitigation: {analysis.risks.get('market', {}).get('mitigation', '')}
- Skills Gap Risk: {analysis.risks.get('skills', {}).get('description', '')}
  * Mitigation: {analysis.risks.get('skills', {}).get('mitigation', '')}

30/60/90 ROADMAP SUMMARY:
- 30-Day Milestone: {analysis.roadmap.get('day_30', {}).get('milestone', '')}
  Tasks: {', '.join(analysis.roadmap.get('day_30', {}).get('tasks', []))}
- 60-Day Milestone: {analysis.roadmap.get('day_60', {}).get('milestone', '')}
  Tasks: {', '.join(analysis.roadmap.get('day_60', {}).get('tasks', []))}
- 90-Day Milestone: {analysis.roadmap.get('day_90', {}).get('milestone', '')}
  Tasks: {', '.join(analysis.roadmap.get('day_90', {}).get('tasks', []))}

IMMEDIATE RECOMMENDED ACTION FOR TODAY:
"{analysis.first_action}"

SECOND BRAIN ANALYSIS:
- Debated Tradeoff Summary: {analysis.mentor_debate_results.get('tradeoff_summary', '') if analysis.mentor_debate_results else ''}
- Cognitive Blind Spots: {', '.join([s.get('name', '') + ' (' + s.get('impact', '') + ' Impact)' for s in (analysis.blind_spot_analysis or [])])}
- Net Opportunity Score: {analysis.opportunity_cost_analysis.get('net_opportunity_score', 50) if analysis.opportunity_cost_analysis else 50}/100

CONVERSATION HISTORY:
"""
    for msg in history:
        context += f"{'User' if msg.role == 'user' else 'Coach'}: {msg.content}\n"

    context += f"\nUser: {message}\nCoach:"

    api_key = getattr(settings, "GEMINI_API_KEY", "")
    if not api_key or api_key == "your_gemini_api_key_here":
        return generate_coach_fallback_response(analysis, message)

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-3.5-flash")
        response = model.generate_content(context)
        return response.text.strip()
    except Exception as e:
        logger.error(
            f"Error calling Gemini in coach: {e}. Switching to local fallback."
        )
        return generate_coach_fallback_response(analysis, message)


def generate_coach_fallback_response(analysis, message):
    """
    Formulates professional, rich context-aware responses when the Gemini API is offline/rate-limited.
    """
    if not analysis:
        return "I don't have access to your project analysis yet. Please verify it has loaded correctly."

    msg_lower = message.lower()

    if "feasibility" in msg_lower:
        time_score = analysis.feasibility_score.get("time_score", 5)
        budget_score = analysis.feasibility_score.get("budget_score", 5)
        skill_score = analysis.feasibility_score.get("skill_score", 5)
        overall_score = analysis.feasibility_score.get("overall_score", 5)

        return (
            f"Looking at your feasibility scores (Overall: {overall_score}/10):\n\n"
            f"• **Time Feasibility ({time_score}/10)**: {analysis.feasibility_score.get('time_rationale', '')}\n"
            f"• **Budget Feasibility ({budget_score}/10)**: {analysis.feasibility_score.get('budget_rationale', '')}\n"
            f"• **Skill Feasibility ({skill_score}/10)**: {analysis.feasibility_score.get('skill_rationale', '')}\n\n"
            "If some of your scores are low, consider dedicating more weekly hours, budgeting extra resources, or leveraging templates to bridge any skill gaps."
        )

    elif "risk" in msg_lower:
        tech = analysis.risks.get("technical", {})
        res = analysis.risks.get("resource", {})
        mkt = analysis.risks.get("market", {})
        skills = analysis.risks.get("skills", {})

        return (
            "Here are the key risks and mitigation strategies calculated for your project:\n\n"
            f"• **Technical Risk**: {tech.get('description', '')}\n"
            f"  *Mitigation*: {tech.get('mitigation', '')}\n\n"
            f"• **Resource Risk**: {res.get('description', '')}\n"
            f"  *Mitigation*: {res.get('mitigation', '')}\n\n"
            f"• **Market Risk**: {mkt.get('description', '')}\n"
            f"  *Mitigation*: {mkt.get('mitigation', '')}\n\n"
            f"• **Skills Gap Risk**: {skills.get('description', '')}\n"
            f"  *Mitigation*: {skills.get('mitigation', '')}"
        )

    elif "readiness" in msg_lower or "improve" in msg_lower:
        return (
            f"Your **BrainForge Readiness Score** is **{analysis.readiness_score}/100**.\n\n"
            f'Venture Advisor Rationale: *"{analysis.readiness_interpretation}"*\n\n'
            "To raise this score:\n"
            "1. **Skills (40% weight)**: Expand your technology stack or partner with a technical co-founder.\n"
            "2. **Time (30% weight)**: Free up more hours to dedicate to weekly execution.\n"
            "3. **Budget (20% weight)**: Set aside additional funds to cover hosting and standard API limits.\n"
            "4. **Risks (10% weight)**: Scope down your MVP features to lower technical risk complexity."
        )

    elif "roadmap" in msg_lower or "milestone" in msg_lower or "summarize" in msg_lower:
        day_30 = analysis.roadmap.get("day_30", {})
        day_60 = analysis.roadmap.get("day_60", {})
        day_90 = analysis.roadmap.get("day_90", {})

        tasks_30 = "\n".join([f"  - {t}" for t in day_30.get("tasks", [])])
        tasks_60 = "\n".join([f"  - {t}" for t in day_60.get("tasks", [])])
        tasks_90 = "\n".join([f"  - {t}" for t in day_90.get("tasks", [])])

        return (
            "Here is the summary of your milestones roadmap:\n\n"
            f"• **Days 1 - 30 (Milestone: {day_30.get('milestone', '')})**\n{tasks_30}\n\n"
            f"• **Days 31 - 60 (Milestone: {day_60.get('milestone', '')})**\n{tasks_60}\n\n"
            f"• **Days 61 - 90 (Milestone: {day_90.get('milestone', '')})**\n{tasks_90}"
        )

    elif "first" in msg_lower or "do first" in msg_lower or "action" in msg_lower:
        return (
            f"Your immediate next action recommended by the AI is:\n\n"
            f'**"{analysis.first_action}"**\n\n'
            "Focus strictly on this single item today to overcome analysis paralysis and start building momentum."
        )

    elif "skills" in msg_lower or "missing" in msg_lower:
        skills_gap = analysis.risks.get("skills", {})
        return (
            f"Your skill feasibility is scored at **{analysis.feasibility_score.get('skill_score', 5)}/10**.\n\n"
            f"• **Skills Gap**: {skills_gap.get('description', '')}\n"
            f"• **Mitigation**: {skills_gap.get('mitigation', '')}\n\n"
            "Using pre-built templates or leveraging no-code dashboard plugins can bridge early skill gaps."
        )

    else:
        # Default fallback summary response
        return (
            f"Hello! I am your **BrainForge Coach**. Here is a brief recap of your project planning:\n\n"
            f"• **Project**: {analysis.project.idea_name}\n"
            f"• **Readiness Score**: {analysis.readiness_score}/100\n"
            f'• **Today\'s Action**: "{analysis.first_action}"\n\n'
            "Ask me a specific question or use one of the starter prompts below!"
        )
