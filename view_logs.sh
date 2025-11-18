#!/bin/bash

# AKILIMO Nigeria Log Viewer
# Helper script to view and monitor application logs

LOG_DIR="logs"
COLOR_RED='\033[0;31m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_BLUE='\033[0;34m'
COLOR_NC='\033[0m' # No Color

# Function to display menu
show_menu() {
    echo -e "${COLOR_GREEN}================================${COLOR_NC}"
    echo -e "${COLOR_GREEN}   AKILIMO Nigeria Log Viewer   ${COLOR_NC}"
    echo -e "${COLOR_GREEN}================================${COLOR_NC}"
    echo ""
    echo "1) View ERROR logs (latest 50 lines)"
    echo "2) View ALL logs (latest 50 lines)"
    echo "3) View DEBUG logs (latest 50 lines)"
    echo "4) View DATABASE logs (latest 50 lines)"
    echo "5) Monitor ERROR logs (live tail)"
    echo "6) Monitor ALL logs (live tail)"
    echo "7) Search logs for specific text"
    echo "8) View logs from last hour"
    echo "9) Clear all logs"
    echo "10) Show log file sizes"
    echo "0) Exit"
    echo ""
}

# Function to check if logs directory exists
check_logs_dir() {
    if [ ! -d "$LOG_DIR" ]; then
        echo -e "${COLOR_RED}Error: Logs directory not found!${COLOR_NC}"
        echo "Creating logs directory..."
        mkdir -p "$LOG_DIR"
    fi
}

# Function to view error logs
view_error_logs() {
    local log_file="$LOG_DIR/akilimo_nigeria_error.log"
    if [ -f "$log_file" ]; then
        echo -e "${COLOR_RED}=== ERROR LOGS (Last 50 lines) ===${COLOR_NC}"
        tail -n 50 "$log_file"
    else
        echo -e "${COLOR_YELLOW}No error log file found yet.${COLOR_NC}"
    fi
}

# Function to view all logs
view_all_logs() {
    local log_file="$LOG_DIR/akilimo_nigeria.log"
    if [ -f "$log_file" ]; then
        echo -e "${COLOR_BLUE}=== ALL LOGS (Last 50 lines) ===${COLOR_NC}"
        tail -n 50 "$log_file"
    else
        echo -e "${COLOR_YELLOW}No log file found yet.${COLOR_NC}"
    fi
}

# Function to view debug logs
view_debug_logs() {
    local log_file="$LOG_DIR/akilimo_nigeria_debug.log"
    if [ -f "$log_file" ]; then
        echo -e "${COLOR_BLUE}=== DEBUG LOGS (Last 50 lines) ===${COLOR_NC}"
        tail -n 50 "$log_file"
    else
        echo -e "${COLOR_YELLOW}No debug log file found yet.${COLOR_NC}"
    fi
}

# Function to view database logs
view_db_logs() {
    local log_file="$LOG_DIR/akilimo_nigeria_db.log"
    if [ -f "$log_file" ]; then
        echo -e "${COLOR_BLUE}=== DATABASE LOGS (Last 50 lines) ===${COLOR_NC}"
        tail -n 50 "$log_file"
    else
        echo -e "${COLOR_YELLOW}No database log file found yet.${COLOR_NC}"
    fi
}

# Function to monitor error logs
monitor_error_logs() {
    local log_file="$LOG_DIR/akilimo_nigeria_error.log"
    if [ -f "$log_file" ]; then
        echo -e "${COLOR_RED}=== MONITORING ERROR LOGS (Press Ctrl+C to stop) ===${COLOR_NC}"
        tail -f "$log_file"
    else
        echo -e "${COLOR_YELLOW}No error log file found yet. Waiting for logs...${COLOR_NC}"
        touch "$log_file"
        tail -f "$log_file"
    fi
}

# Function to monitor all logs
monitor_all_logs() {
    local log_file="$LOG_DIR/akilimo_nigeria.log"
    if [ -f "$log_file" ]; then
        echo -e "${COLOR_BLUE}=== MONITORING ALL LOGS (Press Ctrl+C to stop) ===${COLOR_NC}"
        tail -f "$log_file"
    else
        echo -e "${COLOR_YELLOW}No log file found yet. Waiting for logs...${COLOR_NC}"
        touch "$log_file"
        tail -f "$log_file"
    fi
}

# Function to search logs
search_logs() {
    echo -e "${COLOR_YELLOW}Enter search term:${COLOR_NC}"
    read search_term

    echo -e "${COLOR_GREEN}Searching all log files for: '$search_term'${COLOR_NC}"
    echo ""

    for log_file in "$LOG_DIR"/*.log; do
        if [ -f "$log_file" ]; then
            local results=$(grep -i "$search_term" "$log_file" 2>/dev/null)
            if [ ! -z "$results" ]; then
                echo -e "${COLOR_BLUE}=== Results from $(basename $log_file) ===${COLOR_NC}"
                echo "$results"
                echo ""
            fi
        fi
    done
}

# Function to view recent logs
view_recent_logs() {
    echo -e "${COLOR_GREEN}=== Logs from last hour ===${COLOR_NC}"
    local one_hour_ago=$(date -v-1H +"%Y-%m-%d %H:%M:%S" 2>/dev/null || date -d "1 hour ago" +"%Y-%m-%d %H:%M:%S")

    for log_file in "$LOG_DIR"/*.log; do
        if [ -f "$log_file" ]; then
            echo -e "${COLOR_BLUE}--- $(basename $log_file) ---${COLOR_NC}"
            awk -v since="$one_hour_ago" '$0 >= since' "$log_file" | tail -n 20
            echo ""
        fi
    done
}

# Function to clear logs
clear_logs() {
    echo -e "${COLOR_RED}WARNING: This will delete all log files!${COLOR_NC}"
    echo -e "${COLOR_YELLOW}Are you sure? (yes/no)${COLOR_NC}"
    read confirmation

    if [ "$confirmation" = "yes" ]; then
        rm -f "$LOG_DIR"/*.log
        echo -e "${COLOR_GREEN}All logs cleared!${COLOR_NC}"
    else
        echo "Operation cancelled."
    fi
}

# Function to show log sizes
show_log_sizes() {
    echo -e "${COLOR_GREEN}=== Log File Sizes ===${COLOR_NC}"
    if [ -d "$LOG_DIR" ]; then
        du -h "$LOG_DIR"/*.log 2>/dev/null | while read size file; do
            echo -e "${COLOR_BLUE}$size${COLOR_NC} - $(basename $file)"
        done
        echo ""
        echo -e "${COLOR_GREEN}Total:${COLOR_NC} $(du -sh "$LOG_DIR" | cut -f1)"
    else
        echo -e "${COLOR_YELLOW}No logs directory found.${COLOR_NC}"
    fi
}

# Main loop
check_logs_dir

while true; do
    show_menu
    read -p "Select an option: " choice

    case $choice in
        1) view_error_logs ;;
        2) view_all_logs ;;
        3) view_debug_logs ;;
        4) view_db_logs ;;
        5) monitor_error_logs ;;
        6) monitor_all_logs ;;
        7) search_logs ;;
        8) view_recent_logs ;;
        9) clear_logs ;;
        10) show_log_sizes ;;
        0)
            echo -e "${COLOR_GREEN}Goodbye!${COLOR_NC}"
            exit 0
            ;;
        *)
            echo -e "${COLOR_RED}Invalid option!${COLOR_NC}"
            ;;
    esac

    echo ""
    echo -e "${COLOR_YELLOW}Press Enter to continue...${COLOR_NC}"
    read
done
