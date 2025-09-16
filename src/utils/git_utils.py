"""
Git utilities for DeepCode
Handles git repository operations and information
"""

import subprocess
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class GitUtils:
    def __init__(self, working_dir: str = None):
        self.working_dir = working_dir or os.getcwd()
    
    def is_git_repo(self) -> bool:
        """Check if current directory is a git repository"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def get_current_branch(self) -> Optional[str]:
        """Get current git branch name"""
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None
    
    def get_remote_url(self) -> Optional[str]:
        """Get remote origin URL"""
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None
    
    def get_commit_hash(self, short: bool = True) -> Optional[str]:
        """Get current commit hash"""
        try:
            cmd = ['git', 'rev-parse', '--short', 'HEAD'] if short else ['git', 'rev-parse', 'HEAD']
            result = subprocess.run(
                cmd,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None
    
    def get_status(self) -> Dict[str, List[str]]:
        """Get git status information"""
        status = {
            'modified': [],
            'added': [],
            'deleted': [],
            'untracked': [],
            'staged': []
        }
        
        try:
            # Get status with porcelain format
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    
                    status_code = line[:2]
                    filename = line[3:]
                    
                    if status_code[0] == 'M':  # Modified in index
                        status['staged'].append(filename)
                    elif status_code[0] == 'A':  # Added to index
                        status['staged'].append(filename)
                    elif status_code[0] == 'D':  # Deleted from index
                        status['staged'].append(filename)
                    
                    if status_code[1] == 'M':  # Modified in working tree
                        status['modified'].append(filename)
                    elif status_code[1] == 'D':  # Deleted in working tree
                        status['deleted'].append(filename)
                    elif status_code[1] == '?':  # Untracked
                        status['untracked'].append(filename)
                        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return status
    
    def get_recent_commits(self, count: int = 5) -> List[Dict[str, str]]:
        """Get recent commit information"""
        commits = []
        
        try:
            result = subprocess.run(
                ['git', 'log', f'--max-count={count}', '--pretty=format:%H|%an|%ae|%ad|%s', '--date=short'],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    
                    parts = line.split('|', 4)
                    if len(parts) >= 5:
                        commits.append({
                            'hash': parts[0][:8],  # Short hash
                            'author': parts[1],
                            'email': parts[2],
                            'date': parts[3],
                            'message': parts[4]
                        })
                        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return commits
    
    def get_file_history(self, file_path: str, count: int = 10) -> List[Dict[str, str]]:
        """Get commit history for a specific file"""
        history = []
        
        try:
            result = subprocess.run(
                ['git', 'log', f'--max-count={count}', '--pretty=format:%H|%an|%ad|%s', '--date=short', '--', file_path],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    
                    parts = line.split('|', 3)
                    if len(parts) >= 4:
                        history.append({
                            'hash': parts[0][:8],
                            'author': parts[1],
                            'date': parts[2],
                            'message': parts[3]
                        })
                        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return history
    
    def get_diff(self, file_path: str = None) -> str:
        """Get diff for file or entire repository"""
        try:
            cmd = ['git', 'diff']
            if file_path:
                cmd.extend(['--', file_path])
            
            result = subprocess.run(
                cmd,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                return result.stdout
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return ""
    
    def get_repo_info(self) -> Dict[str, any]:
        """Get comprehensive repository information"""
        return {
            'is_repo': self.is_git_repo(),
            'branch': self.get_current_branch(),
            'remote_url': self.get_remote_url(),
            'commit_hash': self.get_commit_hash(),
            'status': self.get_status(),
            'recent_commits': self.get_recent_commits()
        }
    
    def create_commit(self, message: str, files: List[str] = None) -> bool:
        """Create a commit with specified files"""
        try:
            # Add files if specified
            if files:
                for file_path in files:
                    subprocess.run(
                        ['git', 'add', file_path],
                        cwd=self.working_dir,
                        check=True,
                        timeout=10
                    )
            else:
                # Add all changes
                subprocess.run(
                    ['git', 'add', '.'],
                    cwd=self.working_dir,
                    check=True,
                    timeout=10
                )
            
            # Create commit
            result = subprocess.run(
                ['git', 'commit', '-m', message],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return result.returncode == 0
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def get_branches(self) -> List[str]:
        """Get list of all branches"""
        branches = []
        
        try:
            result = subprocess.run(
                ['git', 'branch', '-a'],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    
                    # Remove asterisk and whitespace
                    branch = line.strip('* ').strip()
                    if branch and not branch.startswith('remotes/'):
                        branches.append(branch)
                        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return branches
