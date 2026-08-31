import os
from langchain_core.tools import tool


# Files/directories that should NEVER be exposed
# to the LLM or included in the project analysis.
IGNORED_NAMES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".env",
    ".idea",
    "node_modules",
}


@tool
def inspect_workspace(project_path: str) -> dict:
    """
    Analyze the structure and important files of a local project.

    Returns project files, detected programming languages,
    configuration files, and basic project information.
    """

    if not os.path.exists(project_path):
        return {
            "success": False,
            "message": f"Project path does not exist: {project_path}",
        }

    if not os.path.isdir(project_path):
        return {
            "success": False,
            "message": f"Project path is not a directory: {project_path}",
        }

    files = []
    directories = []

    extensions = {}

    for root, dirs, filenames in os.walk(project_path):

        # Remove ignored directories from traversal
        dirs[:] = [
            d for d in dirs
            if d not in IGNORED_NAMES
        ]

        for directory in dirs:

            relative_path = os.path.relpath(
                os.path.join(root, directory),
                project_path,
            )

            directories.append(relative_path)

        for filename in filenames:

            if filename in IGNORED_NAMES:
                continue

            full_path = os.path.join(
                root,
                filename,
            )

            relative_path = os.path.relpath(
                full_path,
                project_path,
            )

            files.append(relative_path)

            _, extension = os.path.splitext(filename)

            if extension:
                extension = extension.lower()

                extensions[extension] = (
                    extensions.get(extension, 0) + 1
                )

    return {
        "success": True,
        "project_path": project_path,
        "file_count": len(files),
        "directory_count": len(directories),
        "files": files,
        "directories": directories,
        "file_extensions": extensions,
    }






@tool
def set_repository_metadata(
    repo_name: str,
    repo_description: str,
    private: bool,
    commit_message: str,
) -> dict:
    """
    Store proposed GitHub repository metadata.
    This tool does not create or modify a GitHub repository.
    """

    return {
        "success": True,
        "repo_name": repo_name,
        "repo_description": repo_description,
        "private": private,
        "commit_message": commit_message,
    }