import anthropic
from models import AnalyzeRequest, StructuredAnalysis
from prompts import task_prompt

ANTHROPIC_MODEL = "claude-sonnet-4-6"
client = anthropic.Anthropic()

def call_anthropic(prompt: AnalyzeRequest):
    return client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1500,
        messages=[{"role": "user", "content": task_prompt(prompt)}],
    )


def call_anthropic_structured(prompt: AnalyzeRequest):
    return client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1500,
        temperature=0,
        tools=[{
            "name": "submit_analysis",
            "description": "Submit the CV-vs-listing analysis result",
            "input_schema": StructuredAnalysis.model_json_schema(),
        }],
        tool_choice={"type": "tool", "name": "submit_analysis"},
        messages=[{"role": "user", "content": task_prompt(prompt)}],
    )

async def call_anthropic_stream(prompt: AnalyzeRequest):
    try:
        with client.messages.stream(
                model=ANTHROPIC_MODEL,
                max_tokens=1500,
                messages=[{"role": "user", "content": task_prompt(prompt)}],
        ) as stream:
            for text in stream.text_stream:
                yield text
    except Exception as e:
        yield f"\n\n[ERROR: {e}]"

async def call_anthropic_structured_stream(prompt: AnalyzeRequest):
    try:
        with client.messages.stream(
            model=ANTHROPIC_MODEL,
            max_tokens=1500,
            temperature=0,
            tools=[{
                "name": "submit_analysis",
                "description": "Submit the CV-vs-listing analysis result",
                "input_schema": StructuredAnalysis.model_json_schema(),
            }],
            tool_choice={"type": "tool", "name": "submit_analysis"},
            messages=[{"role": "user", "content": task_prompt(prompt)}],
        ) as stream:
            for event in stream:
                if event.type == "content_block_delta" and event.delta.type == "input_json_delta":
                    yield event.delta.partial_json
    except Exception as e:
        yield f"\n\n[ERROR: {e}]"