from crewai import Task
from models import OrchestratorFinalReport

def create_orchestrator_task(agent):
    return Task(
        description=(
            "Review the collective outputs from the Summarizer, Syntax "
            "Reviewer, and Logic Analyzer. "
            "1. Filter out any vague findings (e.g., 'consider adding error handling'). "
            "2. Ensure vulnerabilities map cleanly to the reported API surfaces. "
            "3. Calculate a final codebase Health Score (1-100). "
            "4. Combine everything into a single, cohesive, and deterministic "
            "final report structure."
        ),
        expected_output="A structured OrchestratorFinalReport containing the filtered and consolidated findings.",
        agent=agent,
        output_pydantic=OrchestratorFinalReport,
        context=[] # Will be filled dynamically in main.py by passing the previous 3 tasks
    )
