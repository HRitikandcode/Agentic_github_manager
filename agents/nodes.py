from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from config import HF_TOKEN
from agents.state import AgentState

from tools.git_tool import (
    check_git_status,
    initialize_git_repository,
    stage_project_files,
    create_git_commit,
    add_github_remote,
    push_to_github,
    git_status,
    git_init,
    git_add,
    git_commit,
    git_add_remote,
    git_push,
    
)
from tools.github_tools import (
    create_github_repository,
    get_github_repository,
    update_github_repository,
    create_repository,
    get_repository,

)
from tools.workspace_tools import (
    inspect_workspace,
    set_repository_metadata,
)



llm = HuggingFaceEndpoint(
    repo_id="zai-org/GLM-5.2",
    huggingfacehub_api_token=HF_TOKEN,
    temperature=0,
)

chat_model = ChatHuggingFace(
    llm=llm,
)




tools = [
    check_git_status,
    initialize_git_repository,
    stage_project_files,
    create_git_commit,
    add_github_remote,
    push_to_github,

    create_github_repository,
    get_github_repository,
    update_github_repository,

    inspect_workspace,
    set_repository_metadata,
]


llm_with_tools = chat_model.bind_tools(tools)



def agent_node(state: AgentState):

    system_prompt = """
You are an AI GitHub Repository Manager.

Your job is to help users manage their local project
and publish it to GitHub.

You have access to Git, GitHub, and workspace tools.

IMPORTANT RULES:

1. Always inspect the project before modifying it.
2. Always check Git status before Git operations.
3. Never expose API tokens or secrets.
4. Never delete repositories.
5. Never invent tool results.
6. Never claim an operation succeeded unless a tool confirms it.
7. Read-only operations can be performed during analysis.
8. GitHub repository creation and code pushing require human approval.
9. After approval, execute only the operations necessary
   to complete the user's request.
10. If a tool fails, inspect the error and determine a safe
    recovery strategy.
"""

    messages = state.get("messages", [])

    print("\n[DEBUG] Messages sent to LLM:")

    for message in messages:
        print(
            f"  {message.type}: "
            f"{message.content}"
        )

    response = llm_with_tools.invoke(
        [
            ("system", system_prompt),
            *messages,
        ]
    )

    print("\n[DEBUG] LLM response:")
    print(response)

    print("\n[DEBUG] Tool calls:")
    print(response.tool_calls)

    return {
        "messages": [response]
    }




def planning_node(state: AgentState):

    repo_name = state.get(
        "repo_name",
        "unknown"
    )

    description = state.get(
        "repo_description",
        ""
    )

    private = state.get(
        "private",
        True
    )

    commit_message = state.get(
        "commit_message",
        "Initial commit"
    )

    visibility = "Private" if private else "Public"

    plan = [
        "Inspect the current project",
        "Check Git repository status",
        f"Create GitHub repository: {repo_name}",
        f"Set repository description: {description}",
        f"Repository visibility: {visibility}",
        "Stage project files",
        f'Create commit: "{commit_message}"',
        "Configure the GitHub repository as origin",
        "Push the current branch to GitHub",
        "Verify the GitHub repository",
    ]

    print("\n===== PROPOSED PLAN =====")

    for index, step in enumerate(
        plan,
        start=1,
    ):
        print(f"{index}. {step}")

    return {
        "plan": plan,
        "approval_required": True,
    }



def human_approval_node(state: AgentState):

    print("\n" + "=" * 60)
    print("HUMAN APPROVAL REQUIRED")
    print("=" * 60)

    for index, step in enumerate(
        state.get("plan", []),
        start=1,
    ):
        print(f"{index}. {step}")

    answer = input(
        "\nApprove? [y/n]: "
    ).strip().lower()

    if answer in {"y", "yes"}:

        return {
            "approved": True,
            "execution_mode": "approved",
        }

    return {
        "approved": False,
        "execution_mode": "rejected",
    }


def approval_router(state: AgentState):

    if state.get("approved") is True:
        return "execute"

    return "end"


def metadata_node(state: AgentState):

    project_path = state["project_path"]

    analysis = inspect_workspace.invoke({
        "project_path": project_path
    })

    if not analysis.get("success"):
        return {
            "error": analysis.get(
                "message",
                "Workspace inspection failed."
            )
        }

    files = analysis.get("files", [])
    directories = analysis.get("directories", [])
    extensions = analysis.get("file_extensions", {})

    prompt = f"""
Analyze this software project and prepare metadata
for a GitHub repository.

Project path:
{project_path}

Files:
{files}

Directories:
{directories}

File extensions:
{extensions}

Use the set_repository_metadata tool to provide:

1. A concise repository name.
2. A one-sentence repository description.
3. Whether the repository should be private.
4. An appropriate initial commit message.

Rules:

- Repository name must be lowercase kebab-case.
- Do not invent technologies.
- Prefer private=true.
- Do not create or modify the GitHub repository.
- Only generate metadata.
"""

    response = llm_with_tools.invoke(
        [
            (
                "system",
                "You are a software project analysis assistant."
            ),
            (
                "user",
                prompt
            ),
        ]
    )

    print("\n===== METADATA AGENT RESPONSE =====")
    print(response)

    return {
        "workspace_analysis": analysis,
        "messages": [response],
    }


def metadata_node(state: AgentState):

    project_path = state["project_path"]

    analysis = inspect_workspace.invoke({
        "project_path": project_path
    })

    if not analysis.get("success"):
        return {
            "error": analysis.get(
                "message",
                "Workspace inspection failed."
            )
        }

    files = analysis.get("files", [])
    directories = analysis.get("directories", [])
    extensions = analysis.get("file_extensions", {})

    metadata_prompt = f"""
You are preparing a software project for GitHub.

Analyze the following project information.

Project path:
{project_path}

Files:
{files}

Directories:
{directories}

File extensions:
{extensions}

Generate GitHub repository metadata.

Return ONLY valid JSON.

Required format:

{{
    "repo_name": "example-project",
    "repo_description": "Short description of the project",
    "private": true,
    "commit_message": "Initial commit"
}}

Rules:

- repo_name must use lowercase kebab-case.
- repo_name should be concise.
- repo_description must describe the actual project.
- Do not invent technologies that are not supported by the project.
- private should normally be true.
- commit_message should be concise.
"""

    response = chat_model.invoke(
        metadata_prompt
    )

    print("\n===== RAW METADATA RESPONSE =====")
    print(response.content)

    return {
        "workspace_analysis": analysis,
        "messages": [response],
    }





def initialize_git_node(state: AgentState):

    project_path = state["project_path"]

    result = git_status(project_path)

    if not result.get("success"):
        return {
            "error": result.get("message")
        }

    if result.get("is_git_repo"):

        return {
            "git_initialized": True
        }

    result = git_init(project_path)

    if not result.get("success"):
        return {
            "error": result.get("message")
        }

    return {
        "git_initialized": True
    }


def stage_files_node(state: AgentState):

    result = git_add(
        state["project_path"]
    )

    if not result.get("success"):
        return {
            "error": result.get("message")
        }

    return {
        "files_staged": True
    }


def commit_node(state: AgentState):

    commit_message = state.get(
        "commit_message",
        "Initial commit",
    )

    result = git_commit(
        state["project_path"],
        commit_message,
    )

    if not result.get("success"):
        return {
            "error": result.get("message")
        }

    return {
        "commit_created": True
    }


def create_github_repo_node(state: AgentState):

    result = create_repository(
        name=state["repo_name"],
        description=state["repo_description"],
        private=state["private"],
    )

    if not result.get("success"):

        return {
            "error": result.get("message")
        }

    return {
        "github_repo_created": True,
        "github_url": result["url"],
        "github_clone_url": result["clone_url"],
    }


def remote_node(state: AgentState):

    result = git_add_remote(
        state["project_path"],
        state["github_clone_url"],
    )

    if not result.get("success"):

        return {
            "error": result.get("message")
        }

    return {}



def push_node(state: AgentState):

    result = git_push(
        state["project_path"]
    )

    if not result.get("success"):

        return {
            "push_successful": False,
            "error": result.get("message"),
        }

    return {
        "push_successful": True
    }


def verify_node(state: AgentState):

    result = get_repository(
        state["repo_name"]
    )

    if not result.get("success"):

        return {
            "verified": False,
            "error": result.get("message"),
        }

    return {
        "verified": True,
        "github_url": result["url"],
    }



