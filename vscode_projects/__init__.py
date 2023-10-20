"""
vscode projects
"""

from dataclasses import dataclass
import json
import os
from pathlib import Path
from shutil import which
from sys import platform
from typing import Union
from albert import *

md_iid = '2.0'
md_version = "1.0"
md_name = "VSCode projects"
md_description = "Open your VSCode projects"
md_license = "GPL-3"
md_url = "https://github.com/albertlauncher/python/"
md_maintainers = ["@hanff"]

@dataclass
class Project:
    name: str
    path: str
    # last_opened: int


@dataclass
class Editor:
    name: str
    icon: Path
    # config_dir_prefix: str
    binary: str

    def __init__(self, name: str, icon: Path, binaries: list[str]):
        self.name = name
        self.icon = icon
        # self.config_dir_prefix = config_dir_prefix
        self.binary = self._find_binary(binaries)

    def _find_binary(self, binaries: list[str]) -> Union[str, None]:
        for binary in binaries:
            if which(binary):
                return binary
        return None

    def list_projects(self) -> list[Project]:
        vscode_settings_path = os.path.expanduser("~/.config/Code/User")
        workspace_storage_path = os.path.join(vscode_settings_path, "workspaceStorage")
        recent_projects = []
        if os.path.exists(workspace_storage_path):
            for root, dirs, files in os.walk(workspace_storage_path):
                for file in files:
                    if file == ("workspace.json"):
                        project_info_path = os.path.join(root, file)
                        with open(project_info_path, "r",encoding='utf8') as f:
                            project_data = json.load(f)
                            recent_projects.append(project_data["folder"])
        print(recent_projects)
        return self._parse_recent_projects(recent_projects)


    def _parse_recent_projects(self, recent_projects_file: list) -> list[Project]:
        projects = []
        
        for recent_file_path in recent_projects_file:
            target_path = recent_file_path[7:]
            projects.append(
                Project(
                    name=Path(target_path).name,
                    path=target_path
                )
            )
        return projects


class Plugin(PluginInstance, TriggerQueryHandler):
    def __init__(self):
        TriggerQueryHandler.__init__(
            self,
            id=md_id,
            name=md_name,
            description=md_description,
            synopsis='project name',
            defaultTrigger='vsc ',
        )
        PluginInstance.__init__(self, extensions=[self])
        
        plugin_dir = Path(__file__).parent
        editors=[
            Editor(
                name="VS Code",
                icon=plugin_dir/"vscode.png",
                binaries=["code"]
            )
        ]
        self.editors = [e for e in editors if e.binary is not None]
    
    def handleTriggerQuery(self, query: TriggerQuery):
        editor_project_pairs=[]
        for editor in self.editors:
            projects = editor.list_projects()
            projects = [p for p in projects if Path(p.path).exists()]
            projects = [p for p in projects if query.string.lower() in p.name.lower()]
            editor_project_pairs.extend([(editor, p) for p in projects])
        query.add([self._make_item(editor, project, query) for editor, project in editor_project_pairs])
        
    def _make_item(self, editor: Editor, project: Project, query: TriggerQuery) -> Item:
        return StandardItem(
            id="%s-%s" % (editor.binary, project.path),
            text=project.name,
            subtext=project.path,
            inputActionText=query.trigger + project.name,
            iconUrls=["file:" + str(editor.icon)],
            actions=[
                Action(
                    "Open",
                    "Open in %s" % editor.name,
                    lambda selected_project=project.path: runDetachedProcess(
                        [editor.binary, selected_project]
                    ),
                )
            ],
        )

