from pathlib import Path
import unittest


class SetupScriptTests(unittest.TestCase):
    def test_setup_windows_has_fail_fast_guards_for_dependency_steps(self) -> None:
        script = Path("setup_windows.bat").read_text(encoding="utf-8")

        self.assertIn("python -m pip install -r requirements.txt", script)
        self.assertIn("playwright install chromium", script)
        self.assertGreaterEqual(script.count("if errorlevel 1 exit /b 1"), 3)

    def test_register_task_uses_hidden_powershell_runner(self) -> None:
        script = Path("register_logon_task.ps1").read_text(encoding="utf-8")

        self.assertIn("-WindowStyle Hidden", script)
        self.assertNotIn('New-ScheduledTaskAction -Execute "cmd.exe"', script)
        self.assertIn("-PassThru", script)
        self.assertIn("-Wait", script)
        self.assertIn("exit $proc.ExitCode", script)
        self.assertIn("-RandomDelay", script)
        self.assertNotIn("Start-Sleep -Seconds", script)

    def test_install_flow_prompts_for_optional_arknights_site(self) -> None:
        script = Path("install_efcheck.bat").read_text(encoding="utf-8")

        self.assertIn("Include Arknights sign-in too?", script)
        self.assertIn("Share Endfield browser profile with Arknights?", script)
        self.assertIn("configure_sites.py", script)
        self.assertIn("capture_session.py --site endfield", script)
        self.assertIn("capture_session.py --site arknights", script)


if __name__ == "__main__":
    unittest.main()
