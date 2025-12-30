"""Terraform execution wrapper for integration testing.

Provides a simplified interface for running Terraform commands in
temporary working directories with proper cleanup.
"""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional


class TerraformRunner:
    """Wrapper for executing Terraform commands in isolated environments."""

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize Terraform runner.

        Args:
            config_dir: Directory containing Terraform configuration files.
                       If None, uses the main terraform/ directory.
        """
        self.repo_root = Path("/workspaces/boycivenga-iac")
        self.config_dir = config_dir or self.repo_root / "terraform"

        # Create temporary working directory for this test
        self.work_dir = Path(tempfile.mkdtemp(prefix="tf-test-"))

        # Copy Terraform configuration to working directory
        self._copy_config()

        self.initialized = False

    def _copy_config(self) -> None:
        """Copy Terraform configuration files to working directory."""
        if not self.config_dir.exists():
            raise FileNotFoundError(f"Config directory not found: {self.config_dir}")

        for tf_file in self.config_dir.glob("*.tf"):
            shutil.copy(tf_file, self.work_dir)

        # Copy lock file if it exists
        lock_file = self.config_dir / ".terraform.lock.hcl"
        if lock_file.exists():
            shutil.copy(lock_file, self.work_dir)

    def _run_command(
        self, cmd: List[str], check: bool = True, capture_output: bool = True
    ) -> subprocess.CompletedProcess:
        """Run a command in the working directory.

        Args:
            cmd: Command and arguments as list
            check: Raise exception on non-zero exit code
            capture_output: Capture stdout and stderr

        Returns:
            CompletedProcess instance
        """
        return subprocess.run(
            cmd,
            cwd=self.work_dir,
            check=check,
            capture_output=capture_output,
            text=True,
        )

    def init(self) -> None:
        """Run terraform init."""
        self._run_command(["terraform", "init", "-no-color"])
        self.initialized = True

    def validate(self) -> bool:
        """Run terraform validate.

        Returns:
            True if validation passes
        """
        if not self.initialized:
            self.init()

        result = self._run_command(["terraform", "validate", "-json"])
        validation = json.loads(result.stdout)
        return validation.get("valid", False)

    def plan(
        self, var_file: Optional[Path] = None, destroy: bool = False
    ) -> Dict[str, Any]:
        """Run terraform plan and return parsed output.

        Args:
            var_file: Path to tfvars file (optional)
            destroy: Generate destroy plan

        Returns:
            Parsed plan as dictionary
        """
        if not self.initialized:
            self.init()

        cmd = ["terraform", "plan", "-out=tfplan", "-json", "-no-color"]

        if var_file:
            cmd.append(f"-var-file={var_file}")

        if destroy:
            cmd.append("-destroy")

        result = self._run_command(cmd)

        # Parse JSON output (line-delimited JSON from Terraform)
        plan_lines = result.stdout.strip().split("\n")
        plan_data = {}

        for line in plan_lines:
            if line.strip():
                try:
                    data = json.loads(line)
                    if data.get("type") == "planned_change":
                        plan_data.setdefault("changes", []).append(data)
                except json.JSONDecodeError:
                    pass

        return plan_data

    def apply(self, auto_approve: bool = True) -> None:
        """Run terraform apply.

        Args:
            auto_approve: Skip approval prompt
        """
        if not self.initialized:
            self.init()

        cmd = ["terraform", "apply", "-no-color"]

        if auto_approve:
            cmd.append("-auto-approve")

        self._run_command(cmd)

    def destroy(self, auto_approve: bool = True) -> None:
        """Run terraform destroy.

        Args:
            auto_approve: Skip approval prompt
        """
        if not self.initialized:
            self.init()

        cmd = ["terraform", "destroy", "-no-color"]

        if auto_approve:
            cmd.append("-auto-approve")

        self._run_command(cmd, check=False)  # Don't fail if nothing to destroy

    def get_state(self) -> Dict[str, Any]:
        """Get current Terraform state.

        Returns:
            Parsed state as dictionary
        """
        if not self.initialized:
            self.init()

        result = self._run_command(["terraform", "show", "-json"])
        return json.loads(result.stdout)

    def get_outputs(self) -> Dict[str, Any]:
        """Get Terraform outputs.

        Returns:
            Dictionary of outputs
        """
        if not self.initialized:
            self.init()

        result = self._run_command(["terraform", "output", "-json"])
        return json.loads(result.stdout)

    def write_tfvars(
        self, variables: Dict[str, Any], filename: str = "test.tfvars.json"
    ) -> Path:
        """Write variables to a tfvars JSON file in the working directory.

        Args:
            variables: Dictionary of variables
            filename: Filename for tfvars file

        Returns:
            Path to created file
        """
        tfvars_file = self.work_dir / filename
        with open(tfvars_file, "w") as f:
            json.dump(variables, f, indent=2)
        return tfvars_file

    def cleanup(self) -> None:
        """Remove temporary working directory."""
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        try:
            # Try to destroy any created resources
            if self.initialized:
                self.destroy()
        except Exception:
            pass  # Best effort cleanup
        finally:
            self.cleanup()
