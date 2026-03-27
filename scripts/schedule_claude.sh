# Schedule a claude prompt to run at a given time using `at`
# Interactive if time or prompt missing; always run from repo root.
# Usage: schedule_claude.sh [time] [prompt]
#        schedule_claude.sh list
#        schedule_claude.sh rm <job_number>
#
# AUTHENTICATION SETUP (required before first use):
#
#   Claude Code stores OAuth credentials in the macOS Keychain
#   (service: "Claude Code-credentials"). The `at` daemon runs jobs in a
#   non-interactive context that CANNOT access the login keychain, so
#   scheduled jobs will fail with "Not logged in" unless you set up a
#   file-based token first.
#
#   1. Generate a token:    claude setup-token
#   2. Save it to disk:     echo "<token>" > ~/.claude/.credentials
#                           chmod 600 ~/.claude/.credentials
#
#   This script reads ~/.claude/.credentials at schedule time and injects
#   the token as CLAUDE_CODE_OAUTH_TOKEN into the `at` job environment.

#!/bin/zsh -l

# prompt user for a value if the variable is empty
ask_if_empty() {
    local varname="$1" prompt_msg="$2"
    # use indirect expansion for the variable
    if [ -z "${!varname}" ]; then
        read -r -p "$prompt_msg" "$varname"
    fi
}

# list scheduled jobs
list_jobs() {
    local jobs
    jobs=$(atq 2>/dev/null)
    
    if [ -z "$jobs" ]; then
        echo "No scheduled jobs"
        return 0
    fi
    
    echo "Scheduled Claude Jobs:"
    echo "---"
    
    while IFS= read -r line; do
        local job_id time queue user
        job_id=$(echo "$line" | awk '{print $1}')
        time=$(echo "$line" | awk '{print $2" "$3" "$4" "$5}')
        
        # get the full command for this job
        local cmd
        cmd=$(at -c "$job_id" 2>/dev/null)
        
        # extract working directory from the command
        local working_dir
        working_dir=$(echo "$cmd" | sed -n "s/.*cd \([^ ]*\).*/\1/p" | head -1)
        
        # extract prompt from the job command
        local prompt
        prompt=$(echo "$cmd" | sed -n "s/.*-p '\([^']*\).*/\1/p" | head -1)
        
        # format and display
        printf "Job %d | Time: %s\n" "$job_id" "$time"
        printf "  Working Dir: %s\n" "$working_dir"
        printf "  Prompt: %s\n" "$prompt"
        echo
    done <<< "$jobs"
}

# remove a job
remove_job() {
    local job_id="$1"
    
    if [ -z "$job_id" ]; then
        echo "Error: job number required"
        echo "Usage: schedule_claude.sh rm <job_number>"
        return 1
    fi
    
    if ! echo "$job_id" | grep -qE '^[0-9]+$'; then
        echo "Error: job number must be an integer"
        return 1
    fi
    
    if atrm "$job_id" 2>/dev/null; then
        echo "Removed job $job_id"
    else
        echo "Error: could not remove job $job_id (may not exist)"
        return 1
    fi
}

# handle list or rm commands
if [ "$1" = "list" ]; then
    list_jobs
    exit $?
elif [ "$1" = "rm" ]; then
    remove_job "$2"
    exit $?
fi

# load oauth token from credentials file
CRED_FILE="$HOME/.claude/.credentials"
if [ ! -f "$CRED_FILE" ]; then
    echo "Error: credentials file not found at $CRED_FILE"
    echo "Run:  claude setup-token"
    echo "Then: echo \"<token>\" > $CRED_FILE && chmod 600 $CRED_FILE"
    exit 1
fi
CLAUDE_TOKEN=$(cat "$CRED_FILE" | tr -d '[:space:]')
if [ -z "$CLAUDE_TOKEN" ]; then
    echo "Error: credentials file is empty at $CRED_FILE"
    exit 1
fi

# otherwise, schedule a new job
# time may be $1
TIME="$1"
# prompt may be $2 (quotation preserved)
PROMPT="$2"

ask_if_empty TIME "Enter time for job (e.g. '5pm'): "
ask_if_empty PROMPT "Enter claude prompt: "

# compute project root (scripts directory is under project root)
CURR_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# create logs directory
mkdir -p "$CURR_DIR/.claude/logs"

# generate timestamp for log file
TIMESTAMP=$(date +%s)
LOG_FILE="$CURR_DIR/.claude/logs/job_${TIMESTAMP}.log"

# build command
# use explicit login shell invocation to ensure environment and authentication are loaded
# use full path to claude to avoid PATH issues with at jobs
BASE_COMMAND="claude --dangerously-skip-permissions --model sonnet -p '$PROMPT'"
# wrap entire command in zsh -l invocation for at, with proper escaping
FULL_COMMAND="zsh -l -c \"$BASE_COMMAND\" >> '$LOG_FILE' 2>&1"

echo "Scheduling claude job at $TIME with prompt: $PROMPT"
echo
echo "Working directory: $CURR_DIR"
echo "Output will be saved to: .claude/logs/job_${TIMESTAMP}.log"
echo

# schedule and capture output to get job ID
# explicitly set HOME for the at job to ensure ~/.claude.json is accessible
at_output=$(echo "export HOME=$HOME && export CLAUDE_CODE_OAUTH_TOKEN='$CLAUDE_TOKEN' && cd $CURR_DIR && $FULL_COMMAND" | at "$TIME" 2>&1)
echo "$at_output"

# extract job ID and display it
job_id=$(echo "$at_output" | sed -n "s/.*job \([0-9]*\).*/\1/p" | head -1)
if [ -n "$job_id" ]; then
    echo "Job ID: $job_id"
    
    # write metadata header to log file immediately
    {
        echo "====================================="
        echo "Claude Scheduled Job"
        echo "====================================="
        echo "Job ID: $job_id"
        echo "Scheduled at: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "Scheduled to run at: $TIME"
        echo "Working directory: $CURR_DIR"
        echo "Command: cd $CURR_DIR && $BASE_COMMAND"
        echo "====================================="
        echo
    } >> "$LOG_FILE"
fi