import os
import sys
import platform
import subprocess

def schedule_windows(script_path, frequency="WEEKLY"):
    """Set up Task Scheduler on Windows"""
    task_name = "FileOrganizerTask"
    
    # Check if task already exists
    check_task_cmd = f'schtasks /query /tn {task_name}'
    task_exists = subprocess.call(check_task_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
    
    if task_exists:
        print(f"Task '{task_name}' already exists. Removing it...")
        subprocess.call(f'schtasks /delete /tn {task_name} /f', shell=True)
    
    # Create new task
    # Schedule to run every Sunday at 1:00 AM
    create_task_cmd = f'schtasks /create /tn {task_name} /tr "python {script_path}" /sc {frequency} /d SUN /st 01:00'
    
    try:
        subprocess.call(create_task_cmd, shell=True)
        print(f"Task '{task_name}' created successfully to run {frequency.lower()}!")
    except Exception as e:
        print(f"Error creating task: {e}")

def schedule_unix(script_path, frequency="weekly"):
    """Set up cron job on Unix-like systems (Linux/Mac)"""
    # Get absolute path to the script
    abs_script_path = os.path.abspath(script_path)
    
    # Check if python is in the path
    python_path = sys.executable
    
    # For weekly schedule, run every Sunday at 1:00 AM
    cron_schedule = "0 1 * * 0"  # minute hour day month weekday
    
    # Command to add to crontab
    cron_command = f'{cron_schedule} {python_path} {abs_script_path}'
    
    try:
        # Check if the cron job already exists
        check_cmd = f'crontab -l | grep "{abs_script_path}"'
        job_exists = subprocess.call(check_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
        
        if job_exists:
            print("Cron job already exists. Updating it...")
            # Remove existing job
            subprocess.call(f'crontab -l | grep -v "{abs_script_path}" | crontab -', shell=True)
        
        # Add new cron job
        subprocess.call(f'(crontab -l 2>/dev/null; echo "{cron_command}") | crontab -', shell=True)
        print("Cron job added successfully to run weekly!")
    except Exception as e:
        print(f"Error setting up cron job: {e}")

def main():
    # Get path to the automatic file organizer script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    auto_organizer_path = os.path.join(script_dir, "auto_organizer.py")
    
    # Check if the file exists
    if not os.path.exists(auto_organizer_path):
        print(f"Error: Could not find auto_organizer.py in {script_dir}")
        return
    
    print("Setting up automatic scheduling for the File Organizer...")
    
    # Determine operating system and set up appropriate scheduler
    system = platform.system()
    
    print(f"Detected operating system: {system}")
    
    if system == "Windows":
        schedule_windows(auto_organizer_path)
    elif system in ["Linux", "Darwin"]:  # Darwin is macOS
        schedule_unix(auto_organizer_path)
    else:
        print(f"Sorry, scheduling is not supported on {system}.")
        print("Please set up scheduling manually.")

if __name__ == "__main__":
    main()