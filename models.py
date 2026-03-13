from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class PromptInjectionCheckResult(BaseModel):
    is_safe: bool = Field(..., description="True if the input appears free of prompt injection attacks, False otherwise.")
    reason: str = Field(..., description="A short explanation of why the input was flagged as an attack or deemed safe.")

class FileSummary(BaseModel):
    filepath: str = Field(..., description="The path to the file")
    purpose: str = Field(..., description="High-level purpose of the file")
    key_logic: str = Field(..., description="The key logic or operations in this file")

class ProjectSummary(BaseModel):
    file_summaries: List[FileSummary] = Field(..., description="List of individual file summaries")
    architecture_overview: str = Field(..., description="Overall summary of the project architecture")

class SyntaxReviewFeedback(BaseModel):
    filepath: str = Field(..., description="The path to the file")
    style_issues: str = Field(..., description="Analysis of naming conventions (e.g. CamelCase vs snake_case consistency)")
    modularity_score: int = Field(..., description="Score 1-10 on how modular the code is")
    modularity_feedback: str = Field(..., description="Specific feedback on modularity")

class SyntaxReviewReport(BaseModel):
    reviews: List[SyntaxReviewFeedback] = Field(..., description="List of syntax reviews")
    overall_style_consistency: str = Field(..., description="Overall comment on codebase style consistency")

class LogicalFlaw(BaseModel):
    severity: str = Field(..., description="Severity of the flaw: Critical, Warning, or Info")
    title: str = Field(..., description="Short title of the flaw")
    description: str = Field(..., description="Detailed description of the logical flaw or security risk")
    cve_or_cwe_id: Optional[str] = Field(None, description="The CVE or CWE identifier if applicable")
    affected_files: List[str] = Field(..., description="Files affected by this flaw")
    recommendation: str = Field(..., description="How to fix the flaw")

class LogicalFlawsReport(BaseModel):
    flaws: List[LogicalFlaw] = Field(..., description="List of logical flaws found in the codebase")

class OrchestratorFinalReport(BaseModel):
    health_score: int = Field(..., description="Overall health score of the codebase 1-100")
    executive_summary: str = Field(..., description="A high-level executive summary of the review")
    key_vulnerabilities: List[LogicalFlaw] = Field(..., description="Consolidated and verified logical flaws (no vague findings)")
    style_and_modularity: SyntaxReviewReport = Field(..., description="Refined syntax and style review")
    architecture_summary: str = Field(..., description="Consolidated architecture overview")
