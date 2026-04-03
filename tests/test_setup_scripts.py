import unittest
from pathlib import Path


class SetupScriptTests(unittest.TestCase):
    def test_setup_windows_has_fail_fast_guards_for_dependency_steps(self) -> None:
        script = Path("setup_windows.bat").read_text(encoding="utf-8")

        self.assertIn("python -m pip install -e .", script)
        self.assertIn("doctor --install-browser", script)
        self.assertGreaterEqual(script.count("if errorlevel 1 exit /b 1"), 3)
        self.assertIn("%EFCHECK_CMD% init", script)

    def test_register_task_uses_hidden_powershell_runner(self) -> None:
        script = Path("register_logon_task.ps1").read_text(encoding="utf-8")

        self.assertIn("-WindowStyle Hidden", script)
        self.assertNotIn('New-ScheduledTaskAction -Execute "cmd.exe"', script)
        self.assertIn("-RandomDelay", script)
        self.assertNotIn("Start-Sleep -Seconds", script)
        self.assertIn("efcheck.exe", script)
        self.assertIn("-m efcheck run", script)

    def test_install_flow_prompts_for_site_selection(self) -> None:
        script = Path("install_efcheck.bat").read_text(encoding="utf-8")

        self.assertIn("Enable Endfield sign-in?", script)
        self.assertIn("Enable Arknights sign-in?", script)
        self.assertIn("Share Endfield browser profile with Arknights?", script)
        self.assertIn("--enable-site endfield", script)
        self.assertIn("--enable-site arknights", script)
        self.assertIn(" configure-sites ", script)
        self.assertIn(" capture-session --site endfield", script)
        self.assertIn(" capture-session --site arknights", script)

    def test_manual_wrappers_delegate_to_unified_cli(self) -> None:
        run_script = Path("run_signin.bat").read_text(encoding="utf-8")
        capture_script = Path("capture_session.bat").read_text(encoding="utf-8")
        register_script = Path("register_logon_task.bat").read_text(encoding="utf-8")

        self.assertIn("efcheck.exe", run_script)
        self.assertIn("-m efcheck run", run_script)
        self.assertIn("efcheck.exe", capture_script)
        self.assertIn("-m efcheck capture-session", capture_script)
        self.assertIn("efcheck.exe", register_script)
        self.assertIn("register-task", register_script)


if __name__ == "__main__":
    unittest.main()
