"""
Archive Repository

Handles:
- Local program storage
- Metadata management
- Future: GitHub sync
"""

import os
import json
import time
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict


@dataclass
class ProgramMetadata:
    """Metadata for an archived program."""
    id: str                    # Unique identifier (timestamp-based)
    filename: str              # e.g., "bouncing_ball_001.py"
    program_type: str          # e.g., "bouncing_ball"
    created_at: str            # ISO timestamp
    mood: str                  # Mood when written
    success: bool              # Did it run successfully?
    lines_of_code: int
    thought_process: str       # The thinking comments
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    synced_to_github: bool = False


class Repository:
    """
    Manages the archive of generated programs.
    
    Stores programs locally with metadata, and optionally
    syncs to a GitHub repository.
    """
    
    def __init__(self, local_path: str, github_enabled: bool = False,
                 github_repo: Optional[str] = None, github_token: Optional[str] = None):
        """
        Initialize repository.
        
        Args:
            local_path: Local directory for storing programs
            github_enabled: Whether to sync to GitHub
            github_repo: GitHub repo in format "user/repo"
            github_token: GitHub personal access token
        """
        self.local_path = local_path
        self.github_enabled = github_enabled
        self.github_repo = github_repo
        self.github_token = github_token
        
        self.index_path = os.path.join(local_path, "index.json")
        self.index: List[ProgramMetadata] = []
        
        self._ensure_directories()
        self._load_index()
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        os.makedirs(self.local_path, exist_ok=True)
        os.makedirs(os.path.join(self.local_path, "programs"), exist_ok=True)
        os.makedirs(os.path.join(self.local_path, "screenshots"), exist_ok=True)
    
    def _load_index(self):
        """Load existing index from disk."""
        if os.path.exists(self.index_path):
            with open(self.index_path, 'r') as f:
                data = json.load(f)
                self.index = [ProgramMetadata(**item) for item in data]
    
    def _save_index(self):
        """Save index to disk."""
        with open(self.index_path, 'w') as f:
            json.dump([asdict(m) for m in self.index], f, indent=2)
    
    def _generate_id(self) -> str:
        """Generate unique ID for a program."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _generate_filename(self, program_type: str) -> str:
        """Generate filename for a program."""
        # Count existing programs of this type
        count = sum(1 for p in self.index if p.program_type == program_type)
        return f"{program_type}_{count + 1:03d}.py"
    
    def save(self, code: str, program_type: str, mood: str,
             success: bool, thought_process: str = "",
             error_message: Optional[str] = None) -> Optional[ProgramMetadata]:
        """
        Save a program to the archive.
        
        Args:
            code: The program source code
            program_type: Type of program
            mood: Mood when written
            success: Whether it ran successfully
            thought_process: Thinking comments
            error_message: Error if failed
            
        Returns:
            Created metadata or None if not saved
        """
        if not success:
            print(f"[Archive] Program failed, not saving to archive.")
            return None

        program_id = self._generate_id()
        filename = self._generate_filename(program_type)
        
        # Save code file
        code_path = os.path.join(self.local_path, "programs", filename)
        with open(code_path, 'w') as f:
            f.write(code)
        
        # Create metadata
        metadata = ProgramMetadata(
            id=program_id,
            filename=filename,
            program_type=program_type,
            created_at=datetime.now().isoformat(),
            mood=mood,
            success=success,
            lines_of_code=len(code.strip().split('\n')),
            thought_process=thought_process,
            error_message=error_message,
            synced_to_github=False
        )
        
        # Update index
        self.index.append(metadata)
        self._save_index()
        
        print(f"[Archive] Saved program: {filename}")
        return metadata
    
    def save_screenshot(self, program_id: str, image_data: bytes) -> str:
        """
        Save a screenshot of a running program.
        
        Args:
            program_id: ID of the program
            image_data: PNG image bytes
            
        Returns:
            Path to saved screenshot
        """
        # TODO: Save screenshot
        # TODO: Update metadata with screenshot path
        pass
    
    def get_stats(self) -> Dict:
        """Get statistics about the archive."""
        total = len(self.index)
        successful = sum(1 for p in self.index if p.success)
        by_type = {}
        for p in self.index:
            by_type[p.program_type] = by_type.get(p.program_type, 0) + 1
        
        return {
            "total_programs": total,
            "successful": successful,
            "failed": total - successful,
            "by_type": by_type,
            "synced": sum(1 for p in self.index if p.synced_to_github)
        }
    
    def get_recent(self, count: int = 10) -> List[ProgramMetadata]:
        """Get most recent programs."""
        return self.index[-count:]
    
    # =========================================================================
    # GITHUB SYNC (FUTURE IMPLEMENTATION)
    # =========================================================================
    # 
    # The methods below are pseudo-implementations for future GitHub sync.
    # They outline the intended functionality but are not yet implemented.
    #
    # To enable GitHub sync:
    # 1. Create a GitHub personal access token with repo scope
    # 2. Create a repository for the archive
    # 3. Set GITHUB_ENABLED=True in config
    # 4. Set GITHUB_REPO and GITHUB_TOKEN
    #
    # =========================================================================
    
    def sync_to_github(self):
        """
        Sync unsynced programs to GitHub.
        
        PSEUDO-IMPLEMENTATION:
        
        1. Get list of unsynced programs
           unsynced = [p for p in self.index if not p.synced_to_github]
        
        2. For each unsynced program:
           a. Read code file
           b. Create/update file via GitHub API:
              PUT /repos/{owner}/{repo}/contents/programs/{filename}
              {
                "message": f"Add {filename} - {program_type}",
                "content": base64.encode(code),
                "branch": "main"
              }
           c. If screenshot exists, upload that too
           d. Mark as synced
        
        3. Update README.md with latest stats:
           - Total programs written
           - Success rate  
           - Breakdown by type
           - Gallery of recent screenshots
        
        4. Commit README update:
           PUT /repos/{owner}/{repo}/contents/README.md
        
        5. Save updated index locally
        """
        if not self.github_enabled:
            print("[Archive] GitHub sync disabled")
            return
        
        # TODO: Implement actual sync
        print("[Archive] GitHub sync not yet implemented")
    
    def _github_api_request(self, method: str, endpoint: str, data: dict = None):
        """
        Make authenticated request to GitHub API.
        
        PSEUDO-IMPLEMENTATION:
        
        import requests
        
        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        url = f"https://api.github.com{endpoint}"
        
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        
        return response.json()
        """
        pass
    
    def _generate_readme(self) -> str:
        """
        Generate README content for the GitHub archive.
        
        PSEUDO-IMPLEMENTATION:
        
        Returns markdown like:
        
        # The Complete Works of Tiny Programmer
        
        A living archive of programs written by a tiny AI,
        one character at a time.
        
        ## Stats
        
        - **Total programs:** 142
        - **Successful runs:** 128 (90%)
        - **Days active:** 47
        
        ## Programs by Type
        
        | Type | Count |
        |------|-------|
        | bouncing_ball | 23 |
        | clock | 18 |
        | pattern | 31 |
        ...
        
        ## Recent Creations
        
        ### bouncing_ball_023.py
        *Written while feeling hopeful*
        
        ```python
        # i think this will be a good one
        # simple bouncing ball, nice and clean
        ...
        ```
        
        ---
        
        *This archive is automatically updated by Tiny Programmer.*
        """
        pass
    
    def verify_github_connection(self) -> bool:
        """
        Verify GitHub credentials and repo access.
        
        PSEUDO-IMPLEMENTATION:
        
        try:
            response = self._github_api_request("GET", f"/repos/{self.github_repo}")
            return "id" in response
        except:
            return False
        """
        pass
