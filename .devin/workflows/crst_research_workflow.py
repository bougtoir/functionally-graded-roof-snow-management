import asyncio
import json
from pathlib import Path


REPO = "bougtoir/functionally-graded-roof-snow-management"
OUTPUT = Path(
    "/home/ubuntu/repos/functionally-graded-roof-snow-management/"
    "references/workflow_research_results.json"
)

REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "topic": {"type": "string"},
        "report": {"type": "string"},
        "critical_gaps": {"type": "string"},
    },
    "required": ["topic", "report", "critical_gaps"],
}

SYNTHESIS_SCHEMA = {
    "type": "object",
    "properties": {
        "journal_requirements": {"type": "string"},
        "verified_literature": {"type": "string"},
        "parameter_recommendations": {"type": "string"},
        "weather_recommendations": {"type": "string"},
        "model_risks": {"type": "string"},
        "implementation_actions": {"type": "string"},
    },
    "required": [
        "journal_requirements",
        "verified_literature",
        "parameter_recommendations",
        "weather_recommendations",
        "model_risks",
        "implementation_actions",
    ],
}

TOPICS = [
    (
        "crst-rules",
        """Verify the CURRENT official Cold Regions Science and Technology
        (Elsevier) Guide for Authors, aims/scope, article types, manuscript,
        figure/table, reference, data/code, submission-file, declarations,
        generative-AI, and cover-letter requirements. Use official Elsevier
        sources as primary evidence. Record exact URLs, page titles, access
        date, and quote or closely paraphrase the rule. Distinguish explicit
        rules from inference. Do not edit the repository.""",
    ),
    (
        "crst-literature",
        """Find recent and foundational Cold Regions Science and Technology
        papers directly relevant to roof snow load, roof snow deposition,
        sliding/shedding, snow mechanics, friction/adhesion, passive control,
        or computational modeling. Independently verify title, authors, year,
        journal, volume/pages/article number, and DOI using publisher/Crossref
        or equivalent authoritative metadata. Explain precisely which claim
        each paper supports. Do not include unverifiable references and do not
        edit the repository.""",
    ),
    (
        "japanese-retention",
        """Research Japanese snow-retention/non-shedding roof practice,
        including 無落雪屋根, plus conventional shedding roofs, snow guards,
        and active melting as comparators. Prioritize peer-reviewed Japanese
        literature, government, university, building-research, standards, and
        other authoritative sources. Verify bibliographic details and stable
        URLs/DOIs. Give technically fair treatment and identify what cannot be
        generalized globally. Do not edit the repository.""",
    ),
    (
        "snow-parameters",
        """Identify defensible sources and ranges for roof-snow density,
        static/kinetic friction, adhesion/cohesion, aging/metamorphism,
        temperature effects, sliding thresholds, rain-on-snow/refreezing, and
        roof materials. Separate measured values from modeling assumptions.
        Verify every citation and DOI. Recommend conservative nominal values
        and sensitivity ranges only where evidence supports them; otherwise
        mark the parameter as an explicit assumption. Do not edit the repo.""",
    ),
    (
        "jma-weather",
        """Determine a reproducible, openly accessible official route for
        hourly/daily Japanese weather observations suitable for multiple
        contrasting heavy-snow stations and winters. Prefer JMA official data
        and document station identifiers, variables, units, missing-value
        flags, terms/licensing, URL patterns or APIs, and transformations
        needed for snow simulation. Recommend scientifically neutral station
        and winter selection criteria. Do not edit the repository.""",
    ),
    (
        "physics-review",
        """Act as a skeptical CRST reviewer. Assess the proposed 2D cell-based
        force-balance snow-roof model and multi-objective optimization of
        maximum retained mass versus maximum single shedding event. Identify
        minimum defensible physics, validation/sanity tests, numerical
        convergence requirements, fair comparator design, optimizer metrics,
        robustness analyses, overclaim risks, and conditions under which the
        study would be publishable as a computational proof of concept. Base
        technical claims on verified literature where possible. Do not edit
        the repository.""",
    ),
]


async def research(label, prompt):
    return await agent(
        (
            f"Repository: {REPO}\n"
            "This is a read-only research task for a CRST submission project.\n"
            f"Topic: {label}\n{prompt}\n"
            "Return a compact but evidence-dense Markdown report. Include a "
            "verification table with source, identifier/DOI, claim supported, "
            "verification URL, and confidence. Never fabricate."
        ),
        phase="research",
        schema=REPORT_SCHEMA,
        label=label,
        repos=[REPO],
        soft_time_limit_minutes=35,
    )


async def main():
    await register_workflow(
        {
            "name": "crst-roof-snow-research",
            "description": (
                "Parallel verification of journal rules, literature, "
                "parameters, weather data, and model risks, followed by synthesis"
            ),
            "product": REPO,
            "soft_time_limit_minutes": 35,
            "phases": [
                {
                    "title": "research",
                    "detail": "Independent source verification",
                    "count": len(TOPICS),
                    "labels": [topic[0] for topic in TOPICS],
                },
                {
                    "title": "synthesis",
                    "detail": "Cross-check and turn research into implementation actions",
                    "count": 1,
                    "labels": ["evidence-synthesis"],
                    "soft_time_limit_minutes": 30,
                },
            ],
        }
    )
    log("Starting six independent evidence-verification tasks")
    reports = await parallel(
        [
            (lambda label=label, prompt=prompt: research(label, prompt))
            for label, prompt in TOPICS
        ]
    )
    log("Independent research complete; starting cross-source synthesis")
    synthesis = await agent(
        (
            "Synthesize the six research reports below for implementation of a "
            "submission-ready computational proof-of-concept paper for Cold "
            "Regions Science and Technology. Cross-check disagreements, reject "
            "weak or unverifiable claims, clearly separate official submission "
            "rules from recommendations, and produce actionable requirements "
            "for configs, analysis, manuscript, audits, and packaging. Do not "
            "edit the repository.\n\n"
            + json.dumps(reports, ensure_ascii=False, sort_keys=True)
        ),
        phase="synthesis",
        schema=SYNTHESIS_SCHEMA,
        label="evidence-synthesis",
        repos=[REPO],
        soft_time_limit_minutes=30,
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {"reports": reports, "synthesis": synthesis},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    log(f"Saved structured research synthesis to {OUTPUT}")


asyncio.run(main())
