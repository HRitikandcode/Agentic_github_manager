from langgraph.graph import (
    StateGraph,
    START,
    END,
)

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
)


def approval_router(state: AgentState):

    if state.get("approved") is True:
        return "execute"

    return "end"


def build_graph():

    graph = StateGraph(AgentState)

    # -------------------------
    # Nodes
    # -------------------------

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

    # -------------------------
    # Workflow
    # -------------------------

    graph.add_edge(
        START,
        "metadata",
    )

    graph.add_edge(
        "metadata",
        "planning",
    )

    graph.add_edge(
        "planning",
        "approval",
    )

    graph.add_conditional_edges(
        "approval",
        approval_router,
        {
            "execute": "initialize_git",
            "end": END,
        },
    )

    graph.add_edge(
        "initialize_git",
        "stage_files",
    )

    graph.add_edge(
        "stage_files",
        "commit",
    )

    graph.add_edge(
        "commit",
        "create_github_repo",
    )

    graph.add_edge(
        "create_github_repo",
        "remote",
    )

    graph.add_edge(
        "remote",
        "push",
    )

    graph.add_edge(
        "push",
        "verify",
    )

    graph.add_edge(
        "verify",
        END,
    )

    return graph.compile()