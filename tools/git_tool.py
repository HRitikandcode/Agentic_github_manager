import os

from git import Repo, GitCommandError
from git.exc import InvalidGitRepositoryError, NoSuchPathError


def git_status(project_path: str) -> dict:
    """
    Get the current Git status of a project.
    """

    try:
        repo = Repo(project_path)

        return {
            "success": True,
            "is_git_repo": True,
            "branch": repo.active_branch.name,
            "has_changes": repo.is_dirty(untracked_files=True),
            "untracked_files": repo.untracked_files,
        }

    except InvalidGitRepositoryError:
        return {
            "success": True,
            "is_git_repo": False,
            "message": "This directory is not a Git repository.",
        }

    except NoSuchPathError:
        return {
            "success": False,
            "message": f"Path does not exist: {project_path}",
        }


def git_init(project_path: str) -> dict:
    """
    Initialize a Git repository.
    """

    try:
        repo = Repo.init(project_path)

        return {
            "success": True,
            "message": "Git repository initialized successfully.",
            "branch": repo.active_branch.name,
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e),
        }


def git_add(project_path: str) -> dict:
    """
    Stage all files in the project.
    """

    try:
        repo = Repo(project_path)

        repo.git.add(A=True)

        return {
            "success": True,
            "message": "All files staged successfully.",
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e),
        }


def git_commit(project_path: str, message: str) -> dict:
    """
    Create a Git commit.
    """

    try:
        repo = Repo(project_path)

        if not repo.is_dirty(untracked_files=True):
            return {
                "success": False,
                "message": "There are no changes to commit.",
            }

        commit = repo.index.commit(message)

        return {
            "success": True,
            "message": "Commit created successfully.",
            "commit_hash": commit.hexsha,
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e),
        }


def git_remote(project_path: str) -> dict:
    """
    Get the configured Git remotes.
    """

    try:
        repo = Repo(project_path)

        remotes = []

        for remote in repo.remotes:
            remotes.append({
                "name": remote.name,
                "url": remote.url,
            })

        return {
            "success": True,
            "remotes": remotes,
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e),
        }


def git_add_remote(
    project_path: str,
    remote_url: str,
) -> dict:
    """
    Add the GitHub repository as the origin remote.
    """

    try:
        repo = Repo(project_path)

        if "origin" in [remote.name for remote in repo.remotes]:
            return {
                "success": False,
                "message": "Origin remote already exists.",
            }

        repo.create_remote("origin", remote_url)

        return {
            "success": True,
            "message": "Origin remote added successfully.",
            "remote_url": remote_url,
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e),
        }


def git_push(project_path: str) -> dict:
    """
    Push the current branch to origin.
    """

    try:
        repo = Repo(project_path)

        branch = repo.active_branch.name

        origin = repo.remote("origin")

        origin.push(
            refspec=f"{branch}:{branch}",
            set_upstream=True,
        )

        return {
            "success": True,
            "message": f"Successfully pushed branch '{branch}'.",
            "branch": branch,
        }

    except GitCommandError as e:
        return {
            "success": False,
            "message": str(e),
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e),
        }







from langchain_core.tools import tool

@tool
def check_git_status(project_path: str) -> dict:
    """
    Check whether a directory is a Git repository
    and return its current Git status.
    """
    return git_status(project_path)


@tool
def initialize_git_repository(project_path: str) -> dict:
    """
    Initialize a Git repository in the specified project directory.
    """
    return git_init(project_path)


@tool
def stage_project_files(project_path: str) -> dict:
    """
    Stage all project files for the next Git commit.
    """
    return git_add(project_path)


@tool
def create_git_commit(
    project_path: str,
    message: str,
) -> dict:
    """
    Create a Git commit with the specified commit message.
    """
    return git_commit(project_path, message)


@tool
def add_github_remote(
    project_path: str,
    remote_url: str,
) -> dict:
    """
    Add a GitHub repository as the origin remote.
    """
    return git_add_remote(project_path, remote_url)


@tool
def push_to_github(project_path: str) -> dict:
    """
    Push the current Git branch to the GitHub origin remote.
    """
    return git_push(project_path)


import subprocess

from langchain_core.tools import tool


@tool
def git_remote_get(project_path: str) -> dict:
    """
    Get the Git remote URLs for a project.
    """

    try:

        result = subprocess.run(
            [
                "git",
                "-C",
                project_path,
                "remote",
                "-v",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:

            return {
                "success": False,
                "message": result.stderr.strip(),
            }

        origin = None

        for line in result.stdout.splitlines():

            parts = line.split()

            if len(parts) >= 2 and parts[0] == "origin":

                origin = parts[1]
                break

        return {
            "success": True,
            "origin": origin,
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e),
        }



@tool
def git_set_remote(
    project_path: str,
    remote_url: str,
) -> dict:
    """
    Set the origin remote URL for a Git repository.
    """

    try:

        result = subprocess.run(
            [
                "git",
                "-C",
                project_path,
                "remote",
                "set-url",
                "origin",
                remote_url,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:

            return {
                "success": False,
                "message": result.stderr.strip(),
            }

        return {
            "success": True,
            "remote_url": remote_url,
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e),
        }