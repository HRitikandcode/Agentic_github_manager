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
    git_remote_get,
    git_set_remote,
    
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

    project_path = state["project_path"]

    repo_name = state.get(
        "repo_name",
        "unknown",
    )

    description = state.get(
        "repo_description",
        "",
    )

    private = state.get(
        "private",
        True,
    )

    commit_message = state.get(
        "commit_message",
        "Initial commit",
    )

    # -----------------------------------------
    # Check current Git state
    # -----------------------------------------

    status = git_status(project_path)

    if not status.get("success"):

        return {
            "error": status.get(
                "message",
                "Unable to determine Git status."
            )
        }

    has_changes = status.get(
        "has_changes",
        False,
    )

    # -----------------------------------------
    # Build plan
    # -----------------------------------------

    plan = [
        "Inspect the current project",
        "Check Git repository status",
        f"Create GitHub repository: {repo_name}",
        f"Set repository description: {description}",
        f"Repository visibility: "
        f"{'Private' if private else 'Public'}",
    ]

    if has_changes:

        plan.extend([
            "Stage project files",
            f'Create commit: "{commit_message}"',
        ])

    else:

        plan.append(
            "No local changes detected; skip commit"
        )

    plan.extend([
        "Configure the GitHub repository as origin",
        "Push the current branch to GitHub",
        "Verify the GitHub repository",
    ])

    print("\n===== PROPOSED PLAN =====")

    for index, step in enumerate(
        plan,
        start=1,
    ):
        print(f"{index}. {step}")

    return {
        "plan": plan,
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

metadata_llm = chat_model.bind_tools(
    [set_repository_metadata]
)


def metadata_node(state: AgentState):

    project_path = state["project_path"]

    print("\n===== ANALYZING WORKSPACE =====")

    # Inspect workspace directly.
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
You are generating metadata for a GitHub repository.

The workspace has ALREADY been inspected.

Project path:
{project_path}

Files:
{files}

Directories:
{directories}

File extensions:
{extensions}

DO NOT inspect the workspace.
DO NOT call inspect_workspace.
DO NOT call any other tool.

You MUST call set_repository_metadata.

Generate:

- repo_name
- repo_description
- private
- commit_message

Rules:
- repo_name must be lowercase kebab-case.
- Keep the repository name concise.
- Description must describe the actual project.
- Do not invent technologies.
- Set private to true.
- Commit message should be concise.
"""

    response = metadata_llm.invoke([
        (
            "system",
            """
You are a GitHub repository metadata generator.

You have exactly ONE tool available:
set_repository_metadata.

You MUST use that tool.
Do not call any other tool.
"""
        ),
        (
            "user",
            prompt
        ),
    ])

    print("\n===== METADATA LLM RESPONSE =====")
    print(response)

    print("\n===== METADATA TOOL CALLS =====")
    print(response.tool_calls)

    # Validate tool call
    if not response.tool_calls:
        return {
            "error": (
                "GLM-5.2 failed to generate repository metadata."
            )
        }

    tool_call = response.tool_calls[0]

    if tool_call["name"] != "set_repository_metadata":
        return {
            "error": (
                f"Unexpected tool called: "
                f"{tool_call['name']}"
            )
        }

    metadata = tool_call["args"]

    # Validate fields
    required_fields = [
        "repo_name",
        "repo_description",
        "private",
        "commit_message",
    ]

    missing = [
        field
        for field in required_fields
        if field not in metadata
    ]

    if missing:
        return {
            "error": (
                f"Missing metadata fields: {missing}"
            )
        }

    # Store metadata in LangGraph state
    repo_name = metadata["repo_name"].strip()
    repo_description = metadata[
        "repo_description"
    ].strip()

    commit_message = metadata[
        "commit_message"
    ].strip()

    private = bool(metadata["private"])

    print("\n===== GENERATED REPOSITORY METADATA =====")
    print(f"Repository: {repo_name}")
    print(f"Description: {repo_description}")
    print(f"Private: {private}")
    print(f"Commit: {commit_message}")

    return {
        "workspace_analysis": analysis,
        "repo_name": repo_name,
        "repo_description": repo_description,
        "private": private,
        "commit_message": commit_message,
    }
    

def error_node(state: AgentState):

    print("\n" + "=" * 60)
    print("AGENT ERROR")
    print("=" * 60)

    print(
        state.get(
            "error",
            "Unknown error occurred."
        )
    )

    return {}

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

    project_path = state["project_path"]

    # Check Git status first
    status = git_status(project_path)

    if not status.get("success"):
        return {
            "error": status.get(
                "message",
                "Unable to check Git status."
            )
        }

    # ------------------------------------------------
    # Nothing changed
    # ------------------------------------------------

    if not status.get("has_changes", False):

        print("\n===== GIT COMMIT =====")
        print("No changes detected.")
        print("Skipping commit.")

        return {
            "commit_created": False,
        }

    # ------------------------------------------------
    # Changes exist
    # ------------------------------------------------

    commit_message = state.get(
        "commit_message",
        "Update project",
    )

    result = git_commit(
        project_path,
        commit_message,
    )

    if not result.get("success"):

        return {
            "error": result.get(
                "message",
                "Git commit failed."
            )
        }

    print("\n===== GIT COMMIT =====")
    print(f"Commit created: {commit_message}")

    return {
        "commit_created": True,
    }


def create_github_repo_node(state: AgentState):

    repo_name = state.get("repo_name")
    repo_description = state.get("repo_description")
    private = state.get("private")

    if not repo_name:
        return {
            "error": "Repository name is missing."
        }

    if not repo_description:
        return {
            "error": "Repository description is missing."
        }

    if private is None:
        return {
            "error": "Repository visibility is missing."
        }

    print("\n===== GITHUB REPOSITORY =====")
    print(f"Repository: {repo_name}")

    # ------------------------------------------------
    # Try to create repository
    # ------------------------------------------------

    result = create_repository(
        name=repo_name,
        description=repo_description,
        private=private,
    )

    # ------------------------------------------------
    # Repository created
    # ------------------------------------------------

    if result.get("success"):

        print("Repository created successfully.")

        return {
            "github_repo_created": True,
            "github_url": result["url"],
            "github_clone_url": result["clone_url"],
        }

    # ------------------------------------------------
    # Repository already exists
    # ------------------------------------------------

    message = result.get(
        "message",
        ""
    )

    if "already exists" in message.lower():

        print(
            "Repository already exists."
        )

        print(
            "Attempting to use the existing repository..."
        )

        existing = get_repository(
            repo_name
        )

        if not existing.get("success"):

            return {
                "error": (
                    "Repository exists, but "
                    "could not retrieve it: "
                    + existing.get(
                        "message",
                        "Unknown error",
                    )
                )
            }

        print(
            "Existing repository found."
        )

        # Get repository URL from the existing repository response
        github_url = existing.get("url")

        # GitHub clone URL may not be returned by our tool.
        # Construct it from the repository URL.
        if not github_url:
            return {
                "error": (
                    "Existing repository was found, "
                    "but its URL was not returned."
                )
            }

        github_clone_url = github_url.rstrip("/") + ".git"

        print(f"GitHub URL: {github_url}")
        print(f"Git clone URL: {github_clone_url}")

        return {
            "github_repo_created": True,
            "github_url": github_url,
            "github_clone_url": github_clone_url,
        }

    # ------------------------------------------------
    # Other GitHub error
    # ------------------------------------------------

    return {
        "error": message or "GitHub repository creation failed."
    }

def remote_node(state: AgentState):

    project_path = state["project_path"]
    expected_url = state["github_clone_url"]

    print("\n===== GIT REMOTE =====")

    # Get existing remotes
    result = git_remote_get.invoke(project_path)

    if not result.get("success"):
        return {
            "error": result.get(
                "message",
                "Unable to inspect Git remotes."
            )
        }

    existing_origin = result.get("origin")

    # ------------------------------------------------
    # No origin exists
    # ------------------------------------------------

    if not existing_origin:

        print("No origin remote found.")
        print("Adding GitHub repository as origin...")

        result = git_add_remote(
            project_path,
            expected_url,
        )

        if not result.get("success"):
            return {
                "error": result.get(
                    "message",
                    "Failed to add GitHub remote."
                )
            }

        print("Origin added successfully.")

        return {}

    # ------------------------------------------------
    # Origin already exists
    # ------------------------------------------------

    print(f"Existing origin: {existing_origin}")

    # Normalize URLs before comparison
    current = existing_origin.rstrip("/").rstrip(".git")
    expected = expected_url.rstrip("/").rstrip(".git")

    if current.lower() == expected.lower():

        print("Origin already points to the correct repository.")
        print("Keeping existing origin.")

        return {}

    # ------------------------------------------------
    # Origin points somewhere else
    # ------------------------------------------------

    print("Origin points to a different repository.")
    print("Updating origin...")

    result = git_set_remote.invoke({
        "project_path": project_path,
        "remote_url": expected_url,
    })

    if not result.get("success"):

        return {
            "error": result.get(
                "message",
                "Failed to update Git remote."
            )
        }

    print("Origin updated successfully.")

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



