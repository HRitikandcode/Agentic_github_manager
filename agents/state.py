from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):

    # -------------------------
    # Conversation
    # -------------------------

    messages: Annotated[list[AnyMessage], add_messages]

    user_request: str

    # -------------------------
    # Project
    # -------------------------

    project_path: str

    # -------------------------
    # Repository metadata
    # -------------------------

    repo_name: str
    repo_description: str
    private: bool
    commit_message: str

    # -------------------------
    # Workspace
    # -------------------------

    workspace_analysis: dict

    # -------------------------
    # Git state
    # -------------------------

    git_initialized: bool
    files_staged: bool
    commit_created: bool

    # -------------------------
    # GitHub state
    # -------------------------

    github_repo_created: bool
    github_url: str
    github_clone_url: str

    # -------------------------
    # Execution
    # -------------------------

    plan: list[str]

    approval_required: bool
    approved: bool

    # -------------------------
    # Final state
    # -------------------------

    push_successful: bool
    verified: bool

    error: str