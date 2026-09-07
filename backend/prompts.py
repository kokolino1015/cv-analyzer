from models import AnalyzeRequest


def task_prompt(req: AnalyzeRequest) -> str:
    return (
        "Compare this CV against this job listing.\n"
        "Identify: 1) matched requirements, 2) missing requirements, "
        "3) a match score 0-100, 4) two concrete suggestions to improve the match.\n\n"
        f"CV:\n{req.cv_text}\n\nJOB LISTING:\n{req.job_listing}"
    )


def json_prompt(req: AnalyzeRequest) -> str:
    return (
        "Respond with ONLY a valid JSON object — no markdown, no code fences, no text "
        'before or after — in exactly this structure: {"score": <integer 0-100>, '
        '"matched": [<strings>], "missing": [<strings>], "suggestions": [<strings>]}.\n\n'
        + task_prompt(req)
    )