"""
File Manager for DeepCode
Handles safe file operations, backups, and context management
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib

class FileManager:
    def __init__(self, config):
        self.config = config
        self.backup_dir = Path.home() / '.conflict-deepcode' / 'backups'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # File size limits
        self.max_file_size = self._parse_size(config.get('project.max_file_size', '1MB'))
        
        # Ignore patterns
        self.ignore_patterns = config.get('project.ignore_patterns', [
            '.git', 'node_modules', '__pycache__', '*.pyc', '.deepcode'
        ])
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string like '1MB' to bytes"""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    def is_directory_target(self, target: str) -> bool:
        """Check if target appears to be a directory/project"""
        # If no extension and doesn't exist as file, assume directory
        path = Path(target)
        return not path.suffix and not path.is_file()
    
    def read_file(self, file_path: Path) -> str:
        """Safely read file content with size and encoding checks"""
        try:
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size:
                raise ValueError(f"File too large: {file_size} bytes > {self.max_file_size} bytes")
            
            # Try to read with different encodings
            for encoding in ['utf-8', 'utf-8-sig', 'latin-1']:
                try:
                    return file_path.read_text(encoding=encoding)
                except UnicodeDecodeError:
                    continue
            
            raise ValueError("Could not decode file with any supported encoding")
            
        except Exception as e:
            raise Exception(f"Failed to read {file_path}: {str(e)}")
    
    def write_file(self, file_path: Path, content: str) -> bool:
        """Safely write content to file"""
        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write with UTF-8 encoding
            file_path.write_text(content, encoding='utf-8')
            
            return True
            
        except Exception as e:
            raise Exception(f"Failed to write {file_path}: {str(e)}")
    
    def create_file(self, file_path: Path, content: str) -> bool:
        """Create new file with content"""
        if file_path.exists():
            raise FileExistsError(f"File {file_path} already exists")
        
        return self.write_file(file_path, content)
    
    def create_backup(self, file_path: Path) -> Path:
        """Create backup of file before modification"""
        if not file_path.exists():
            raise FileNotFoundError(f"Cannot backup non-existent file: {file_path}")
        
        # Generate backup filename with timestamp and hash
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        content = self.read_file(file_path)
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        
        backup_name = f"{file_path.stem}_{timestamp}_{content_hash}{file_path.suffix}"
        backup_path = self.backup_dir / backup_name
        
        # Copy file to backup location
        shutil.copy2(file_path, backup_path)
        
        return backup_path
    
    def list_backups(self, file_path: Path = None) -> List[Dict]:
        """List available backups, optionally for specific file"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*"):
            if backup_file.is_file():
                # Parse backup filename to extract info
                parts = backup_file.stem.split('_')
                if len(parts) >= 3:
                    original_name = '_'.join(parts[:-2])
                    timestamp = parts[-2]
                    file_hash = parts[-1]
                    
                    if file_path is None or original_name == file_path.stem:
                        backups.append({
                            'file': str(backup_file),
                            'original_name': original_name,
                            'timestamp': timestamp,
                            'hash': file_hash,
                            'size': backup_file.stat().st_size
                        })
        
        return sorted(backups, key=lambda x: x['timestamp'], reverse=True)
    
    def restore_backup(self, backup_path: Path, target_path: Path) -> bool:
        """Restore file from backup"""
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        # Create backup of current file if it exists
        if target_path.exists():
            self.create_backup(target_path)
        
        # Copy backup to target location
        shutil.copy2(backup_path, target_path)
        return True
    
    def get_project_files(self, root_dir: Path = None, extensions: List[str] = None) -> List[Path]:
        """Get list of relevant project files"""
        if root_dir is None:
            root_dir = Path('.')
        
        if extensions is None:
            extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.php', '.rb']
        
        files = []
        
        for ext in extensions:
            for file_path in root_dir.rglob(f"*{ext}"):
                if self._should_include_file(file_path):
                    files.append(file_path)
        
        return sorted(files)
    
    def _should_include_file(self, file_path: Path) -> bool:
        """Check if file should be included based on ignore patterns"""
        path_str = str(file_path)
        
        for pattern in self.ignore_patterns:
            if pattern.startswith('*'):
                # Wildcard pattern
                if path_str.endswith(pattern[1:]):
                    return False
            elif pattern in path_str:
                # Substring pattern
                return False
        
        # Check file size
        try:
            if file_path.stat().st_size > self.max_file_size:
                return False
        except:
            return False
        
        return True
    
    def get_file_info(self, file_path: Path) -> Dict:
        """Get detailed information about a file"""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        stat = file_path.stat()
        
        return {
            'path': str(file_path),
            'name': file_path.name,
            'extension': file_path.suffix,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'is_readable': os.access(file_path, os.R_OK),
            'is_writable': os.access(file_path, os.W_OK)
        }
    
    def find_similar_files(self, file_path: Path) -> List[Path]:
        """Find files with similar names or in same directory"""
        similar_files = []
        
        # Files in same directory with same extension
        for sibling in file_path.parent.glob(f"*{file_path.suffix}"):
            if sibling != file_path and self._should_include_file(sibling):
                similar_files.append(sibling)
        
        # Files with similar names in subdirectories
        stem_pattern = f"*{file_path.stem}*{file_path.suffix}"
        for similar in file_path.parent.rglob(stem_pattern):
            if similar != file_path and self._should_include_file(similar):
                similar_files.append(similar)
        
        return similar_files[:10]  # Limit to 10 similar files
    
    def get_directory_structure(self, root_dir: Path = None, max_depth: int = 3) -> Dict:
        """Get directory structure as nested dict"""
        if root_dir is None:
            root_dir = Path('.')
        
        def _build_tree(path: Path, depth: int = 0) -> Dict:
            if depth > max_depth:
                return {}
            
            tree = {'type': 'directory', 'children': {}}
            
            try:
                for item in path.iterdir():
                    if self._should_include_path(item):
                        if item.is_dir():
                            tree['children'][item.name] = _build_tree(item, depth + 1)
                        else:
                            tree['children'][item.name] = {
                                'type': 'file',
                                'size': item.stat().st_size,
                                'extension': item.suffix
                            }
            except PermissionError:
                pass
            
            return tree
        
        return _build_tree(root_dir)
    
    def _should_include_path(self, path: Path) -> bool:
        """Check if path should be included in directory listing"""
        path_str = str(path)
        
        for pattern in self.ignore_patterns:
            if pattern.startswith('*'):
                if path.name.endswith(pattern[1:]):
                    return False
            elif pattern in path_str or path.name == pattern:
                return False
        
        return True
    
    def delete_file(self, file_path: Path, force: bool = False) -> Dict[str, Any]:
        """Safely delete a file with optional backup"""
        try:
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"File {file_path} does not exist"
                }

            # Create backup before deletion unless force is True
            backup_path = None
            if not force:
                try:
                    backup_path = self.create_backup(file_path)
                except Exception as e:
                    if not force:
                        return {
                            "success": False,
                            "error": f"Failed to create backup: {str(e)}"
                        }

            # Delete the file
            file_path.unlink()

            return {
                "success": True,
                "file": str(file_path),
                "backup_created": backup_path is not None,
                "backup_path": str(backup_path) if backup_path else None,
                "message": f"Successfully deleted {file_path}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to delete {file_path}: {str(e)}"
            }

    def clear_file(self, file_path: Path, force: bool = False) -> Dict[str, Any]:
        """Clear file contents (make file empty) with optional backup"""
        try:
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"File {file_path} does not exist"
                }

            # Create backup before clearing unless force is True
            backup_path = None
            if not force:
                try:
                    backup_path = self.create_backup(file_path)
                except Exception as e:
                    if not force:
                        return {
                            "success": False,
                            "error": f"Failed to create backup: {str(e)}"
                        }

            # Clear the file by writing empty content
            self.write_file(file_path, "")

            return {
                "success": True,
                "file": str(file_path),
                "backup_created": backup_path is not None,
                "backup_path": str(backup_path) if backup_path else None,
                "message": f"Successfully cleared contents of {file_path}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to clear {file_path}: {str(e)}"
            }

    def delete_directory(self, dir_path: Path, force: bool = False, recursive: bool = False) -> Dict[str, Any]:
        """Safely delete a directory with optional backup"""
        try:
            if not dir_path.exists():
                return {
                    "success": False,
                    "error": f"Directory {dir_path} does not exist"
                }

            if not dir_path.is_dir():
                return {
                    "success": False,
                    "error": f"{dir_path} is not a directory"
                }

            # Check if directory is empty (for safety)
            if not recursive and list(dir_path.iterdir()):
                return {
                    "success": False,
                    "error": f"Directory {dir_path} is not empty. Use recursive=True to delete non-empty directories"
                }

            # For directories, we can't easily create a backup like files
            # Instead, we'll create a manifest of what was deleted
            manifest = []
            if recursive:
                for item in dir_path.rglob("*"):
                    if item.is_file():
                        manifest.append({
                            "path": str(item),
                            "type": "file",
                            "size": item.stat().st_size
                        })
                    else:
                        manifest.append({
                            "path": str(item),
                            "type": "directory"
                        })

            # Delete the directory
            if recursive:
                shutil.rmtree(dir_path)
            else:
                dir_path.rmdir()

            return {
                "success": True,
                "directory": str(dir_path),
                "recursive": recursive,
                "manifest": manifest,
                "message": f"Successfully deleted directory {dir_path}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to delete directory {dir_path}: {str(e)}"
            }

    def cleanup_backups(self, keep_count: int = 50) -> int:
        """Clean up old backups, keeping only the most recent ones"""
        backups = list(self.backup_dir.glob("*"))
        backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        removed_count = 0
        for backup in backups[keep_count:]:
            try:
                backup.unlink()
                removed_count += 1
            except:
                continue

        return removed_count
    # --- Extended file operations appended by Kilo Code ---

    def append_file(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Append content to a file, creating it if missing."""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            existing = ""
            if file_path.exists():
                existing = self.read_file(file_path)
            new_content = (existing + ("\n" if existing and not existing.endswith("\n") else "") + content)
            self.write_file(file_path, new_content)
            return {
                "success": True,
                "file": str(file_path),
                "bytes_appended": len(content.encode("utf-8")),
                "message": f"Appended {len(content)} chars to {file_path}"
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to append to {file_path}: {str(e)}"}

    def create_directory(self, dir_path: Path, exist_ok: bool = True) -> Dict[str, Any]:
        """Create a directory."""
        try:
            dir_path.mkdir(parents=True, exist_ok=exist_ok)
            return {"success": True, "directory": str(dir_path), "message": f"Created directory {dir_path}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to create directory {dir_path}: {str(e)}"}

    def move_file(self, src: Path, dst: Path, overwrite: bool = False, backup: bool = True) -> Dict[str, Any]:
        """Move/rename a single file."""
        try:
            if not src.exists() or not src.is_file():
                return {"success": False, "error": f"Source file not found: {src}"}
            dst.parent.mkdir(parents=True, exist_ok=True)

            if dst.exists():
                if not overwrite:
                    return {"success": False, "error": f"Destination exists: {dst}. Use overwrite=True to replace."}
                # Backup destination if overwriting and backup requested
                if backup and dst.is_file():
                    try:
                        self.create_backup(dst)
                    except Exception:
                        pass
                if dst.is_file():
                    dst.unlink()
                else:
                    return {"success": False, "error": f"Destination {dst} is a directory, expected a file"}

            # Optional backup of source before move
            if backup:
                try:
                    self.create_backup(src)
                except Exception:
                    pass

            shutil.move(str(src), str(dst))
            return {"success": True, "source": str(src), "destination": str(dst), "message": f"Moved {src} -> {dst}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to move file {src} -> {dst}: {str(e)}"}

    def copy_file(self, src: Path, dst: Path, overwrite: bool = False) -> Dict[str, Any]:
        """Copy a single file."""
        try:
            if not src.exists() or not src.is_file():
                return {"success": False, "error": f"Source file not found: {src}"}
            dst.parent.mkdir(parents=True, exist_ok=True)

            if dst.exists():
                if not overwrite:
                    return {"success": False, "error": f"Destination exists: {dst}. Use overwrite=True to replace."}
                if dst.is_file():
                    dst.unlink()
                else:
                    return {"success": False, "error": f"Destination {dst} is a directory, expected a file"}

            shutil.copy2(str(src), str(dst))
            return {"success": True, "source": str(src), "destination": str(dst), "message": f"Copied {src} -> {dst}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to copy file {src} -> {dst}: {str(e)}"}

    def move_directory(self, src: Path, dst: Path, overwrite: bool = False) -> Dict[str, Any]:
        """Move/rename a directory."""
        try:
            if not src.exists() or not src.is_dir():
                return {"success": False, "error": f"Source directory not found: {src}"}
            dst.parent.mkdir(parents=True, exist_ok=True)

            if dst.exists():
                if not overwrite:
                    return {"success": False, "error": f"Destination exists: {dst}. Use overwrite=True to replace."}
                shutil.rmtree(dst)

            shutil.move(str(src), str(dst))
            return {"success": True, "source": str(src), "destination": str(dst), "message": f"Moved directory {src} -> {dst}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to move directory {src} -> {dst}: {str(e)}"}

    def copy_directory(self, src: Path, dst: Path, overwrite: bool = False) -> Dict[str, Any]:
        """Copy a directory recursively."""
        try:
            if not src.exists() or not src.is_dir():
                return {"success": False, "error": f"Source directory not found: {src}"}
            if dst.exists():
                if not overwrite:
                    return {"success": False, "error": f"Destination exists: {dst}. Use overwrite=True to replace."}
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            return {"success": True, "source": str(src), "destination": str(dst), "message": f"Copied directory {src} -> {dst}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to copy directory {src} -> {dst}: {str(e)}"}