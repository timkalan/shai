import os
import shlex
import subprocess
import re


class ShellExecutor:
    """
    A class to execute shell commands in a subprocess.
    """

    def __init__(self):
        self.cwd = os.getcwd()

    def run(self, command: str):
        command = command.strip()

        if command.startswith("cd "):
            return self._handle_cd(command)

        if self._is_unsupported(command):
            print(f"⚠️ Skipping unsupported shell command: {command}")
            return

        try:
            subprocess.run(command, shell=True, cwd=self.cwd)
        except Exception as e:
            print(f"❌ Error running command: {e}")

    def _handle_cd(self, command: str):
        try:
            parts = shlex.split(command)
            if len(parts) < 2:
                print("❌ No directory specified.")
                return
            new_dir = os.path.abspath(os.path.join(self.cwd, parts[1]))
            os.chdir(new_dir)
            self.cwd = new_dir
            print(f"📁 Changed directory to {self.cwd}")
        except Exception as e:
            print(f"❌ Failed to change directory: {e}")

    def _is_unsupported(self, command: str) -> bool:
        # Add more as needed
        unsupported_patterns = [
            r"^\s*(export|alias|unalias|source|\.)\b",
        ]
        return any(re.match(pattern, command) for pattern in unsupported_patterns)
