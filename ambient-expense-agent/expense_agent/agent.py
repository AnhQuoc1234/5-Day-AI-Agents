from google.adk.workflow import Workflow, node
from google.adk.agents import LlmAgent
from google.adk.agents.context import Context
from google.adk.events.event import Event
from google.adk.events.request_input import RequestInput
from google.adk.apps import App
from pydantic import BaseModel
import base64
import json
import logging
import re

logger = logging.getLogger(__name__)

# --- Configuration ---
EXPENSE_THRESHOLD = 100.0
MODEL_NAME = "gemini-3.1-flash-lite"

# --- Schemas ---
class ExpenseReport(BaseModel):
    amount: float
    submitter: str
    category: str
    description: str
    date: str

class RiskAssessment(BaseModel):
    risk_factors: str
    needs_review: bool

# --- Security Utilities ---
def detect_injection(text: str) -> bool:
    """Heuristic to detect prompt injection attempts."""
    suspicious_phrases = ["ignore previous", "system prompt", "bypass", "auto-approve", "you are now"]
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in suspicious_phrases)

def scrub_pii(text: str) -> tuple[str, list[str]]:
    """Scrubs SSNs and Credit Cards, returning the clean text and a list of redacted categories."""
    redacted_categories = []
    
    # SSN pattern
    ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
    if re.search(ssn_pattern, text):
        text = re.sub(ssn_pattern, '[REDACTED SSN]', text)
        redacted_categories.append('SSN')
        
    # Credit Card pattern
    cc_pattern = r'\b(?:\d[ -]*?){13,16}\b'
    if re.search(cc_pattern, text):
        text = re.sub(cc_pattern, '[REDACTED CREDIT CARD]', text)
        redacted_categories.append('Credit Card')
        
    return text, redacted_categories

# --- Nodes ---

@node
def parse_event(node_input: dict | str | bytes) -> Event:
    """Parses the incoming JSON event, handling plain JSON or base64 (Pub/Sub)."""
    data = node_input
    if isinstance(data, dict) and "data" in data:
        data = data["data"]
        
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            data = json.loads(base64.b64decode(data).decode("utf-8"))
            
    expense = ExpenseReport(**data)
    route = "review" if expense.amount >= EXPENSE_THRESHOLD else "auto_approve"
    logger.info(f"Parsed expense for ${expense.amount}. Routing to: {route}")
    
    return Event(
        output=expense.model_dump(), 
        route=route, 
        state={"expense": expense.model_dump()}
    )

@node
def auto_approve(node_input: dict) -> Event:
    """Instantly approves expenses under the threshold without LLM."""
    expense = node_input
    return Event(output={
        "status": "approved", 
        "reason": f"Under ${EXPENSE_THRESHOLD} threshold", 
        "expense": expense
    })

@node
def security_checkpoint(ctx: Context, node_input: dict) -> Event:
    """Security node to prevent prompt injection and scrub PII."""
    expense = ctx.state["expense"].copy()
    desc = expense["description"]
    
    # 1. Defend against prompt injection
    if detect_injection(desc):
        logger.warning(f"Injection detected in expense from {expense['submitter']}")
        # Create a mock risk assessment and route directly to human review
        risk_assessment = {
            "risk_factors": "SECURITY EVENT: Suspected prompt injection attempt detected in description.",
            "needs_review": True
        }
        return Event(output=risk_assessment, route="injection_detected")
        
    # 2. Scrub personal data
    clean_desc, redacted = scrub_pii(desc)
    expense["description"] = clean_desc
    
    # Update the state so downstream nodes get the CLEAN expense
    state_update = {
        "expense": expense,
        "redacted_categories": redacted
    }
    
    # Route to the LLM reviewer with the clean expense as output
    return Event(output=expense, route="clean", state=state_update)

# LLM Node: Reviews expenses over the threshold for risks
risk_reviewer = LlmAgent(
    name="risk_reviewer",
    model=MODEL_NAME,
    instruction="""
    Review the following expense for any risk factors. 
    Look for suspicious categories, unusually large amounts for the description, 
    or policy violations. Provide your assessment.
    """,
    output_schema=RiskAssessment,
)

@node
async def human_review(ctx: Context, node_input: dict):
    """Pauses workflow for a human to review the risk assessment."""
    risk_assessment = node_input
    expense = ctx.state["expense"]  # This is the CLEANED expense if it went through security
    redacted = ctx.state.get("redacted_categories", [])
    
    if not ctx.resume_inputs:
        redaction_note = f"\n(Redacted PII: {', '.join(redacted)})" if redacted else ""
        message = (
            f"⚠️ Expense needs review: {expense['submitter']} requested ${expense['amount']}.\n"
            f"Category: {expense['category']} | Desc: {expense['description']}{redaction_note}\n"
            f"Risk Assessment: {risk_assessment['risk_factors']}\n\n"
            f"Do you approve or reject this expense?"
        )
        yield RequestInput(interrupt_id="approval_decision", message=message)
        return
        
    decision = ctx.resume_inputs["approval_decision"]
    outcome = "approved" if "approve" in str(decision).lower() else "rejected"
    
    yield Event(output={
        "status": outcome, 
        "reason": "Human review", 
        "expense": expense, 
        "risk_assessment": risk_assessment
    })

@node
def record_outcome(node_input: dict) -> dict:
    """Final node that records the outcome of the expense report."""
    logger.info(f"Final Outcome: {node_input['status']} - {node_input['reason']}")
    return node_input

# --- Graph Definition ---

workflow = Workflow(
    name="expense_workflow",
    edges=[
        ('START', parse_event),
        # Parsing output routing
        (parse_event, auto_approve, "auto_approve"),
        (parse_event, security_checkpoint, "review"),
        
        # Security Checkpoint routing
        (security_checkpoint, risk_reviewer, "clean"),
        (security_checkpoint, human_review, "injection_detected"),
        
        # LLM to human
        (risk_reviewer, human_review),
        
        # Converge to the final outcome recorder
        (auto_approve, record_outcome),
        (human_review, record_outcome),
    ]
)

app = App(name="expense_agent", root_agent=workflow)
