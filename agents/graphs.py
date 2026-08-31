from langgraph.graph import StateGraph, START, END

from agents.state import AgentState

from agents.nodes import (
    metadata_node,
    planning_node,
    human_approval_node,
    initialize_git_node,
    stage_files_node,
    commit_node,
    create_github_repo_node,
    remote_node,
    push_node,
    verify_node,
    error_node,
)


# ============================================================
# ROUTER: METADATA
# ============================================================

def metadata_router(state: AgentState):

    if state.get("error"):
        return "error"

    required = [
        "repo_name",
        "repo_description",
        "private",
        "commit_message",
    ]

    for field in required:

        if field not in state:
            return "error"

    return "planning"


# ============================================================
# ROUTER: APPROVAL
# ============================================================

def approval_router(state: AgentState):

    if state.get("approved") is True:
        return "execute"

    return "end"


# ============================================================
# ROUTER: EXECUTION ERROR
# ============================================================

def execution_router(state: AgentState):

    if state.get("error"):
        return "error"

    return "continue"


# ============================================================
# BUILD GRAPH
# ============================================================

def build_graph():

    graph = StateGraph(AgentState)

    # --------------------------------------------------------
    # Nodes
    # --------------------------------------------------------

    graph.add_node(
        "metadata",
        metadata_node,
    )

    graph.add_node(
        "planning",
        planning_node,
    )

    graph.add_node(
        "approval",
        human_approval_node,
    )

    graph.add_node(
        "initialize_git",
        initialize_git_node,
    )

    graph.add_node(
        "stage_files",
        stage_files_node,
    )

    graph.add_node(
        "commit",
        commit_node,
    )

    graph.add_node(
        "create_github_repo",
        create_github_repo_node,
    )

    graph.add_node(
        "remote",
        remote_node,
    )

    graph.add_node(
        "push",
        push_node,
    )

    graph.add_node(
        "verify",
        verify_node,
    )

    graph.add_node(
        "error",
        error_node,
    )

    # --------------------------------------------------------
    # START
    # --------------------------------------------------------

    graph.add_edge(
        START,
        "metadata",
    )

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    graph.add_conditional_edges(
        "metadata",
        metadata_router,
        {
            "planning": "planning",
            "error": "error",
        },
    )

    # --------------------------------------------------------
    # Planning → Approval
    # --------------------------------------------------------

    graph.add_edge(
        "planning",
        "approval",
    )

    # --------------------------------------------------------
    # Approval
    # --------------------------------------------------------

    graph.add_conditional_edges(
        "approval",
        approval_router,
        {
            "execute": "initialize_git",
            "end": END,
        },
    )

    # --------------------------------------------------------
    # Git initialization
    # --------------------------------------------------------

    graph.add_conditional_edges(
        "initialize_git",
        execution_router,
        {
            "continue": "stage_files",
            "error": "error",
        },
    )

    # --------------------------------------------------------
    # Stage files
    # --------------------------------------------------------

    graph.add_conditional_edges(
        "stage_files",
        execution_router,
        {
            "continue": "commit",
            "error": "error",
        },
    )

    # --------------------------------------------------------
    # Commit
    # --------------------------------------------------------

    graph.add_conditional_edges(
        "commit",
        execution_router,
        {
            "continue": "create_github_repo",
            "error": "error",
        },
    )

    # --------------------------------------------------------
    # GitHub repository
    # --------------------------------------------------------

    graph.add_conditional_edges(
        "create_github_repo",
        execution_router,
        {
            "continue": "remote",
            "error": "error",
        },
    )

    # --------------------------------------------------------
    # Remote
    # --------------------------------------------------------

    graph.add_conditional_edges(
        "remote",
        execution_router,
        {
            "continue": "push",
            "error": "error",
        },
    )

    # --------------------------------------------------------
    # Push
    # --------------------------------------------------------

    graph.add_conditional_edges(
        "push",
        execution_router,
        {
            "continue": "verify",
            "error": "error",
        },
    )

    # --------------------------------------------------------
    # Verify
    # --------------------------------------------------------

    graph.add_conditional_edges(
        "verify",
        execution_router,
        {
            "continue": END,
            "error": "error",
        },
    )

    # --------------------------------------------------------
    # Error
    # --------------------------------------------------------

    graph.add_edge(
        "error",
        END,
    )

    return graph.compile()