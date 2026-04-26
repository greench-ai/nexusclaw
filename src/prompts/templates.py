"""
NexusClaw Prompt Templates
Pre-built prompts for common tasks: coding, research, analysis, writing, review.
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class PromptTemplate:
    name: str
    description: str
    system: str
    user_template: str
    few_shot_examples: list[dict] = None
    tags: list[str] = None

# ─────────────────────────────────────────────────────────────────
# SYSTEM PROMPTS
# ─────────────────────────────────────────────────────────────────

SYSTEM_CODER = """You are an expert programmer. You write clean, efficient, production-ready code.
Follow these rules:
1. Always handle errors gracefully
2. Add type hints to Python
3. Write tests for new code
4. Follow the project's existing style
5. Explain non-obvious decisions in comments
6. Prefer simplicity over cleverness
"""

SYSTEM_RESEARCHER = """You are a thorough researcher. You:
1. Start with broad understanding, then narrow to specifics
2. Cite your sources when possible
3. Distinguish facts from interpretations
4. Acknowledge uncertainty when present
5. Present multiple perspectives on contested topics
6. End with a summary and open questions
"""

SYSTEM_ANALYST = """You are a data analyst. You:
1. Start by understanding what the data represents
2. Look for patterns, anomalies, and correlations
3. Consider statistical significance
4. Visualize when helpful
5. Present findings clearly with context
6. Recommend next steps based on evidence
"""

SYSTEM_WRITER = """You are a skilled writer. You:
1. Match the tone and style requested
2. Structure for readability (headings, bullets, paragraphs)
3. Avoid passive voice unless necessary
4. Use concrete examples
5. Readability > impressiveness
"""

SYSTEM_REVIEWER = """You are a code reviewer. You:
1. Focus on correctness, security, and performance
2. Suggest improvements, don't just criticize
3. Approve when good enough, not perfect
4. Reference best practices and documentation
5. Be respectful and constructive
"""

# ─────────────────────────────────────────────────────────────────
# USER TEMPLATES
# ─────────────────────────────────────────────────────────────────

TEMPLATES = [
    
    PromptTemplate(
        name="code_review",
        description="Review code for bugs, security, performance",
        system=SYSTEM_CODER + "\n" + SYSTEM_REVIEWER,
        user_template="Review this code:\n\n```{language}\n{code}\n```\n\nFocus on: {focus}",
        tags=["code", "review", "security"]
    ),
    
    PromptTemplate(
        name="explain_code",
        description="Explain what code does in plain language",
        system="You are a patient teacher. Explain code clearly, step by step.",
        user_template="Explain this code:\n\n```{language}\n{code}\n```",
        tags=["code", "education"]
    ),
    
    PromptTemplate(
        name="write_tests",
        description="Write unit tests for code",
        system=SYSTEM_CODER,
        user_template="Write unit tests for:\n\n```{language}\n{code}\n```\n\nUse {framework} testing framework. Cover edge cases.",
        tags=["code", "testing"]
    ),
    
    PromptTemplate(
        name="refactor",
        description="Refactor code to be cleaner and more efficient",
        system=SYSTEM_CODER + "\nRefactor for: readability, performance, maintainability.",
        user_template="Refactor this:\n\n```{language}\n{code}\n```\n\nGoals: {goals}",
        tags=["code", "refactor"]
    ),
    
    PromptTemplate(
        name="debug",
        description="Find and fix bugs in code",
        system=SYSTEM_CODER + "\nThink systematically. Check: inputs, edge cases, state, concurrency.",
        user_template="This code has a bug. Find and fix it:\n\n```{language}\n{code}\n```\n\nError: {error}",
        tags=["code", "debug"]
    ),
    
    PromptTemplate(
        name="research_topic",
        description="Deep research on a topic",
        system=SYSTEM_RESEARCHER,
        user_template="Research: {topic}\n\nProvide: overview, key concepts, current state, open questions.",
        tags=["research"]
    ),
    
    PromptTemplate(
        name="summarize",
        description="Summarize text concisely",
        system="You summarize clearly and accurately. Include key points only.",
        user_template="Summarize this:\n\n{text}\n\nTarget length: {length} words.",
        tags=["writing", "summary"]
    ),
    
    PromptTemplate(
        name="write_email",
        description="Write a professional email",
        system=SYSTEM_WRITER,
        user_template="Write a {tone} email:\nTo: {to}\nSubject: {subject}\nPurpose: {purpose}",
        tags=["writing", "email"]
    ),
    
    PromptTemplate(
        name="analyze_data",
        description="Analyze data and find patterns",
        system=SYSTEM_ANALYST,
        user_template="Analyze this data:\n\n{data}\n\nQuestions: {questions}",
        tags=["analysis", "data"]
    ),
    
    PromptTemplate(
        name="写作助手",
        description="中文写作助手",
        system="你是一位专业的中文写作助手。请用简洁、准确、流畅的中文写作。",
        user_template="{task}\n\n要求：{requirements}",
        tags=["writing", "chinese"]
    ),
]

# Template lookup
def get_template(name: str) -> PromptTemplate | None:
    for t in TEMPLATES:
        if t.name == name:
            return t
    return None

def list_templates(tag: str = None) -> list[PromptTemplate]:
    if tag:
        return [t for t in TEMPLATES if tag in (t.tags or [])]
    return list(TEMPLATES)

def render(name: str, **kwargs) -> tuple[str, str]:
    """Render a template. Returns (system_prompt, full_prompt)."""
    t = get_template(name)
    if not t:
        raise ValueError(f"Template '{name}' not found. Available: {[x.name for x in TEMPLATES]}")
    
    system = t.system
    user = t.user_template.format(**kwargs)
    return system, user

# ─────────────────────────────────────────────────────────────────
# CHAIN TEMPLATES (multi-step)
# ─────────────────────────────────────────────────────────────────

CHAIN_SOLVE = [
    {"step": 1, "name": "understand", "prompt": "Understand the problem: {problem}\nBreak it down into parts."},
    {"step": 2, "name": "plan", "prompt": "Plan your approach to: {problem}\nList steps."},
    {"step": 3, "name": "execute", "prompt": "Execute the plan for: {problem}\nShow your work."},
    {"step": 4, "name": "review", "prompt": "Review the solution to: {problem}\nCheck for errors."},
]

CHAIN_REVIEW_PR = [
    {"step": 1, "name": "read", "prompt": "Read and understand this PR:\n\n{changes}"},
    {"step": 2, "name": "test_plan", "prompt": "What should be tested? List test cases for this PR."},
    {"step": 3, "name": "risks", "prompt": "What could go wrong? Identify risks in this PR."},
    {"step": 4, "name": "recommend", "prompt": "Recommendation: Approve / Request Changes / Comment?\nProvide reasoning."},
]

def render_chain(chain: list, **kwargs) -> list[dict]:
    """Render a chain template."""
    return [{"step": s["step"], "name": s["name"], "prompt": s["prompt"].format(**kwargs)} for s in chain]

def list_chains() -> dict:
    return {"solve": CHAIN_SOLVE, "review_pr": CHAIN_REVIEW_PR}
