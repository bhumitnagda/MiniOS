# MiniOS - Mini Operating System Simulator

#### Video Demo: <URL HERE>

#### Description:

MiniOS is a mini operating system simulator. I built it to understand how operating systems actually work instead of just reading about them in theory. It has process management, file systems, user authentication, and logging.

## Components

**Logger**: Keeps a record of everything that happens in the system. Every action gets a level (INFO, WARN, ERROR, DEBUG) and a message. Pretty straightforward.

**ProcessManager**: Creates and manages processes. Uses a simple Round Robin algorithm: each process gets a turn in the queue, runs, then goes back to the end. Fair scheduling basically.

**FileSystem**: You can create, read, write, delete files. Files are stored in a dictionary with content, owner, and creation time. Only the owner or root can change or delete files. Had to enforce this to avoid breaking permissions.

**UserManager**: Handles user login and passwords. Root user exists by default and has special permissions. Only root can create users or view logs.

**Shell**: The command interface. Has 16 commands that let you actually interact with the system. Parses commands, handles quoted arguments, sends them to the right handler.

**MiniOS**: Ties everything together. Boots the system, manages who's logged in, handles shutdown.

## How to Use

```bash
python miniOS.py
```

Login:
```
Login username (enter for root): root
Password: root
```

Then use commands:
- `whoami` - Shows current user
- `create file.txt Hello` - Make a new file
- `ls` - List files
- `read file.txt` - Read file content
- `write file.txt NewText` - Update file
- `delete file.txt` - Remove file
- `ps` - List processes
- `run bash ls` - Create process
- `kill 1` - Stop a process
- `adduser john pass123` - Add user (root only)
- `logs` - View logs (root only)
- `help` - See all commands
- `shutdown` - Exit

## Features

- User login with password verification
- File creation/reading/writing/deletion with ownership
- Process creation and simple Round Robin scheduling
- Root and regular user permission levels
- System logging for everything
- Terminal with command parsing
- Error handling that doesn't crash
- Everything runs in memory, so it doesn't save anything after you shut down

## What I Learned

Building this from scratch was actually useful. You can read about how operating systems work all you want, but actually coding it is different.

The hard parts were:

- **Sharing the Logger across everything**: All components needed access to the same logger so logs didn't get scattered everywhere. Had to think about how to pass it around properly.

- **The scheduler**: Implementing Round Robin sounds simple on paper. You take from the front, run it, put it at the back. But handling process termination, checking if a process still exists, keeping the queue in sync, that's where the bugs came from.

- **File permissions**: Keeping track of who owns what and stopping users from accessing files they shouldn't. Had to check ownership every single time someone tried to modify a file.

- **Command parsing**: Handling quoted strings like `create "my file.txt" "hello world"` where spaces shouldn't split the arguments. The parser had to track whether you're inside quotes or not.

- **Error handling**: Making sure that when something goes wrong, the system tells the user what happened and keeps running. Can't have it crash because a user typed something wrong.

## Files

- `miniOS.py` - Main code
- `test_miniOS.py` - Tests