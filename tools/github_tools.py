from github import Github
from github.GithubException import GithubException
from langchain_core.tools import tool
from config import GITHUB_TOKEN


def get_github_user():
    """
    Return information about the authenticated GitHub user.
    """

    try:
        github = Github(GITHUB_TOKEN)
        user = github.get_user()

        return {
            "success": True,
            "username": user.login,
            "name": user.name,
        }

    except GithubException as e:
        return {
            "success": False,
            "message": str(e),
        }


def create_repository(
    name: str,
    description: str = "",
    private: bool = False,
):
    """
    Create a new GitHub repository.
    """

    try:
        github = Github(GITHUB_TOKEN)

        user = github.get_user()

        # Check whether repository already exists
        try:
            user.get_repo(name)

            return {
                "success": False,
                "message": f"Repository '{name}' already exists.",
            }

        except GithubException as e:
            if e.status != 404:
                raise

        repo = user.create_repo(
            name=name,
            description=description,
            private=private,
            auto_init=False,
        )

        return {
            "success": True,
            "name": repo.name,
            "full_name": repo.full_name,
            "url": repo.html_url,
            "clone_url": repo.clone_url,
            "ssh_url": repo.ssh_url,
            "private": repo.private,
        }

    except GithubException as e:
        return {
            "success": False,
            "message": str(e),
        }


def get_repository(name: str):
    """
    Get information about an existing repository.
    """

    try:
        github = Github(GITHUB_TOKEN)

        user = github.get_user()

        repo = user.get_repo(name)

        return {
            "success": True,
            "name": repo.name,
            "full_name": repo.full_name,
            "description": repo.description,
            "url": repo.html_url,
            "private": repo.private,
            "default_branch": repo.default_branch,
        }

    except GithubException as e:
        return {
            "success": False,
            "message": str(e),
        }


def update_repository(
    name: str,
    description: str | None = None,
    private: bool | None = None,
):
    """
    Update repository metadata.
    """

    try:
        github = Github(GITHUB_TOKEN)

        user = github.get_user()

        repo = user.get_repo(name)

        if description is not None:
            repo.edit(description=description)

        if private is not None:
            repo.edit(private=private)

        return {
            "success": True,
            "name": repo.name,
            "description": repo.description,
            "private": repo.private,
            "url": repo.html_url,
        }

    except GithubException as e:
        return {
            "success": False,
            "message": str(e),
        }


@tool
def create_github_repository(
    name: str,
    description: str,
    private: bool = False,
) -> dict:
    """
    Create a new GitHub repository for the authenticated user.
    """
    return create_repository(
        name=name,
        description=description,
        private=private,
    )


@tool
def get_github_repository(name: str) -> dict:
    """
    Get information about an existing GitHub repository.
    """
    return get_repository(name)


@tool
def update_github_repository(
    name: str,
    description: str | None = None,
    private: bool | None = None,
) -> dict:
    """
    Update GitHub repository metadata.
    """
    return update_repository(
        name=name,
        description=description,
        private=private,
    )