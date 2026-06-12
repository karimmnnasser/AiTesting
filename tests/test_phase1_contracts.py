import tempfile
import unittest
from pathlib import Path

import tools.file_tools
import tools.cmd_tools
import tools.registry_tools
import tools.service_tools
import tools.user_tools
import tools.system_tools
import tools.network_tools
import tools.env_tools
import tools.power_tools
import tools.scheduled_tools
from core.executor import Executor
from schemas.tool_schema import ToolRequest, ToolResponse
from tools.registry import execute_tool, list_tools, requires_confirmation


class PhaseOneContractTests(unittest.TestCase):
    def setUp(self):
        self.executor = Executor()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmpdir.name)
        self.sample_file = self.tmp_path / "sample.txt"

    def tearDown(self):
        self.tmpdir.cleanup()

    def execute(self, action, parameters=None, confirmed=False):
        request = ToolRequest(action=action, parameters=parameters or {})
        return self.executor.execute(request, confirmed=confirmed)

    def test_tool_response_helpers_keep_message_data_and_error(self):
        ok = ToolResponse.ok("demo", data="done")
        self.assertTrue(ok.success)
        self.assertEqual(ok.message, "done")
        self.assertEqual(ok.data, "done")

        fail = ToolResponse.fail("demo", "broken")
        self.assertFalse(fail.success)
        self.assertEqual(fail.message, "broken")
        self.assertEqual(fail.error, "broken")

        confirm = ToolResponse.needs_confirmation_response("run_cmd", {"cmd": "dir"})
        self.assertTrue(confirm.needs_confirmation)
        self.assertEqual(confirm.parameters["cmd"], "dir")

    def test_class_based_safe_tools_execute_through_executor(self):
        written = self.execute("write_file", {"path": str(self.sample_file), "content": "hello"})
        self.assertTrue(written.success, written.message)
        self.assertEqual(written.action, "write_file")
        self.assertIsNotNone(written.data)

        read = self.execute("read_file", {"path": str(self.sample_file)})
        self.assertTrue(read.success, read.message)
        self.assertEqual(read.data, "hello")

        listed = self.execute("list_files", {"path": str(self.tmp_path)})
        self.assertTrue(listed.success, listed.message)
        self.assertIn("sample.txt", listed.message)

        deleted = self.execute("delete_file", {"path": str(self.sample_file)})
        self.assertTrue(deleted.success, deleted.message)

        python_result = self.execute("run_python", {"code": "print('phase1-ok')"})
        self.assertTrue(python_result.success, python_result.message)
        self.assertIn("phase1-ok", python_result.message)

        registry_result = self.execute("registry_read", {"key_path": r"HKCU\Environment"})
        self.assertIsInstance(registry_result, ToolResponse)
        self.assertEqual(registry_result.action, "registry_read")

    def test_function_based_safe_tools_execute_through_registry(self):
        result = execute_tool("power_management", action="status")
        self.assertIsInstance(result, str)

    def test_dangerous_tools_request_confirmation_without_execution(self):
        dangerous_params = {
            "run_cmd": {"cmd": "echo should-not-run"},
            "registry_write": {"key_path": "", "value_name": "", "value_data": ""},
            "service_control": {"action": "start", "service_name": "Spooler"},
            "manage_users": {"action": "list"},
            "system_power": {"action": "shutdown"},
            "network_config": {"action": "ipconfig"},
            "environment_variables": {"action": "set", "var_name": "PHASE1_TEST", "var_value": "1"},
            "scheduled_tasks": {"action": "list"},
        }

        for action, params in dangerous_params.items():
            if action not in list_tools():
                continue
            with self.subTest(action=action):
                response = self.execute(action, params)
                self.assertFalse(response.success)
                self.assertTrue(response.needs_confirmation)
                self.assertEqual(response.action, action)
                self.assertEqual(response.parameters, params)

    def test_confirmed_dangerous_tools_still_return_tool_response_for_invalid_actions(self):
        invalid_params = {
            "registry_write": {"key_path": "", "value_name": "", "value_data": ""},
            "service_control": {"action": "invalid", "service_name": "Spooler"},
            "manage_users": {"action": "invalid"},
            "system_power": {"action": "invalid"},
            "network_config": {"action": "invalid"},
            "environment_variables": {"action": "invalid"},
            "scheduled_tasks": {"action": "invalid"},
        }

        for action, params in invalid_params.items():
            if action not in list_tools():
                continue
            with self.subTest(action=action):
                response = self.execute(action, params, confirmed=True)
                self.assertIsInstance(response, ToolResponse)
                self.assertEqual(response.action, action)
                self.assertFalse(response.needs_confirmation)

    def test_all_registered_tools_have_contract_coverage(self):
        covered = {
            "write_file",
            "read_file",
            "list_files",
            "delete_file",
            "run_cmd",
            "run_python",
            "registry_read",
            "registry_write",
            "service_control",
            "manage_users",
            "system_power",
            "network_config",
            "environment_variables",
            "power_management",
            "scheduled_tasks",
        }
        self.assertEqual(set(list_tools()), covered)
        for action in list_tools():
            self.assertIsInstance(requires_confirmation(action), bool)


if __name__ == "__main__":
    unittest.main()
