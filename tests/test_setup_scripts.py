import unittest
from pathlib import Path


class SetupScriptTests(unittest.TestCase):
    def test_batch_wrappers_are_saved_without_utf8_bom(self) -> None:
        for path in [
            Path("setup_windows.bat"),
            Path("install_skport_signin.bat"),
            Path("capture_session.bat"),
            Path("register_logon_task.bat"),
            Path("run_signin.bat"),
        ]:
            contents = path.read_bytes()
            self.assertFalse(
                contents.startswith(b"\xef\xbb\xbf"),
                f"{path} should not start with a UTF-8 BOM",
            )

    def test_setup_windows_has_fail_fast_guards_for_dependency_steps(self) -> None:
        script = Path("setup_windows.bat").read_text(encoding="utf-8")

        self.assertIn('"%VENV_PY%" -m pip install -e .', script)
        self.assertIn("doctor --install-browser", script)
        self.assertGreaterEqual(script.count("if errorlevel 1 exit /b 1"), 3)
        self.assertIn("%SKPORT_SIGNIN_CMD% init", script)
        self.assertNotIn("activate.bat", script)
        self.assertIn("Existing virtual environment is invalid. Recreating .venv...", script)
        self.assertIn('"%VENV_PY%" -c "import sys" >nul 2>nul', script)
        self.assertIn("call :resolve_python_cmd", script)
        self.assertIn('%USERPROFILE%\\AppData\\Local', script)
        self.assertIn('%LOCAL_APPDATA_DIR%\\Programs\\Python\\Launcher\\py.exe', script)
        self.assertIn("rmdir /s /q \".venv\"", script)

    def test_register_task_uses_hidden_powershell_runner(self) -> None:
        script = Path("register_logon_task.ps1").read_text(encoding="utf-8")

        self.assertIn("-WindowStyle Hidden", script)
        self.assertNotIn('New-ScheduledTaskAction -Execute "cmd.exe"', script)
        self.assertIn("-RandomDelay", script)
        self.assertNotIn("Start-Sleep -Seconds", script)
        self.assertIn("skport_signin.exe", script)
        self.assertIn("-m skport_signin run", script)
        self.assertLess(
            script.index(".\\.venv\\Scripts\\python.exe"),
            script.index(".\\.venv\\Scripts\\pythonw.exe"),
        )

    def test_install_flow_delegates_to_setup_command(self) -> None:
        script = Path("install_skport_signin.bat").read_text(encoding="utf-8")

        self.assertIn(" setup --interactive", script)
        self.assertNotIn("Enable Endfield sign-in?", script)
        self.assertNotIn("Enable Arknights sign-in?", script)
        self.assertNotIn("Share Endfield browser profile with Arknights?", script)
        self.assertNotIn(" configure-sites ", script)
        self.assertIn("call :has_working_venv", script)
        self.assertIn("Failed while running the guided setup flow.", script)

    def test_manual_wrappers_delegate_to_unified_cli(self) -> None:
        run_script = Path("run_signin.bat").read_text(encoding="utf-8")
        capture_script = Path("capture_session.bat").read_text(encoding="utf-8")
        register_script = Path("register_logon_task.bat").read_text(encoding="utf-8")

        self.assertIn("skport_signin.exe", run_script)
        self.assertIn("-m skport_signin run", run_script)
        self.assertIn("skport_signin.exe", capture_script)
        self.assertIn("-m skport_signin capture-session", capture_script)
        self.assertIn("skport_signin.exe", register_script)
        self.assertIn("register-task", register_script)
        self.assertIn("call :has_working_venv", run_script)
        self.assertIn("call :has_working_venv", capture_script)
        self.assertIn("call :has_working_venv", register_script)


if __name__ == "__main__":
    unittest.main()
