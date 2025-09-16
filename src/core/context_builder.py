"""
Context Builder for DeepCode
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from .file_manager import FileManager

class ContextBuilder:
    def __init__(self, config):
        self.config = config
        self.file_manager = FileManager(config)
        # Safe, configurable limits for larger context windows
        self.max_files = self.config.get('project.context_max_files', 200)
        self.dir_tree_depth = self.config.get('project.context_tree_depth', 4)

    def build_project_context(self, project_type: str = None, template: str = None) -> Dict[str, Any]:
        """Build context for creating a new project"""
        # Collect a snapshot of the repository to seed the model's context
        files = self.file_manager.get_project_files(root_dir=Path('.'))
        files_limited = [str(p) for p in files[: self.max_files]]

        # Detect languages by extension
        languages = sorted({Path(p).suffix.lstrip('.').lower() for p in files_limited if Path(p).suffix})

        return {
            'project_type': project_type,
            'template': template,
            'current_directory': str(Path.cwd()),
            'existing_files': files_limited,
            'languages_detected': languages,
            'directory_structure': self.file_manager.get_directory_structure(Path('.'), max_depth=self.dir_tree_depth)
        }

    def build_file_context(self, directory: Path, file_type: str) -> Dict[str, Any]:
        """Build context for creating or analyzing a single file"""
        # Use file manager to enrich file context
        directory = Path(directory)
        samples = []
        if directory.exists() and directory.is_dir():
            # Take a small sample of files in the directory with the same type
            for p in directory.glob(f"*.{file_type}" if file_type and not file_type.startswith('.') else f"*{file_type}"):
                if self.file_manager._should_include_file(p):
                    samples.append(str(p))
                    if len(samples) >= 20:
                        break

        return {
            'directory': str(directory),
            'file_type': file_type,
            'similar_files': samples,
            'project_structure': self.file_manager.get_directory_structure(directory, max_depth=min(2, self.dir_tree_depth))
        }

    def build_modification_context(self, file_path: Path, description: str) -> Dict[str, Any]:
        """Build context for modifying an existing file"""
        file_path = Path(file_path)
        file_info: Dict[str, Any] = {}
        similar: List[str] = []

        try:
            if file_path.exists():
                file_info = self.file_manager.get_file_info(file_path)
                similar = [str(p) for p in self.file_manager.find_similar_files(file_path)]
        except Exception:
            file_info = {}
            similar = []

        return {
            'file_path': str(file_path),
            'file_type': self._detect_file_type(file_path.suffix),
            'description': description,
            'file_analysis': file_info,
            'related_files': similar,
            'dependencies': []  # Dependency detection is handled by analyzers elsewhere
        }

    def build_chat_context(self) -> Dict[str, Any]:
        """Build general context for chat interactions"""
        cwd = Path.cwd()
        files = self.file_manager.get_project_files(root_dir=cwd)
        files_limited = [str(p) for p in files[: self.max_files]]

        # Detect languages and guess project type
        languages = sorted({Path(p).suffix.lstrip('.').lower() for p in files_limited if Path(p).suffix})
        project_type = None
        if 'py' in languages:
            project_type = 'python'
        elif any(lang in languages for lang in ('js', 'ts')):
            project_type = 'javascript'
        elif 'java' in languages:
            project_type = 'java'

        return {
            'working_directory': str(cwd),
            'project_files': files_limited,
            'languages_detected': languages,
            'project_type': project_type,
            'directory_structure': self.file_manager.get_directory_structure(cwd, max_depth=self.dir_tree_depth)
        }

    def _detect_file_type(self, extension: str) -> str:
        """Detect file type from extension"""
        type_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.cs': 'csharp',
            '.swift': 'swift',
            '.html': 'html',
            '.css': 'css',
            '.sql': 'sql',
            '.json': 'json',
            '.yaml': 'yaml',
            '.md': 'markdown',
            '.txt': 'text'
        }
        return type_map.get(extension.lower(), 'unknown')
