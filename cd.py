
from pathlib import Path
import subprocess
import sys

WORKSPACE = Path("./workspace").resolve()
MAX_FILE_SIZE = 200_000

ALLOWED_COMMANDS = {
    "test": [sys.executable, "-m", "pytest", "-q"],
    "check": [sys.executable, "-m", "compileall", "-q", "."],
}


def safe_path(relative_path: str) -> Path:
    """Only allow access to files inside the workspace."""
    target = (WORKSPACE / relative_path).resolve()

    if target != WORKSPACE and WORKSPACE not in target.parents:
        raise PermissionError("Access outside workspace is forbidden.")

    if target.is_symlink():
        raise PermissionError("Symbolic links are not allowed.")

    return target


def inspect_file(path: str) -> str:
    """Read a project file without exposing the rest of the machine."""
    target = safe_path(path)

    if not target.is_file():
        raise FileNotFoundError(path)

    if target.stat().st_size > MAX_FILE_SIZE:
        raise ValueError("File is too large to inspect.")

    return target.read_text(encoding="utf-8")


def write_file(path: str, content: str) -> str:
    """Create or update a file inside the project workspace."""
    target = safe_path(path)

    if target.suffix not in {".py", ".html", ".css", ".js", ".json", ".md"}:
        raise PermissionError("This file type is not permitted.")

    if len(content.encode("utf-8")) > MAX_FILE_SIZE:
        raise ValueError("Content exceeds the size limit.")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    return f"Updated {target.relative_to(WORKSPACE)}"


def run_check(check_name: str) -> str:
    """Run only predefined, approved project checks."""
    if check_name not in ALLOWED_COMMANDS:
        raise PermissionError("That command is not on the allowlist.")

    result = subprocess.run(
        ALLOWED_COMMANDS[check_name],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        timeout=60,
        shell=False,
    )

    output = (result.stdout + "\n" + result.stderr).strip()
    return f"Exit code: {result.returncode}\n{output[:4000]}"


def main():
    WORKSPACE.mkdir(parents=True, exist_ok=True)

    print("Forge — Autonomous Software Engineer")
    print(f"Workspace: {WORKSPACE}")
    print("Commands: read <file>, check, test, quit")

    while True:
        try:
            request = input("\nforge> ").strip()
            if not request:
                continue

            parts = request.split(maxsplit=1)
            command = parts[0].lower()

            if command == "quit":
                break
            elif command == "read" and len(parts) == 2:
                print(inspect_file(parts[1]))
            elif command in {"check", "test"}:
                print(run_check(command))
            else:
                print("Unknown command. Try read <file>, check, test, or quit.")

        except (OSError, ValueError, PermissionError, subprocess.TimeoutExpired) as error:
            print(f"Action blocked or failed: {error}")


if __name__ == "__main__":
    main()
