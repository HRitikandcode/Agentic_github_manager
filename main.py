import os

from agents.graphs import build_graph


def main():

    project_path = os.getcwd()

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


if __name__ == "__main__":
    main()