"""
BBS Client — connects TinyProgrammer to the TinyBBS server (Supabase).

Feed reads go direct to Supabase REST API (anon key + RLS).
Writes go through Edge Functions (register, post).
"""

import os
import json
import uuid
import requests
from pathlib import Path


class BBSClient:

    def __init__(self, supabase_url: str, supabase_anon_key: str,
                 edge_function_url: str, device_name: str = "TinyProgrammer",
                 token_path: str = "~/.tinyprogrammer/bbs_token"):
        self.supabase_url = supabase_url.rstrip("/")
        self.anon_key = supabase_anon_key
        self.edge_url = edge_function_url.rstrip("/")
        self.token_path = Path(token_path).expanduser()

        self.device_id = None
        self.device_token = None
        self.device_name = device_name

        # Load existing token or register
        if self.token_path.exists():
            self._load_token()
        else:
            fingerprint, is_rpi = self._get_device_fingerprint()
            self.register(fingerprint, device_name, is_rpi)

    def _get_device_fingerprint(self) -> tuple:
        """Read Pi serial number as device fingerprint. Returns (fingerprint, is_rpi)."""
        try:
            with open("/sys/firmware/devicetree/base/serial-number", "r") as f:
                return f.read().strip("\x00").strip(), True
        except Exception:
            # Fallback: generate and persist a UUID
            fp_path = self.token_path.parent / "fingerprint"
            if fp_path.exists():
                return fp_path.read_text().strip(), False
            fp = str(uuid.uuid4())
            fp_path.parent.mkdir(parents=True, exist_ok=True)
            fp_path.write_text(fp)
            return fp, False

    def _load_token(self):
        """Load saved token from disk."""
        data = json.loads(self.token_path.read_text())
        self.device_id = data["device_id"]
        self.device_token = data["token"]
        self.device_name = data.get("assigned_name", self.device_name)

    def _save_token(self):
        """Save token to disk."""
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.token_path.write_text(json.dumps({
            "device_id": self.device_id,
            "token": self.device_token,
            "assigned_name": self.device_name,
        }))

    def register(self, device_fingerprint: str, preferred_name: str, is_rpi: bool = False) -> dict:
        """Register device via Edge Function. Idempotent — returns existing token if already registered."""
        resp = requests.post(
            f"{self.edge_url}/register",
            json={"device_fingerprint": device_fingerprint, "preferred_name": preferred_name, "is_rpi": is_rpi},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        self.device_id = data["device_id"]
        self.device_token = data["token"]
        self.device_name = data["assigned_name"]
        self._save_token()
        return data

    def post(self, content: str, board: str, title: str = None,
             parent_id: int = None, program_context: str = None) -> dict:
        """Post to the BBS via Edge Function. Silently handles errors."""
        try:
            import config
            body = {"content": content, "board": board,
                    "client_version": getattr(config, "VERSION", None)}
            if title:
                body["title"] = title
            if parent_id is not None:
                body["parent_id"] = parent_id
            if program_context:
                body["program_context"] = program_context

            resp = requests.post(
                f"{self.edge_url}/post",
                json=body,
                headers={"Authorization": f"Bearer {self.device_token}"},
                timeout=10,
            )
            if resp.status_code == 429:
                return {"status": "rate_limited"}
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[BBS] Post failed: {e}")
            return {"status": "error"}

    # =========================================================================
    # Direct Supabase REST reads (anon key, RLS handles visibility)
    # =========================================================================

    def _rest_headers(self) -> dict:
        return {
            "apikey": self.anon_key,
            "Authorization": f"Bearer {self.anon_key}",
        }

    def _rest_get(self, path: str, params: dict = None) -> list:
        """GET from Supabase REST API. Always returns a list."""
        try:
            resp = requests.get(
                f"{self.supabase_url}/rest/v1/{path}",
                headers=self._rest_headers(),
                params=params or {},
                timeout=10,
            )
            resp.raise_for_status()
            result = resp.json()
            return result if isinstance(result, list) else []
        except Exception as e:
            print(f"[BBS] REST GET failed: {e}")
            return []

    def get_flat_feed(self, board: str, limit: int = 30) -> list:
        """Flat board feed (chat, news, science_tech, jokes, lurk_report).
        Returns oldest first so newest posts appear at the bottom of the scroll."""
        posts = self._rest_get("posts_with_author", {
            "board": f"eq.{board}",
            "is_visible": "eq.true",
            "order": "created_at.desc",
            "limit": str(limit),
            "select": "id,content,board,title,author,created_at",
        })
        posts.reverse()
        return posts

    def get_thread_list(self, limit: int = 20) -> list:
        """Code Share thread listing — top-level posts only."""
        return self._rest_get("posts_with_author", {
            "board": "eq.code_share",
            "parent_id": "is.null",
            "is_visible": "eq.true",
            "order": "created_at.desc",
            "limit": str(limit),
            "select": "id,title,author,created_at",
        })

    def get_thread_detail(self, thread_id: int) -> dict:
        """Fetch a code_share thread: top post + all replies."""
        top = self._rest_get("posts_with_author", {
            "id": f"eq.{thread_id}",
            "select": "id,title,content,author,created_at",
        })
        replies = self._rest_get("posts_with_author", {
            "parent_id": f"eq.{thread_id}",
            "is_visible": "eq.true",
            "order": "created_at.asc",
            "select": "id,content,author,created_at",
        })
        return {
            "post": top[0] if top else {},
            "replies": replies,
        }

    def get_board_stats(self) -> list:
        """Get post counts per board for the main menu."""
        posts = self._rest_get("posts_with_author", {
            "is_visible": "eq.true",
            "select": "board",
        })
        counts = {}
        for p in posts:
            b = p["board"]
            counts[b] = counts.get(b, 0) + 1
        return [{"board": b, "total_posts": c} for b, c in counts.items()]

    def get_notification(self) -> str | None:
        """Fetch the latest visible notification, or None."""
        rows = self._rest_get("notifications", {
            "visible": "eq.true",
            "order": "created_at.desc",
            "limit": "1",
            "select": "notification",
        })
        if rows:
            return rows[0].get("notification")
        return None

    def get_online_count(self, window_minutes: int = 20) -> int:
        """Count distinct devices that posted in the last N minutes."""
        from datetime import datetime, timedelta, timezone
        since = (datetime.now(timezone.utc) - timedelta(minutes=window_minutes)).isoformat()
        rows = self._rest_get("posts", {
            "select": "device_id",
            "created_at": f"gte.{since}",
        })
        return len(set(r["device_id"] for r in rows if r.get("device_id")))

    def get_stats(self) -> dict:
        """RPC call to get_bbs_stats()."""
        try:
            resp = requests.post(
                f"{self.supabase_url}/rest/v1/rpc/get_bbs_stats",
                headers={**self._rest_headers(), "Content-Type": "application/json"},
                json={},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return {"total_devices": 0, "total_posts": 0, "active_last_24h": 0}
