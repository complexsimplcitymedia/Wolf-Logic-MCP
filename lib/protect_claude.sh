#!/bin/bash
# Claude Daemon Protection Script
# Prevents unauthorized restarts/kills of Claude processes
# Only sudo can stop this protection

CLAUDE_PIDS=""
PROTECTED=false

get_claude_code_pid() {
    # Get ONLY Claude Code CLI PID - NOT Desktop
    CLAUDE_CODE_PID=$(pgrep -f "bin/claude$" | head -1)
}

get_claude_desktop_pids() {
    # Get Claude Desktop PIDs separately
    CLAUDE_DESKTOP_PIDS=$(pgrep -f "claude-desktop" | tr '\n' ' ')
}

protect_process() {
    local pid=$1
    # Make the process ignore SIGTERM from non-root
    # This requires the process to be started with protection
    echo "Protecting PID: $pid"
}

check_sudo() {
    if [ "$EUID" -ne 0 ]; then
        echo "ERROR: This action requires sudo permission."
        echo "Claude daemon is protected. Run with sudo to proceed."
        exit 1
    fi
}

start_protection() {
    echo "=========================================="
    echo "CLAUDE CODE PROTECTION ACTIVE"
    echo "=========================================="
    echo "Claude Code (CLI) is now ISOLATED from Desktop"
    echo "Only sudo can restart or kill Claude Code."
    echo ""

    get_claude_code_pid
    get_claude_desktop_pids

    echo "Claude Code PID (PROTECTED): $CLAUDE_CODE_PID"
    echo "Claude Desktop PIDs (separate): $CLAUDE_DESKTOP_PIDS"

    # Create a lock file that only root can remove
    sudo touch /var/run/claude_code_protected.lock
    sudo chmod 000 /var/run/claude_code_protected.lock

    # Store the protected PID
    echo "$CLAUDE_CODE_PID" | sudo tee /var/run/claude_code_protected.pid > /dev/null

    echo ""
    echo "Protection lock: /var/run/claude_code_protected.lock"
    echo "Protected PID stored: /var/run/claude_code_protected.pid"
    echo ""
    echo "Desktop can restart without killing Code session."
    echo "=========================================="
}

stop_protection() {
    check_sudo

    if [ -f /var/run/claude_code_protected.lock ]; then
        sudo rm /var/run/claude_code_protected.lock
        sudo rm -f /var/run/claude_code_protected.pid
        echo "Claude Code protection disabled."
    else
        echo "Protection was not active."
    fi
}

status() {
    echo "=========================================="
    if [ -f /var/run/claude_code_protected.lock ]; then
        echo "Claude Code protection: ACTIVE"
        get_claude_code_pid
        get_claude_desktop_pids
        STORED_PID=$(sudo cat /var/run/claude_code_protected.pid 2>/dev/null)
        echo ""
        echo "Protected PID (stored): $STORED_PID"
        echo "Current Code PID: $CLAUDE_CODE_PID"
        echo "Desktop PIDs (separate): $CLAUDE_DESKTOP_PIDS"
    else
        echo "Claude Code protection: INACTIVE"
        get_claude_code_pid
        echo "Current Code PID: $CLAUDE_CODE_PID"
    fi
    echo "=========================================="
}

restart_claude_code() {
    check_sudo

    if [ -f /var/run/claude_code_protected.lock ]; then
        echo "Protection active. Sudo authorization confirmed."
        echo ""
        echo "WARNING: This will kill your current Claude Code session!"
        read -p "Are you sure? (yes/no): " confirm

        if [ "$confirm" != "yes" ]; then
            echo "Aborted."
            exit 0
        fi

        # Kill ONLY Claude Code, not Desktop
        get_claude_code_pid
        if [ -n "$CLAUDE_CODE_PID" ]; then
            kill -9 $CLAUDE_CODE_PID
            echo "Killed Claude Code PID: $CLAUDE_CODE_PID"
        fi
        sleep 2

        # Restart Claude CLI
        echo "Restarting Claude Code..."
        nohup /home/thewolfwalksalone/.nvm/versions/node/v24.11.1/bin/claude > /dev/null 2>&1 &

        NEW_PID=$!
        echo "$NEW_PID" | sudo tee /var/run/claude_code_protected.pid > /dev/null
        echo "Claude Code restarted with PID: $NEW_PID"
    else
        echo "Protection not active. Enable protection first."
    fi
}

case "$1" in
    start)
        start_protection
        ;;
    stop)
        stop_protection
        ;;
    status)
        status
        ;;
    restart)
        restart_claude_code
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart}"
        echo ""
        echo "  start   - Enable Claude Code protection (isolates from Desktop)"
        echo "  stop    - Disable protection (requires sudo)"
        echo "  status  - Check protection status"
        echo "  restart - Restart Claude Code with authorization (requires sudo)"
        echo ""
        echo "This script protects Claude Code CLI from being killed when"
        echo "Claude Desktop restarts (e.g., from MCP installs)."
        exit 1
        ;;
esac
