# miniOS 
import re 
import time
import json


# We will start with the helper functions first.
def validate_filename(name):
    if not isinstance(name,str):
        return False
    if name == "" or ".." in name:
        return False
    first_char = name[0]
    if first_char =='/' or first_char == '\\':
        return False
    pattern = r"^[a-zA-Z0-9_\-\.]+$"
    if re.fullmatch(pattern,name):
        return True
    else:
        return False
    
def parse_command_string(cmd):
    if not isinstance(cmd,str):
        return []
    tokens = []
    current = ''
    inside_quotes = False
    for char in cmd:
        if char == "'" or char =='"':
            inside_quotes = not inside_quotes
        elif char == ' ' and not inside_quotes:
            if current != '':
                tokens.append(current)
                current = ''
        else:
             current += char

    if current != '':
        tokens.append(current)
    return tokens

 
def sanitize_input(text):
    if not isinstance(text, str):
        return ""
    return text.replace(";", "").strip()


class Logger:
    def __init__(self):
        self.__entries = []

    def log(self, level, message):
        entry = {
            "ts": time.time(),
            "level": level,
            "message": message
        }
        self.__entries.append(entry)

    def get_logs(self):
        copied = []
        for entry in self.__entries:
            copied.append(dict(entry))
        return copied    

    def dump(self):
        return json.dumps(self.__entries, indent=2)

    @property
    def logs(self):
        return tuple(self.__entries)

class Process:
    def __init__(self,pid,name,cmd):
        self.pid = pid 
        self.name = name
        self.cmd = cmd
        self.status = "running"
        self.created = time.time()

    def info(self):
        return {"pid": self.pid, "name": self.name, "cmd": self.cmd, "status": self.status}
    
class ProcessManager:   # I have used a simple Round-Robin sheduling algorithm.
    def __init__(self,logger):
        self._next_pid = 1
        self._queue = []
        self._process = {}
        self.logger = logger

    def create(self,name,cmd):
        pid = self._next_pid
        self._next_pid += 1
        p = Process(pid,name,cmd)
        self._process[pid] = p
        self._queue.append(pid)
        self.logger.log("INFO", "Process created: %s (pid=%d)" % (name, pid))
        return pid 

    def kill(self,pid):
        p = self._process.get(pid)
        if not p:
            return False
        p.status = "terminated"
        if pid in self._queue:
            self._queue.remove(pid)
        self.logger.log("INFO", "Process killed: pid=%d" % pid)
        return True   # so that the kill is successful
   
    def list(self):
        result = []
        for p in self._process.values():
            result.append(p.info())
        return result
    
    def scheduler(self):
        while self._queue:
            pid = self._queue.pop(0)
            p = self._process.get(pid)
            if not p:
                continue
            if p.status == 'running':
                self._queue.append(pid)
                self.logger.log("DEBUG", "Scheduled pid=%d" % pid)
                return pid
        return None

class FileSystem:
    def __init__(self,logger):
        self._files = {}
        self.logger = logger

    def create(self,name,owner,content):
        # First we do Filename Validation
        if not validate_filename(name):
            self.logger.log("ERROR", "Incorrect File name %s " % name)
            return False
        # what if the file already exists in self.files ?
        if name in self._files:
            self.logger.log("Error","File with file name %s already exists." % name)
            return False
        self._files[name] = {"content":content,"owner":owner,"created":time.time()}
        self.logger.log("INFO","File with file name: %s is successfully created" % name)
        return True

    def read(self,name):
            if name not in self._files:
                self.logger.log("Error!", "Read failed for %s. File not found." % name)
                return None
            content = self._files[name]["content"]
            return content
    
    def write(self,name,content,owner = 'root'):
        if not validate_filename(name):
            self.logger.log("ERROR", "Incorrect File name %s " % name)
            return False
        if name not in self._files:
            self.logger.log("Error!", "Read failed for %s. File not found." % name)
            return False
        # if owner is root or the file owner matches owner name then only we allow to write content
        if self._files[name]['owner'] != owner and owner != "root":
            self.logger.log("WARN", "Write denied: %s -> %s" % (owner, name))
            return False
        self._files[name]["content"] = content
        self.logger.log("INFO", "File written: %s by %s" % (name, owner))
        return True
    
    def delete(self,name,owner = 'root'):
        if not validate_filename(name):
            self.logger.log("ERROR", "Incorrect File name %s" % name)
            return False
        if name not in self._files:
            self.logger.log("ERROR", "Read failed for %s. File not found." % name)
            return False
        if self._files[name]['owner'] != owner and owner != "root":
            self.logger.log("WARN", "Write denied: %s -> %s" % (owner, name))
            return False        
        # deletes the file content and file itself.
        del self._files[name] 
        self.logger.log("INFO", "File deleted: %s by %s" % (name, owner))
        return True
    
    def list(self):
        file_info = []
        for name in sorted(self._files.keys()):
            file_data = self._files[name] 
            file_info.append({
                'name': name,
                'owner' : file_data['owner'],
                'created': file_data['created']
            })
        return file_info
    
class User:
    def __init__(self,username,password,is_admin = False):
        self.username = username
        self.password = password
        self.created = time.time()
        self.is_admin = is_admin

class UserManager:
    def __init__(self,logger):
        self._users = {}
        self.logger = logger
        self._users['root'] = User("root","root",True)

    def add_user(self,username,password):
        if username in self._users:
            return False
        self._users[username] = User(username,password,False)
        self.logger.log("INFO", 'User %s created successfully' % username) 
        return True

    def authenticate(self,username,password):
        user = self._users.get(username)
        if user and user.password == password:
            self.logger.log("INFO", "User authenticated: %s" % username)
            return True
        else:
            self.logger.log("WARN", "Authentication failed for %s" % username)
            return False

    def is_admin(self,username,password):
        user = self._users.get(username)
        if user and user.is_admin and user.password == password:
            self.logger.log("INFO", "Admin authenticated: %s" % username)
            return True
        else:
            self.logger.log("WARN", "Admin authentication failed for %s" % username)
            return False
    
    def delete_user(self,username,admin_username,admin_password):
        # only admin can delete user:
        if not self.is_admin(admin_username,admin_password):
            self.logger.log("WARN", "Admin authentication failed.")
            return False
        
        # corner case root user should not be deleted
        if username == 'root':
            self.logger.log("ERROR", "Root user cannot be deleted")
            return False

        if username not in self._users:
            self.logger.log("ERROR", "User not detected, failed to delete")
            return False
        
        del self._users[username]
        self.logger.log("INFO", "User %s deleted successfully" % username)
        return True
    
    def list_users(self):
        users_info = []
        for username in sorted(self._users.keys()):
            user = self._users.get(username)
            users_info.append({
                'username': username,
                'is_admin': user.is_admin,
                'created': user.created
            })
        return users_info
        
    def change_password(self,username,oldpassword,newpassword):
        # user exits or not, check.
        if username not in self._users:
            self.logger.log("Error", "User %s not found." % username)
            return False

        user = self._users[username]
        if not oldpassword == user.password:
            self.logger.log("Error", "User password did not match.")
            return False
        
        user.password = newpassword
        self.logger.log("INFO", "Password changed for %s" % username)
        return True
        
class Shell:
    def __init__(self, os_ref,logger):
        self.os = os_ref
        self.logger = logger
        # dict was better approach rather than using lots of if-elif blocks
        self.commands = {
            "help": self.help_cmd,
            "ps": self.ps_cmd,
            "run": self.run_cmd,
            "kill": self.kill_cmd,
            "create": self.create_cmd,
            "read": self.read_cmd,
            "write": self.write_cmd,
            "delete": self.delete_cmd,
            "ls": self.ls_cmd,
            "whoami": self.whoami_cmd,
            "adduser": self.adduser_cmd,
            "logs": self.logs_cmd,
            "echo": self.echo_cmd,
            "cat": self.cat_cmd,
            "login": self.login_cmd,
            "logout": self.logout_cmd
        }    

    # Our Router function, main loop that handles all the user input 
    def execute(self, raw_cmd):
        raw_cmd = sanitize_input(raw_cmd)
        if not raw_cmd:
            return ""
        parts = parse_command_string(raw_cmd)
        if not parts:
            return ""
        cmd = parts[0]
        args = parts[1:]
        handler = self.commands.get(cmd)
        if handler:
            try:
                return handler(args)
            except Exception as e:
                self.logger.log("ERROR", "Error running %s: %s" % (cmd, str(e)))
                return "Error: %s" % str(e)
        return "Unknown command: %s" % cmd

    def login_cmd(self, args):
        if len(args) < 2:
                return "Usage: login <username> <password>"
            
        username = args[0]
        password = args[1]
            
        if self.os.um.authenticate(username, password):
            self.os.current_user = username
            self.logger.log("INFO", "Login successful for %s" % username)
            return "Welcome %s!" % username
        else:
            self.logger.log("WARN", "Login failed for %s" % username)
            return "Login failed: Invalid username or password"
    

    def logout_cmd(self,args):
        # check if user is login then will logout the user
        if not self.os.current_user:
            return 'User not logged In'
            
        user,self.os.current_user = self.os.current_user,None
        self.logger.log("INFO", "User %s logged out" % user)
        return "Logged out successfully"
        
    def whoami_cmd(self,args):
        return (self.os.current_user)

    def echo_cmd(self,args):
        return " ".join(args)    

    def help_cmd(self,args):
        help_text = """
                    Available Commands:
                    login <username> <password>    - Login to system
                    logout                         - Logout from system
                    whoami                         - Show current user
                    echo <text>                    - Print text
                    create <file> <content>        - Create a file
                    read <file>                    - Read a file
                    write <file> <content>         - Write to a file
                    delete <file>                  - Delete a file
                    ls                             - List all files
                    ps                             - List processes
                    run <name> <cmd>               - Run a process
                    kill <pid>                     - Kill a process
                    adduser <username> <password>  - Add user (admin only)
                    logs                           - Show logs (admin only)
                    cat <file>                     - Read file (alias for read)
                    help                           - Show this help
                    """
        return help_text
        
    def create_cmd(self,args):
        if len(args) < 2:
            return "Usage: create <file> <content>"
        filename = args[0]
        content = " ".join(args[1:])
        cmd_call = self.os.fs.create(filename,self.os.current_user,content)
        if cmd_call:
            return "File %s created successfully" % filename
        return "File creation failed"

    def read_cmd(self,args):
        if len(args) < 1:
            return "Usage: read <file>"
        filename = args[0]
        content = self.os.fs.read(filename)
        if content is not None:
            return content
        return "File not found."
    
    def ls_cmd(self,args):
        file_info = self.os.fs.list()
        if not file_info:
            return "No files found"
        files = []
        for f in file_info:
            files.append("%s (owner: %s)" % (f['name'], f['owner']))
        return '\n'.join(files)
    
    def ps_cmd(self,args):
        process = self.os.pm.list()
        if not process:
            return "No process"        
        lines = []
        for p in process:
            lines.append("%3d %-12s %s" % (p["pid"], p["name"], p["status"]))
        return '\n'.join(lines)     

    def run_cmd(self,args):
        if len(args) < 1:
            return "Usage: run <name> <cmd>"
        pname = args[0]
        cmd =  " ".join(args)
        pid = self.os.pm.create(pname, cmd)
        return "Started %s pid=%d" % (pname, pid)
    
    def kill_cmd(self, args):
        if not args:
            return "Usage: kill <pid>"
        try:
            pid = int(args[0])
        except ValueError:
            return "Invalid pid"
        ok = self.os.pm.kill(pid)
        if ok:
            return "Killed"
        return "PID not found"

    def write_cmd(self, args):
        if len(args) < 2:
            return "Usage: write <file> <content>"
        filename = args[0]
        content = " ".join(args[1:])
        ok = self.os.fs.write(filename, content, owner=self.os.current_user)
        if ok:
            return "File %s written successfully" % filename
        return "Write failed"       
    
    def delete_cmd(self,args):
        if len(args) < 1:
            return "Usage: delete <name>"
        filename = args[0]
        file = self.os.fs.delete(filename, owner=self.os.current_user)
        if file:
            return "File %s successfully deleted" % filename
        return "File deletion failed"
    
    def adduser_cmd(self,args):
        if len(args) < 2:
            return "Usage: adduser <username> <password>"
        
        if not self.os.current_user == "root":
            return "Failed only Admin can add users"

        username = args[0]
        password = args[1]

        user = self.os.um.add_user(username, password)

        if user:
            return "User %s added successfully" % username
        return "User Could not be added"
    
    def logs_cmd(self,args):
        if not self.os.current_user == "root":
            return "permission denied"        
        self.logger.log("INFO", "Logs accessed by %s" % self.os.current_user)
        log = self.os.logger.dump()
        return log
    
    def cat_cmd(self,args):
        return (self.read_cmd(args))
    
class MiniOS:
    def __init__(self):
        self.logger = Logger()
        self.fs = FileSystem(self.logger)
        self.um = UserManager(self.logger)
        self.pm = ProcessManager(self.logger)
        self.shell = Shell(self, self.logger)
        self.current_user = "root"
        self.running = False

        self.fs.create("welcome.txt", "root", "Welcome to MiniOS!")
        self.fs.create("readme.txt", "root", "Type 'help' for commands")    

    def boot(self):
        self.running = True
        self.logger.log("INFO", "System boot")
        return "MiniOS booted. Type 'help'"

    def shutdown(self):
        self.running = False
        self.logger.log("INFO", "System shutdown")
        return "Shutting down..."

    def run_command(self, cmd):
        return self.shell.execute(cmd)

    def login(self, username, password):
        ok = self.um.authenticate(username, password)
        if ok:
            self.current_user = username
            self.logger.log("INFO", "Direct login: %s" % username)
        else:
            self.logger.log("WARN", "Direct login failed for %s" % username)
        return ok
    
def main():
    osys = MiniOS()
    print(osys.boot())

    try:
        usr = input("Login username (enter for root): ").strip()
        if usr == '':
            usr = 'root'
        
        username = usr
        password = input("Password: ").strip()

        if not osys.login(username,password):
            print("Login failed. Exiting.")
            return 
        else:
            print("Welcome, %s!" % username)

    except (KeyboardInterrupt, EOFError):
        print("\nExiting.")
        return

# This kept biting me during testing  
    while osys.running:
        try:
            line = input("%s@MiniOS> " % osys.current_user).strip()
        except (KeyboardInterrupt, EOFError):
            print("\nUse 'shutdown' to stop the OS.")
            continue      

        if not line: # This means '' empty string is passed in line input
            continue

        if line == 'shutdown':
            print(osys.shutdown())
            break

        if line == "simulate-schedule":
            pid = osys.pm.scheduler()
            if pid:
                print("Scheduled pid: %d" % pid)
            else:
                print("No process scheduled")

        out = osys.run_command(line)
        print(out)

if __name__ == "__main__":
    main()



