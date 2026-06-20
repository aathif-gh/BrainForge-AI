from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.db import transaction
import logging
import datetime
from io import BytesIO

import json
from .models import UserProject, ProjectAnalysis, ProjectChatMessage
from .gemini_service import generate_project_analysis, generate_coach_response

# ReportLab Imports for PDF Generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

logger = logging.getLogger(__name__)


def index_view(request):
    """
    Renders the landing page / dashboard, listing all user projects.
    """
    projects = UserProject.objects.all()
    return render(
        request,
        "planner/dashboard.html",
        {"projects": projects, "active_project": None},
    )


def project_detail_view(request, pk):
    """
    Renders the detailed AI planning analysis for a specific project.
    """
    projects = UserProject.objects.all()
    project = get_object_or_404(UserProject, pk=pk)

    # Fetch or verify the analysis exists
    analysis = getattr(project, "analysis", None)
    chat_history = project.chat_messages.all().order_by("timestamp")

    return render(
        request,
        "planner/project_detail.html",
        {
            "projects": projects,
            "active_project": project,
            "analysis": analysis,
            "chat_history": chat_history,
        },
    )


@require_POST
def create_project_view(request):
    """
    AJAX endpoint to analyze and create a new project.
    """
    idea_name = request.POST.get("idea_name", "").strip()
    description = request.POST.get("description", "").strip()
    time_available_str = request.POST.get("time_available", "").strip()
    budget_str = request.POST.get("budget", "").strip()
    skills = request.POST.get("skills", "").strip()
    goal = request.POST.get("goal", "").strip()

    # Form Validation
    errors = {}
    if not idea_name:
        errors["idea_name"] = "Idea name is required."
    if not description:
        errors["description"] = "Description is required."

    try:
        time_available = int(time_available_str)
        if time_available <= 0:
            errors["time_available"] = "Time must be a positive number."
    except ValueError:
        errors["time_available"] = "Time must be a valid integer."

    try:
        budget = float(budget_str)
        if budget < 0:
            errors["budget"] = "Budget cannot be negative."
    except ValueError:
        errors["budget"] = "Budget must be a valid number."

    if not skills:
        errors["skills"] = "Skills field is required."
    if not goal:
        errors["goal"] = "Goal/outcome is required."

    if errors:
        return JsonResponse({"status": "error", "errors": errors}, status=400)

    try:
        # 1. Call Gemini API first (before saving to DB, so we don't save orphans on API errors)
        analysis_data = generate_project_analysis(
            idea_name=idea_name,
            description=description,
            time_available=time_available,
            budget=budget,
            skills=skills,
            goal=goal,
        )

        # 2. Save to database in an atomic transaction
        with transaction.atomic():
            project = UserProject.objects.create(
                idea_name=idea_name,
                description=description,
                time_available=time_available,
                budget=budget,
                skills=skills,
                goal=goal,
            )

            feasibility = analysis_data.get("feasibility", {})
            risks = analysis_data.get("risks", {})
            scenarios = analysis_data.get("scenarios", {})
            roadmap = analysis_data.get("roadmap", {})

            # Extract scores
            time_score = int(feasibility.get("time_score", 5))
            budget_score = int(feasibility.get("budget_score", 5))
            skill_score = int(feasibility.get("skill_score", 5))
            risk_level = int(analysis_data.get("risk_level", 5))

            # Calculate Readiness Score
            readiness_score = int(
                (skill_score * 10) * 0.40
                + (time_score * 10) * 0.30
                + (budget_score * 10) * 0.20
                + (10 - risk_level) * 10 * 0.10
            )
            readiness_score = max(0, min(100, readiness_score))

            ProjectAnalysis.objects.create(
                project=project,
                problem_statement=analysis_data.get("problem_statement", ""),
                target_audience=analysis_data.get("target_audience", ""),
                value_proposition=analysis_data.get("value_proposition", ""),
                key_assumptions=analysis_data.get("key_assumptions", []),
                feasibility_score=feasibility,
                risks=risks,
                scenarios=scenarios,
                roadmap=roadmap,
                first_action=analysis_data.get("first_action", "Start planning today."),
                confidence_level=analysis_data.get("confidence_level", "Medium"),
                is_fallback=analysis_data.get("is_fallback", False),
                # Hackathon Fields
                readiness_score=readiness_score,
                readiness_interpretation=analysis_data.get(
                    "readiness_interpretation", "Your project shows moderate viability."
                ),
                risk_level=risk_level,
                confidence_score=int(analysis_data.get("confidence_score", 75)),
                confidence_reasoning=analysis_data.get(
                    "confidence_reasoning", "Standard alignment parameters."
                ),
                assumptions=analysis_data.get("assumptions", []),
                # Second Brain Fields
                mentor_debate_results=analysis_data.get("mentor_debate", {}),
                blind_spot_analysis=analysis_data.get("blind_spots", []),
                opportunity_cost_analysis=analysis_data.get("opportunity_cost", {}),
            )

        return JsonResponse({"status": "success", "project_id": project.id})

    except ValueError as e:
        logger.error(f"Validation or configuration error: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=400)
    except RuntimeError as e:
        logger.error(f"AI Service runtime error: {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=400)
    except Exception:
        logger.exception("Unexpected error during project creation")
        return JsonResponse(
            {
                "status": "error",
                "message": "An unexpected error occurred during AI analysis. Please try again later.",
            },
            status=500,
        )


@require_POST
def delete_project_view(request, pk):
    """
    Endpoint to delete a project from database.
    """
    project = get_object_or_404(UserProject, pk=pk)
    project.delete()
    return redirect("planner:index")


def team_details_view(request):
    """
    Renders the dedicated Team Details page.
    """
    projects = UserProject.objects.all()
    return render(
        request,
        "planner/team_details.html",
        {"projects": projects, "active_project": None},
    )


def what_if_simulate_view(request, pk):
    """
    AJAX Scenario Sandbox simulation endpoint.
    Recalculates scores based on user sliders.
    """
    project = get_object_or_404(UserProject, pk=pk)
    analysis = getattr(project, "analysis", None)
    if not analysis:
        return JsonResponse(
            {"status": "error", "message": "Analysis not found"}, status=404
        )

    try:
        # Get simulated inputs
        mod_budget = float(request.GET.get("budget", project.budget))
        mod_time = float(request.GET.get("time", project.time_available))
        team_size = int(request.GET.get("team_size", 1))
        skill_level = int(request.GET.get("skill_level", 5))
    except (ValueError, TypeError):
        return JsonResponse(
            {"status": "error", "message": "Invalid input parameters"}, status=400
        )

    # Initial Baseline Values
    init_time = int(analysis.feasibility_score.get("time_score", 5))
    init_budget = int(analysis.feasibility_score.get("budget_score", 5))
    init_skill = int(analysis.feasibility_score.get("skill_score", 5))
    init_risk = int(analysis.risk_level)

    # Recalculate Time Feasibility
    time_ratio = (
        mod_time / float(project.time_available) if project.time_available > 0 else 1.0
    )
    new_time_score = init_time * time_ratio * (1.0 + 0.1 * (team_size - 1))
    new_time_score = max(1, min(10, round(new_time_score)))

    # Recalculate Budget Feasibility
    budget_ratio = mod_budget / float(project.budget) if project.budget > 0 else 1.0
    new_budget_score = init_budget * budget_ratio
    new_budget_score = max(1, min(10, round(new_budget_score)))

    # Recalculate Skill Feasibility
    new_skill_score = skill_level

    # Recalculate Risk Level (Higher skills and team size decrease risk)
    skill_ratio = init_skill / float(new_skill_score) if new_skill_score > 0 else 1.0
    new_risk_level = init_risk * skill_ratio / (1.0 + 0.05 * (team_size - 1))
    new_risk_level = max(1, min(10, round(new_risk_level)))

    # Recalculate Readiness Score
    new_readiness = (
        (new_skill_score * 10) * 0.40
        + (new_time_score * 10) * 0.30
        + (new_budget_score * 10) * 0.20
        + (10 - new_risk_level) * 10 * 0.10
    )
    new_readiness = max(0, min(100, round(new_readiness)))

    # Readiness Category
    if new_readiness >= 71:
        new_category = "Strong Readiness"
    elif new_readiness >= 41:
        new_category = "Moderate Readiness"
    else:
        new_category = "High Risk"

    # Recalculate Success Probabilities based on readiness ratio
    readiness_ratio = (
        new_readiness / float(analysis.readiness_score)
        if analysis.readiness_score > 0
        else 1.0
    )

    init_realistic_prob = int(
        analysis.scenarios.get("realistic", {}).get("probability", 55)
    )
    init_optimistic_prob = int(
        analysis.scenarios.get("optimistic", {}).get("probability", 80)
    )
    init_pessimistic_prob = int(
        analysis.scenarios.get("pessimistic", {}).get("probability", 25)
    )

    new_realistic_prob = max(5, min(95, round(init_realistic_prob * readiness_ratio)))
    new_optimistic_prob = max(5, min(95, round(init_optimistic_prob * readiness_ratio)))
    new_pessimistic_prob = max(
        5, min(95, round(init_pessimistic_prob * (2.0 - readiness_ratio)))
    )

    # Roadmap Difficulty
    if new_readiness >= 75:
        new_difficulty = "Easy"
    elif new_readiness >= 50:
        new_difficulty = "Medium"
    elif new_readiness >= 30:
        new_difficulty = "Hard"
    else:
        new_difficulty = "Extreme"

    # Cache / Log simulation result
    log = analysis.what_if_results or []
    log.append(
        {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "inputs": {
                "budget": mod_budget,
                "time": mod_time,
                "team_size": team_size,
                "skill_level": skill_level,
            },
            "readiness_score": new_readiness,
            "difficulty": new_difficulty,
        }
    )
    analysis.what_if_results = log
    analysis.save()

    return JsonResponse(
        {
            "status": "success",
            "current": {
                "time_score": init_time,
                "budget_score": init_budget,
                "skill_score": init_skill,
                "risk_level": init_risk,
                "readiness_score": analysis.readiness_score,
                "category": (
                    "Strong Readiness"
                    if analysis.readiness_score >= 71
                    else (
                        "Moderate Readiness"
                        if analysis.readiness_score >= 41
                        else "High Risk"
                    )
                ),
                "realistic_prob": init_realistic_prob,
                "optimistic_prob": init_optimistic_prob,
                "pessimistic_prob": init_pessimistic_prob,
                "difficulty": "Medium" if analysis.readiness_score >= 50 else "Hard",
            },
            "modified": {
                "time_score": new_time_score,
                "budget_score": new_budget_score,
                "skill_score": new_skill_score,
                "risk_level": new_risk_level,
                "readiness_score": new_readiness,
                "category": new_category,
                "realistic_prob": new_realistic_prob,
                "optimistic_prob": new_optimistic_prob,
                "pessimistic_prob": new_pessimistic_prob,
                "difficulty": new_difficulty,
            },
        }
    )


def download_pdf_view(request, pk):
    """
    Generates a professional, multi-page PDF project viability report using ReportLab.
    """
    project = get_object_or_404(UserProject, pk=pk)
    analysis = getattr(project, "analysis", None)
    if not analysis:
        return HttpResponse("Analysis report not found for this project.", status=404)

    # Update PDF download history
    pdf_history = analysis.generated_pdf_history or []
    pdf_history.append(
        {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ip": request.META.get("REMOTE_ADDR", "Unknown"),
        }
    )
    analysis.generated_pdf_history = pdf_history
    analysis.save()

    # Setup PDF layout
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    # Custom Document Styles
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=30,
        textColor=colors.HexColor("#4f46e5"),
        spaceAfter=12,
    )

    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=25,
    )

    h1_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#1e1b4b"),
        spaceBefore=16,
        spaceAfter=10,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "SubSectionHeader",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#4338ca"),
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=8,
    )

    bullet_style = ParagraphStyle(
        "ReportBullet", parent=body_style, leftIndent=12, bulletIndent=4, spaceAfter=4
    )

    meta_label_style = ParagraphStyle(
        "MetaLabel",
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#475569"),
    )

    meta_value_style = ParagraphStyle(
        "MetaValue",
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0f172a"),
    )

    story = []

    # --- PAGE 1: COVER PAGE ---
    story.append(
        Paragraph(
            "<font size=16 color='#6366f1'><b>⚡ BrainForge AI</b></font>", body_style
        )
    )
    story.append(Spacer(1, 40))
    story.append(Paragraph("Project Execution &amp; Viability Report", title_style))
    story.append(
        Paragraph(
            f"Strategic analysis and milestones roadmap generated for the project: <b>{project.idea_name}</b>",
            subtitle_style,
        )
    )
    story.append(Spacer(1, 20))

    # Cover Metadata Block Table
    readiness_cat = (
        "Strong Readiness"
        if analysis.readiness_score >= 71
        else ("Moderate Readiness" if analysis.readiness_score >= 41 else "High Risk")
    )
    meta_data = [
        [
            Paragraph("<b>Project Name:</b>", meta_label_style),
            Paragraph(project.idea_name, meta_value_style),
        ],
        [
            Paragraph("<b>Core Goal:</b>", meta_label_style),
            Paragraph(project.goal, meta_value_style),
        ],
        [
            Paragraph("<b>Weekly Time Budget:</b>", meta_label_style),
            Paragraph(f"{project.time_available} Hours/Week", meta_value_style),
        ],
        [
            Paragraph("<b>Financial Budget:</b>", meta_label_style),
            Paragraph(f"${project.budget} USD", meta_value_style),
        ],
        [
            Paragraph("<b>Readiness Score:</b>", meta_label_style),
            Paragraph(
                f"<b>{analysis.readiness_score}/100</b> ({readiness_cat})",
                meta_value_style,
            ),
        ],
        [
            Paragraph("<b>Confidence Level:</b>", meta_label_style),
            Paragraph(
                f"{analysis.confidence_score}% ({analysis.confidence_level})",
                meta_value_style,
            ),
        ],
        [
            Paragraph("<b>Generated Date:</b>", meta_label_style),
            Paragraph(datetime.datetime.now().strftime("%B %d, %Y"), meta_value_style),
        ],
    ]
    t_meta = Table(meta_data, colWidths=[120, 410])
    t_meta.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
                ("PADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(t_meta)

    story.append(Spacer(1, 80))
    story.append(
        Paragraph(
            "CONFIDENTIAL | PREPARED BY BRAINFORGE AI PLANNING ENGINE",
            ParagraphStyle(
                "Conf",
                parent=body_style,
                fontName="Helvetica-Oblique",
                fontSize=8,
                textColor=colors.HexColor("#94a3b8"),
            ),
        )
    )
    story.append(PageBreak())

    # --- PAGE 2: BUSINESS CONCEPT & CLARIFICATION ---
    story.append(
        Paragraph("1. Executive Summary &amp; Concept Clarification", h1_style)
    )
    story.append(Paragraph("<b>Problem Statement:</b>", h2_style))
    story.append(Paragraph(analysis.problem_statement, body_style))
    story.append(Paragraph("<b>Target Audience:</b>", h2_style))
    story.append(Paragraph(analysis.target_audience, body_style))
    story.append(Paragraph("<b>Value Proposition:</b>", h2_style))
    story.append(Paragraph(analysis.value_proposition, body_style))
    story.append(Spacer(1, 15))

    # Feasibility Section
    story.append(Paragraph("2. Feasibility &amp; Readiness Dashboard", h1_style))
    story.append(
        Paragraph(
            f"<b>Readiness Score: {analysis.readiness_score}/100</b> (Category: <i>{readiness_cat}</i>)",
            h2_style,
        )
    )
    story.append(
        Paragraph(
            analysis.readiness_interpretation or "No custom assessment available.",
            body_style,
        )
    )

    feas_table = [
        ["Feasibility Factor", "Score", "Venture Advisory Rationale"],
        [
            "Time Feasibility",
            f"{analysis.feasibility_score.get('time_score')}/10",
            analysis.feasibility_score.get("time_rationale"),
        ],
        [
            "Budget Feasibility",
            f"{analysis.feasibility_score.get('budget_score')}/10",
            analysis.feasibility_score.get("budget_rationale"),
        ],
        [
            "Skill Feasibility",
            f"{analysis.feasibility_score.get('skill_score')}/10",
            analysis.feasibility_score.get("skill_rationale"),
        ],
        [
            "Risk Assessment",
            f"{analysis.risk_level}/10",
            "General difficulty index factoring complexity, skill levels and resource availability.",
        ],
    ]
    t_feas = Table(feas_table, colWidths=[110, 50, 370])
    t_feas.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f8fafc")],
                ),
            ]
        )
    )
    story.append(t_feas)
    story.append(PageBreak())

    # --- PAGE 3: HIDDEN ASSUMPTIONS & RISKS ---
    story.append(Paragraph("3. Hidden Assumptions Analysis", h1_style))
    story.append(
        Paragraph(
            "The key hypotheses that must be validated to protect execution resources:",
            body_style,
        )
    )

    ass_list = analysis.assumptions or []
    if not ass_list:
        ass_list = [
            {
                "category": "User",
                "assumption": "Users will upload resumes regularly.",
                "risk": "Medium",
                "explanation": "Users find manual uploads tedious.",
                "validation_recommendation": "Survey 20 target users.",
            }
        ]

    ass_table_data = [
        [
            "Category",
            "Hypothesis / Assumption",
            "Risk",
            "Explanation",
            "Validation Recommendation",
        ]
    ]
    for item in ass_list:
        ass_table_data.append(
            [
                item.get("category", "User"),
                Paragraph(item.get("assumption", ""), body_style),
                item.get("risk", "Medium"),
                Paragraph(item.get("explanation", ""), body_style),
                Paragraph(item.get("validation_recommendation", ""), body_style),
            ]
        )
    t_ass = Table(ass_table_data, colWidths=[65, 115, 50, 140, 160])
    t_ass.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8b5cf6")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f8fafc")],
                ),
            ]
        )
    )
    story.append(t_ass)
    story.append(Spacer(1, 15))

    # Risks Section
    story.append(Paragraph("4. Risk Assessment &amp; Mitigation Roadmap", h1_style))
    risks_table = [
        [
            "Risk Area",
            "Adverse Roadblock / Threat Description",
            "Proactive Mitigation Strategy",
        ],
        [
            "Technical",
            analysis.risks.get("technical", {}).get("description", ""),
            analysis.risks.get("technical", {}).get("mitigation", ""),
        ],
        [
            "Resource",
            analysis.risks.get("resource", {}).get("description", ""),
            analysis.risks.get("resource", {}).get("mitigation", ""),
        ],
        [
            "Market",
            analysis.risks.get("market", {}).get("description", ""),
            analysis.risks.get("market", {}).get("mitigation", ""),
        ],
        [
            "Skills Gap",
            analysis.risks.get("skills", {}).get("description", ""),
            analysis.risks.get("skills", {}).get("mitigation", ""),
        ],
    ]
    t_risk = Table(risks_table, colWidths=[80, 225, 225])
    t_risk.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3b82f6")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f8fafc")],
                ),
            ]
        )
    )
    story.append(t_risk)
    story.append(PageBreak())

    # --- PAGE 4: SCENARIOS, CONFIDENCE & ROADMAP ---
    story.append(Paragraph("5. Scenario Simulations &amp; Risk Metrics", h1_style))
    scen_data = [
        [
            "Scenario Mode",
            "Success Prob.",
            "Target Outcome Description",
            "Main Success Drivers",
        ],
        [
            "Optimistic",
            f"{analysis.scenarios.get('optimistic', {}).get('probability')}%",
            Paragraph(
                analysis.scenarios.get("optimistic", {}).get("outcome", ""), body_style
            ),
            Paragraph(
                ", ".join(analysis.scenarios.get("optimistic", {}).get("factors", [])),
                body_style,
            ),
        ],
        [
            "Realistic",
            f"{analysis.scenarios.get('realistic', {}).get('probability')}%",
            Paragraph(
                analysis.scenarios.get("realistic", {}).get("outcome", ""), body_style
            ),
            Paragraph(
                ", ".join(analysis.scenarios.get("realistic", {}).get("factors", [])),
                body_style,
            ),
        ],
        [
            "Pessimistic",
            f"{analysis.scenarios.get('pessimistic', {}).get('probability')}%",
            Paragraph(
                analysis.scenarios.get("pessimistic", {}).get("outcome", ""), body_style
            ),
            Paragraph(
                ", ".join(analysis.scenarios.get("pessimistic", {}).get("factors", [])),
                body_style,
            ),
        ],
    ]
    t_scen = Table(scen_data, colWidths=[90, 80, 190, 170])
    t_scen.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#06b6d4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f8fafc")],
                ),
            ]
        )
    )
    story.append(t_scen)
    story.append(Spacer(1, 10))

    # Confidence Area
    story.append(Paragraph("6. Confidence &amp; Disclaimer Panel", h1_style))
    story.append(
        Paragraph(
            f"<b>AI Recommendation Confidence: {analysis.confidence_score}% ({analysis.confidence_level})</b>",
            h2_style,
        )
    )
    story.append(
        Paragraph(
            analysis.confidence_reasoning
            or "Standard analysis based on user inputs consistency.",
            body_style,
        )
    )
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "<i>Disclaimer: BrainForge AI provides decision-support insights, not final decisions. Users remain responsible for all execution choices.</i>",
            ParagraphStyle(
                "Dis",
                parent=body_style,
                fontName="Helvetica-Oblique",
                fontSize=8.5,
                textColor=colors.HexColor("#64748b"),
            ),
        )
    )
    story.append(Spacer(1, 10))

    # Roadmap Area
    story.append(Paragraph("7. 30/60/90 Day Execution Roadmap", h1_style))

    story.append(
        Paragraph(
            "<b>Days 1 - 30 (Milestone: "
            + analysis.roadmap.get("day_30", {}).get("milestone", "")
            + ")</b>",
            h2_style,
        )
    )
    for t in analysis.roadmap.get("day_30", {}).get("tasks", []):
        story.append(Paragraph(f"• {t}", bullet_style))

    story.append(
        Paragraph(
            "<b>Days 31 - 60 (Milestone: "
            + analysis.roadmap.get("day_60", {}).get("milestone", "")
            + ")</b>",
            h2_style,
        )
    )
    for t in analysis.roadmap.get("day_60", {}).get("tasks", []):
        story.append(Paragraph(f"• {t}", bullet_style))

    story.append(
        Paragraph(
            "<b>Days 61 - 90 (Milestone: "
            + analysis.roadmap.get("day_90", {}).get("milestone", "")
            + ")</b>",
            h2_style,
        )
    )
    for t in analysis.roadmap.get("day_90", {}).get("tasks", []):
        story.append(Paragraph(f"• {t}", bullet_style))
    story.append(Spacer(1, 15))

    # First Action
    story.append(Paragraph("8. Immediate Next Action", h1_style))
    story.append(
        Paragraph(
            "<b>Today's recommended next step:</b>",
            ParagraphStyle(
                "TodayH",
                fontName="Helvetica-Bold",
                fontSize=10,
                leading=13,
                textColor=colors.HexColor("#b91c1c"),
            ),
        )
    )
    story.append(
        Paragraph(
            f'"{analysis.first_action}"',
            ParagraphStyle(
                "TodayA",
                parent=body_style,
                fontName="Helvetica-BoldOblique",
                fontSize=10.5,
                leading=14,
                textColor=colors.HexColor("#0f172a"),
            ),
        )
    )
    story.append(Spacer(1, 15))

    # Page Break for Second Brain Capabilities
    story.append(PageBreak())

    # --- PAGE 5: SECOND BRAIN - AI DEBATE ---
    story.append(Paragraph("9. Multi-Perspective AI Debate", h1_style))
    story.append(
        Paragraph(
            "<i>Alternative perspectives are generated to encourage critical thinking and should not be interpreted as definitive advice.</i>",
            ParagraphStyle(
                "DebateSub",
                parent=body_style,
                fontName="Helvetica-Oblique",
                fontSize=8.5,
                textColor=colors.HexColor("#b91c1c"),
                spaceAfter=12,
            ),
        )
    )

    debate = analysis.mentor_debate_results or {}

    # Builder Card Table
    builder_data = [
        [
            Paragraph(
                "<b>Builder Viewpoint (Execution &amp; MVP Speed)</b>",
                ParagraphStyle(
                    "BH", fontName="Helvetica-Bold", fontSize=10, textColor=colors.white
                ),
            ),
            "",
        ],
        [
            Paragraph("<b>Recommendation:</b>", meta_label_style),
            Paragraph(
                debate.get("builder", {}).get("recommendation", "Start building MVP."),
                body_style,
            ),
        ],
        [
            Paragraph("<b>Main Concern:</b>", meta_label_style),
            Paragraph(
                debate.get("builder", {}).get("concern", "Losing speed."), body_style
            ),
        ],
        [
            Paragraph("<b>Suggested Next Step:</b>", meta_label_style),
            Paragraph(
                debate.get("builder", {}).get("next_step", "Draft flow."), body_style
            ),
        ],
    ]
    t_builder = Table(builder_data, colWidths=[130, 400])
    t_builder.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
                ("SPAN", (0, 0), (1, 0)),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("PADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(t_builder)
    story.append(Spacer(1, 10))

    # Investor Card Table
    investor_data = [
        [
            Paragraph(
                "<b>Investor Viewpoint (Viability &amp; Risk)</b>",
                ParagraphStyle(
                    "IH", fontName="Helvetica-Bold", fontSize=10, textColor=colors.white
                ),
            ),
            "",
        ],
        [
            Paragraph("<b>Recommendation:</b>", meta_label_style),
            Paragraph(
                debate.get("investor", {}).get(
                    "recommendation", "Validate market demand."
                ),
                body_style,
            ),
        ],
        [
            Paragraph("<b>Main Concern:</b>", meta_label_style),
            Paragraph(
                debate.get("investor", {}).get("concern", "Financial risk."), body_style
            ),
        ],
        [
            Paragraph("<b>Suggested Next Step:</b>", meta_label_style),
            Paragraph(
                debate.get("investor", {}).get("next_step", "Survey users."), body_style
            ),
        ],
    ]
    t_investor = Table(investor_data, colWidths=[130, 400])
    t_investor.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8b5cf6")),
                ("SPAN", (0, 0), (1, 0)),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("PADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(t_investor)
    story.append(Spacer(1, 10))

    # Engineer Card Table
    engineer_data = [
        [
            Paragraph(
                "<b>Engineer Viewpoint (Feasibility &amp; Complexity)</b>",
                ParagraphStyle(
                    "EH", fontName="Helvetica-Bold", fontSize=10, textColor=colors.white
                ),
            ),
            "",
        ],
        [
            Paragraph("<b>Recommendation:</b>", meta_label_style),
            Paragraph(
                debate.get("engineer", {}).get(
                    "recommendation", "Technical architecture scoping."
                ),
                body_style,
            ),
        ],
        [
            Paragraph("<b>Main Concern:</b>", meta_label_style),
            Paragraph(
                debate.get("engineer", {}).get("concern", "Technical debt / gaps."),
                body_style,
            ),
        ],
        [
            Paragraph("<b>Suggested Next Step:</b>", meta_label_style),
            Paragraph(
                debate.get("engineer", {}).get("next_step", "Define API integration."),
                body_style,
            ),
        ],
    ]
    t_engineer = Table(engineer_data, colWidths=[130, 400])
    t_engineer.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#06b6d4")),
                ("SPAN", (0, 0), (1, 0)),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("PADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(t_engineer)
    story.append(Spacer(1, 12))

    # Agreement / Disagreement / Tradeoff
    story.append(Paragraph("<b>Areas of Agreement:</b>", h2_style))
    story.append(
        Paragraph(debate.get("agreement", "No explicit alignment mapped."), body_style)
    )
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Areas of Disagreement:</b>", h2_style))
    story.append(
        Paragraph(
            debate.get("disagreement", "No explicit conflicts mapped."), body_style
        )
    )
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Tradeoff Summary:</b>", h2_style))
    story.append(
        Paragraph(
            debate.get("tradeoff_summary", "No tradeoffs summarized."), body_style
        )
    )

    story.append(PageBreak())

    # --- PAGE 6: SECOND BRAIN - BLIND SPOTS & OPPORTUNITY COST ---
    story.append(Paragraph("10. Cognitive Blind Spot Analysis", h1_style))
    story.append(
        Paragraph(
            "Cognitive blind spot weaknesses identified inside the project assumptions:",
            body_style,
        )
    )
    story.append(Spacer(1, 6))

    blind_spots = analysis.blind_spot_analysis or []
    if not blind_spots:
        blind_spots = [
            {
                "name": "Missing User Validation",
                "impact": "High",
                "explanation": "The plan lacks surveys/interviews.",
                "recommendation": "Interview 5 adopters.",
            }
        ]

    bs_table_data = [
        [
            "Blind Spot Name",
            "Impact Level",
            "Explanation &amp; Threat",
            "Mitigation / Recommendation",
        ]
    ]
    for item in blind_spots:
        bs_table_data.append(
            [
                Paragraph(f"<b>{item.get('name', '')}</b>", body_style),
                item.get("impact", "Medium"),
                Paragraph(item.get("explanation", ""), body_style),
                Paragraph(item.get("recommendation", ""), body_style),
            ]
        )
    t_bs = Table(bs_table_data, colWidths=[120, 60, 175, 175])
    t_bs.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f97316")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f8fafc")],
                ),
            ]
        )
    )
    story.append(t_bs)
    story.append(Spacer(1, 15))

    # Opportunity Cost Section
    story.append(Paragraph("11. Opportunity Cost Analysis", h1_style))
    opp = analysis.opportunity_cost_analysis or {}
    story.append(
        Paragraph(
            f"<b>Net Opportunity Score: {opp.get('net_opportunity_score', 50)}/100</b>",
            h2_style,
        )
    )
    story.append(Spacer(1, 4))

    # Benefits & Sacrifices Comparison Table
    opp_benefits = opp.get("benefits", [])
    opp_missed = opp.get("missed_opportunities", [])

    max_len = max(len(opp_benefits), len(opp_missed))
    opp_table_data = [
        ["Potential Benefits / Gained", "Potential Sacrifices / Missed Opportunities"]
    ]
    for i in range(max_len):
        b_text = opp_benefits[i] if i < len(opp_benefits) else ""
        m_text = opp_missed[i] if i < len(opp_missed) else ""
        opp_table_data.append(
            [
                Paragraph(f"• {b_text}" if b_text else "", body_style),
                Paragraph(f"• {m_text}" if m_text else "", body_style),
            ]
        )

    t_opp = Table(opp_table_data, colWidths=[265, 265])
    t_opp.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#10b981")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f8fafc")],
                ),
            ]
        )
    )
    story.append(t_opp)
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Opportunity Cost Summary:</b>", h2_style))
    story.append(Paragraph(opp.get("summary", "No summary generated."), body_style))
    story.append(Spacer(1, 15))

    # Build Document
    doc.build(story)

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="{project.idea_name.replace(" ", "_")}_viability_report.pdf"'
    )
    response.write(pdf)
    return response


def load_hackathon_demo_view(request):
    """
    Pitch Demo Mode endpoint: Seeds the database with the "AI Resume Analyzer"
    startup project pre-populated with realistic, rich feasibility parameters.
    """
    with transaction.atomic():
        project = UserProject.objects.create(
            idea_name="AI Resume Analyzer",
            description="An intelligent web application that analyzes uploaded resumes against job descriptions, identifies skill gaps, and recommends validation steps to increase hireability.",
            time_available=10,
            budget=5000.00,
            skills="Python, Machine Learning, HTML, CSS",
            goal="Launch MVP in 30 days and onboard 100 beta testers.",
        )

        ProjectAnalysis.objects.create(
            project=project,
            problem_statement="Job seekers struggle to optimize their resumes for Automated Tracking Systems (ATS) and fail to identify critical skill gaps for target job openings.",
            target_audience="College students, tech job seekers, and career changers.",
            value_proposition="Instantly scan resumes against any job posting, receive a compatibility score, and get automated recommendations for projects/learning to fill skill gaps.",
            key_assumptions=[
                "Users will upload resumes regularly.",
                "Recruiters will value ATS-optimized resumes.",
                "A 10-hour weekly commitment is sufficient for a basic prototype.",
            ],
            feasibility_score={
                "time_score": 8,
                "time_rationale": "10 hours/week is solid for building a simple wrapper around a parser.",
                "budget_score": 9,
                "budget_rationale": "$5000 is ample for basic cloud hosting and free tier API usage.",
                "skill_score": 9,
                "skill_rationale": "Python and ML skills match the parsing backend requirements perfectly.",
                "overall_score": 9,
                "overall_rationale": "Highly feasible. Constraints are well-matched to the scope of an MVP.",
            },
            risks={
                "technical": {
                    "description": "Parsing multi-column PDF layouts accurately.",
                    "mitigation": "Use standard PDF extraction libraries and parse plain text keywords first.",
                },
                "resource": {
                    "description": "Running out of API tokens on third-party parsing services.",
                    "mitigation": "Caching results and implementing local parsing logic for common keywords.",
                },
                "market": {
                    "description": "Low resume uploads if user onboarding takes too long.",
                    "mitigation": "Implement a 1-click drag-and-drop landing page without requiring early signups.",
                },
                "skills": {
                    "description": "Lack of experience in advanced UX/UI styling details.",
                    "mitigation": "Use professional pre-built clean layouts and vanilla styling frameworks.",
                },
            },
            scenarios={
                "optimistic": {
                    "outcome": "Working MVP in 3 weeks, onboarding 150 users in month 1.",
                    "probability": 80,
                    "factors": ["Pre-trained models", "High student network reach"],
                },
                "realistic": {
                    "outcome": "Prototype ready in 4 weeks, with moderate signup conversion.",
                    "probability": 55,
                    "factors": ["Typical CSS adjustment delays"],
                },
                "pessimistic": {
                    "outcome": "Difficulty extracting text from complex PDFs delays launch.",
                    "probability": 25,
                    "factors": ["Underestimating parsing edge cases"],
                },
            },
            roadmap={
                "day_30": {
                    "milestone": "Define Core Concept & Launch Landing Page",
                    "tasks": [
                        "Build Django backend file-upload endpoint.",
                        "Write PDF text extraction script.",
                        "Publish clean landing page with drag-and-drop uploader.",
                    ],
                },
                "day_60": {
                    "milestone": "Feedback Scoring & Skill Recommendations",
                    "tasks": [
                        "Implement compatibility score calculation engine.",
                        "Connect resume to external learning resource recommendations.",
                        "Collect beta feedback from 20 peers.",
                    ],
                },
                "day_90": {
                    "milestone": "Launch MVP to Niche Communities",
                    "tasks": [
                        "Deploy app to server hosting.",
                        "Share in job-seeking subreddits and student groups.",
                        "Track upload counts and user retention metrics.",
                    ],
                },
            },
            first_action="Set up Django project repository and write PDF parsing test script.",
            confidence_level="High",
            is_fallback=False,
            # Hackathon additions
            readiness_score=83,
            readiness_interpretation="Your project shows exceptionally strong viability due to your direct alignment of skills (Python, ML) and the low costs of starting an AI parsing MVP within the $5000 budget.",
            risk_level=4,
            confidence_score=88,
            confidence_reasoning="High confidence due to precise skill alignment and low technical barrier to entry for the resume parser.",
            assumptions=[
                {
                    "category": "User",
                    "assumption": "Users will upload resumes regularly.",
                    "risk": "Medium",
                    "explanation": "If users don't see immediate helpful scoring insights, they won't re-upload.",
                    "validation_recommendation": "Conduct a survey with 20 target users before development.",
                },
                {
                    "category": "Market",
                    "assumption": "Job seekers are willing to trust AI recommendations for resume optimization.",
                    "risk": "Low",
                    "explanation": "Existing interest in resume builders and AI tools indicates positive market sentiment.",
                    "validation_recommendation": "Share a basic mockup in a job-seeking forum and measure click-through interest.",
                },
                {
                    "category": "Technical",
                    "assumption": "Free-tier parser libraries can extract text from 90% of resume layouts.",
                    "risk": "Medium",
                    "explanation": "Two-column tables and images can break plain text extractors.",
                    "validation_recommendation": "Run a test script against 15 different sample resume layouts.",
                },
                {
                    "category": "Resource",
                    "assumption": "$5000 budget is sufficient to host the project for the first 3 months.",
                    "risk": "Low",
                    "explanation": "Basic cloud hostings have generous free tiers or low-cost student packages.",
                    "validation_recommendation": "Set up server limits to prevent resource scaling charges.",
                },
            ],
            # Second Brain additions
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
                {
                    "name": "Underestimated Technical Complexity",
                    "impact": "Medium",
                    "explanation": "Parsing multi-column or heavily formatted resumes using free-tier parser libraries often results in garbled data.",
                    "recommendation": "Identify fallback APIs and parse standard text copies instead of raw PDF layout parsing.",
                },
            ],
            opportunity_cost_analysis={
                "benefits": [
                    "Valuable experience building a full-stack Django project using AI",
                    "Strong portfolio addition demonstrating practical startup validation",
                    "Deepening knowledge in Python file processing and parser integrations",
                ],
                "missed_opportunities": [
                    "Reduces time available to study for structured AWS/Cloud Architect certifications",
                    "Fewer hours to dedicate to preparing for technical internship interviews",
                    "Direct sacrifice of freelancing income that could be earned on secondary tasks",
                ],
                "net_opportunity_score": 75,
                "summary": "Building this project builds hands-on full-stack skills and startup experience, but it takes time away from dedicated internship prep and direct freelancing income.",
            },
        )

    return redirect("planner:project_detail", pk=project.id)


def chat_api_view(request):
    """
    Dedicated API endpoint for the context-aware BrainForge Coach chatbot.
    Accepts POST requests with project_id and message.
    """
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Only POST requests are allowed."},
            status=405,
        )

    try:
        if request.content_type == "application/json":
            data = json.loads(request.body)
            project_id = data.get("project_id")
            message = data.get("message", "").strip()
        else:
            project_id = request.POST.get("project_id")
            message = request.POST.get("message", "").strip()
    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": f"Invalid request payload: {str(e)}"},
            status=400,
        )

    if not project_id or not message:
        return JsonResponse(
            {"status": "error", "message": "Missing project_id or message."}, status=400
        )

    project = get_object_or_404(UserProject, pk=project_id)
    analysis = getattr(project, "analysis", None)
    if not analysis:
        return JsonResponse(
            {"status": "error", "message": "Project analysis does not exist yet."},
            status=400,
        )

    # 1. Save user's message
    ProjectChatMessage.objects.create(project=project, role="user", content=message)

    # 2. Fetch recent context history (up to last 15 messages)
    history = ProjectChatMessage.objects.filter(project=project).order_by("timestamp")[
        :15
    ]

    # 3. Request AI response (with offline fallback capability built-in)
    reply_content = generate_coach_response(project, message, history)

    # 4. Save coach's reply
    ProjectChatMessage.objects.create(
        project=project, role="coach", content=reply_content
    )

    return JsonResponse({"status": "success", "reply": reply_content})
