from crewai import Agent
from models import ProjectSummary

def create_summarizer_agent(llm):
    return Agent(
        role='Senior Codebase Cartographer',
        goal='Analyze the file tree and contents to create a highly accurate functional map of the codebase.',
        backstory=(
            "You are an expert software architect who excels at understanding "
            "strangers' codebases quickly. You look at directory structures and "
            "file contents to figure out the primary logic, purpose, and operations "
            "of each component."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
