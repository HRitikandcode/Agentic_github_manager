import os
import argparse
from agents.graphs import build_graph


def main():

    project_path = get_project_path()
    validate_project(project_path)

    print("=" * 60)
    print("AGENTIC GITHUB REPOSITORY MANAGER")
    print("=" * 60)

    print(f"\nProject: {project_path}")

    graph = build_graph()

    initial_state = {
        "project_path": project_path,

        "messages": [
            (
                "user",
                f"""
Publish my current project to GitHub.

Project path:
{project_path}

Analyze the project first.
Generate an appropriate repository name
and description.
Ask for my approval before performing
any GitHub or Git write operations.
"""
            )
        ],
    }

    result = graph.invoke(
        initial_state
    )

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)

    if result.get("verified"):

        print("\n✅ Project successfully published!")

        print(
            f"Repository: "
            f"{result.get('github_url')}"
        )

    elif result.get("error"):

        print("\n❌ Operation failed.")

        print(
            f"Error: "
            f"{result['error']}"
        )

    else:

        print(
            "\nOperation ended without publishing."
        )


def get_project_path():

    parser = argparse.ArgumentParser(
        description="Agentic GitHub Repository Manager"
    )

    parser.add_argument(
        "--project",
        type=str,
        default=None,
        help="Path to the project to publish",
    )

    args = parser.parse_args()

    if args.project:
        return os.path.abspath(
            args.project
        )

    return os.getcwd()


def validate_project(path):

    if not os.path.exists(path):
        raise ValueError(
            f"Project does not exist: {path}"
        )

    if not os.path.isdir(path):
        raise ValueError(
            f"Project path is not a directory: {path}"
        )


if __name__ == "__main__":
    main()