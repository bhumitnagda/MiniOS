import pytest
from miniOS import validate_filename, parse_command_string, sanitize_input, Logger, FileSystem, UserManager, ProcessManager, MiniOS

class TestValidateFilename:
    def test_valid_filename(self):
        assert validate_filename("file.txt") == True
    
    def test_invalid_starts_with_slash(self):
        assert validate_filename("/file.txt") == False
        assert validate_filename('\\file.txt') == False
        assert validate_filename('file.txt..') == False

    def test_valid_parse_command_string(self):
        assert parse_command_string("'Hello World'") == ["Hello World"]
        assert parse_command_string('cat "my file.txt"') == ['cat', 'my file.txt']

    def test_invalid_parse_command_string(self):
        assert parse_command_string("echo 'world")== ['echo', 'world']
        assert parse_command_string(None)== []
        assert parse_command_string("")== []
        assert parse_command_string("echo 'test data'") == ['echo', 'test data']

class TestLogger:
    def test_log_adds_entry(self):
        logger = Logger()
        assert len(logger.get_logs()) == 0  
        logger.log("INFO", "Test message")
        assert len(logger.get_logs()) == 1
    
    def test_dump_returns_json(self):
        logger = Logger()
        logger.log("INFO", "Test")
        result = logger.dump()
        assert isinstance(result, str)  
        import json
        json.loads(result)

class TestFileSystem:
    def test_create_file(self):
        logger = Logger()
        fs = FileSystem(logger)
        result = fs.create("test.txt", "root", "hello")
        assert result == True

    def test_read_file(self):
        logger = Logger()
        fs = FileSystem(logger)
        fs.create("test.txt", "root", "hello world")
        result = fs.read("test.txt")
        assert result == "hello world"
    
    def test_delete_file(self):
        logger = Logger()
        fs = FileSystem(logger)
        fs.create("test.txt", "root", "hello")
        result = fs.delete("test.txt", owner="root")
        assert result == True
        assert fs.read("test.txt") == None

class TestUserManager:
    def test_authenticate_correct_password(self):
        logger = Logger()
        um = UserManager(logger)
        assert um.authenticate("root", "root") == True
    
    def test_authenticate_wrong_password(self):
        logger = Logger()
        um = UserManager(logger)
        assert um.authenticate("root", "wrong") == False
    
    def test_add_user(self):
        logger = Logger()
        um = UserManager(logger)
        result = um.add_user("bhu", "bhu123")
        assert result == True
        assert um.authenticate("bhu", "bhu123") == True
    
    def test_add_duplicate_user(self):
        logger = Logger()
        um = UserManager(logger)
        um.add_user("bhu", "bhu123")
        result = um.add_user("bhu", "bhu123") 
        assert result == False
    
class TestProcessManager:
    def test_create_process(self):
        logger = Logger()
        pm = ProcessManager(logger)
        pid = pm.create("bash", "ls")
        assert pid == 1 
    
    def test_create_multiple_processes(self):
        logger = Logger()
        pm = ProcessManager(logger)
        pid1 = pm.create("bash", "ls")
        pid2 = pm.create("python", "script.py")
        assert pid1 == 1
        assert pid2 == 2
    
    def test_kill_process(self):
        logger = Logger()
        pm = ProcessManager(logger)
        pid = pm.create("bash", "ls")
        result = pm.kill(pid)
        assert result == True
    
    def test_kill_nonexistent_process(self):
        logger = Logger()
        pm = ProcessManager(logger)
        result = pm.kill(999)
        assert result == False

class TestSanitizeInput:
    def test_removes_semicolon(self):
        result = sanitize_input("echo hello;rm -rf /")
        assert ";" not in result
    
    def test_strips_whitespace(self):
        result = sanitize_input("  echo hello  ")
        assert result == "echo hello"
    
    def test_non_string_input(self):
        result = sanitize_input(None)
        assert result == ""