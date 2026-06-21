from datetime import datetime

from datetime import datetime

def log_to_file(message: str, severity: str = "d"):
    """
    Appends a timestamped message to debug_log.txt.
    Severity 'e': ERROR with dashes.
    Severity 'w': WARN.
    Default 'd': Standard log.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if severity.lower() == "e":
        log_entry = f"[{timestamp}] ERROR ----------{message}----------\n"
    elif severity.lower() == "w":
        log_entry = f"[{timestamp}] WARN {message}\n"
    else:
        log_entry = f"[{timestamp}] {message}\n"
    
    with open("debug_log.txt", "a") as f:
        f.write(log_entry)

log_to_file("hello")
log_to_file("hello with error", "e")
log_to_file("hello with warning", "w")