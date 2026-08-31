import os

from tools.workspace_tools import inspect_workspace


project_path = os.getcwd()

result = inspect_workspace.invoke({
    "project_path": project_path
})

print("\n===== WORKSPACE ANALYSIS =====")

print(result)