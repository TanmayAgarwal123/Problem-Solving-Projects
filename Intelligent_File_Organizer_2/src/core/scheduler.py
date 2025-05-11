import schedule
import time
import threading
import json
import os
from datetime import datetime
import logging
import platform

# Try to import Windows-specific modules
WINDOWS_SUPPORT = False
if platform.system() == "Windows":
    try:
        import win32com.client
        WINDOWS_SUPPORT = True
    except ImportError:
        logging.warning("pywin32 not available, Windows Task Scheduler features disabled")

logger = logging.getLogger(__name__)

class ScheduleManager:
    def __init__(self):
        self.scheduled_jobs = {}
        self.running = False
        self.scheduler_thread = None
        self.jobs_file = "scheduled_jobs.json"
        self._load_jobs()
    
    def _load_jobs(self):
        """Load scheduled jobs from file"""
        if os.path.exists(self.jobs_file):
            try:
                with open(self.jobs_file, 'r') as f:
                    self.scheduled_jobs = json.load(f)
            except:
                self.scheduled_jobs = {}
    
    def _save_jobs(self):
        """Save scheduled jobs to file"""
        with open(self.jobs_file, 'w') as f:
            json.dump(self.scheduled_jobs, f, indent=2)
    
    def add_schedule(self, job_id, folder_path, schedule_type, time_value=None):
        """Add a new scheduled job"""
        job_info = {
            "id": job_id,
            "folder": folder_path,
            "schedule_type": schedule_type,
            "time_value": time_value,
            "created_at": datetime.now().isoformat(),
            "last_run": None,
            "next_run": None,
            "status": "active"
        }
        
        # Add to Windows Task Scheduler if on Windows and available
        if WINDOWS_SUPPORT:
            self._add_windows_task(job_id, folder_path, schedule_type, time_value)
        
        # Add to internal scheduler
        self._add_internal_schedule(job_info)
        
        self.scheduled_jobs[job_id] = job_info
        self._save_jobs()
        
        logger.info(f"Added schedule {job_id} for {folder_path}")
        return job_id
    
    def remove_schedule(self, job_id):
        """Remove a scheduled job"""
        if job_id in self.scheduled_jobs:
            # Remove from Windows Task Scheduler
            if WINDOWS_SUPPORT:
                self._remove_windows_task(job_id)
            
            # Remove from internal scheduler
            schedule.clear(job_id)
            
            del self.scheduled_jobs[job_id]
            self._save_jobs()
            
            logger.info(f"Removed schedule {job_id}")
            return True
        return False
    
    def list_schedules(self):
        """List all scheduled jobs"""
        return list(self.scheduled_jobs.values())
    
    def get_schedule(self, job_id):
        """Get details of a specific schedule"""
        return self.scheduled_jobs.get(job_id)
    
    def update_schedule(self, job_id, **kwargs):
        """Update a scheduled job"""
        if job_id in self.scheduled_jobs:
            job_info = self.scheduled_jobs[job_id]
            job_info.update(kwargs)
            
            # Update Windows Task Scheduler
            if WINDOWS_SUPPORT:
                self._remove_windows_task(job_id)
                self._add_windows_task(
                    job_id,
                    job_info["folder"],
                    job_info["schedule_type"],
                    job_info["time_value"]
                )
            
            # Update internal scheduler
            schedule.clear(job_id)
            self._add_internal_schedule(job_info)
            
            self._save_jobs()
            return True
        return False
    
    def _add_internal_schedule(self, job_info):
        """Add job to internal scheduler"""
        # Import here to avoid circular imports
        from .organizer import SmartOrganizer
        
        def job_function():
            try:
                organizer = SmartOrganizer()
                logger.info(f"Running scheduled job {job_info['id']}")
                stats = organizer.organize_folder(job_info['folder'])
                job_info['last_run'] = datetime.now().isoformat()
                job_info['status'] = 'completed'
                self._save_jobs()
                logger.info(f"Completed job {job_info['id']}: {stats}")
            except Exception as e:
                logger.error(f"Error in job {job_info['id']}: {e}")
                job_info['status'] = 'error'
                self._save_jobs()
        
        # Schedule based on type
        if job_info['schedule_type'] == 'daily':
            schedule.every().day.at(job_info['time_value']).do(job_function).tag(job_info['id'])
        elif job_info['schedule_type'] == 'weekly':
            day, time = job_info['time_value'].split(' ')
            getattr(schedule.every(), day.lower()).at(time).do(job_function).tag(job_info['id'])
        elif job_info['schedule_type'] == 'hourly':
            schedule.every().hour.do(job_function).tag(job_info['id'])
        elif job_info['schedule_type'] == 'minutes':
            schedule.every(int(job_info['time_value'])).minutes.do(job_function).tag(job_info['id'])
    
    def _add_windows_task(self, job_id, folder_path, schedule_type, time_value):
        """Add task to Windows Task Scheduler"""
        if not WINDOWS_SUPPORT:
            return
            
        try:
            scheduler = win32com.client.Dispatch('Schedule.Service')
            scheduler.Connect()
            
            root_folder = scheduler.GetFolder('\\')
            task_def = scheduler.NewTask(0)
            
            # Create trigger
            trigger = task_def.Triggers.Create(1)  # Daily trigger
            trigger.Enabled = True
            
            if schedule_type == 'daily':
                trigger.DaysInterval = 1
                trigger.StartBoundary = f"{datetime.now().date()}T{time_value}:00"
            elif schedule_type == 'weekly':
                day, time = time_value.split(' ')
                trigger.DaysOfWeek = self._get_weekday_mask(day)
                trigger.StartBoundary = f"{datetime.now().date()}T{time}:00"
            
            # Create action
            action = task_def.Actions.Create(0)
            action.Path = 'python'
            action.Arguments = f'-m src.core.runner --job-id {job_id}'
            action.WorkingDirectory = os.getcwd()
            
            # Set principal
            principal = task_def.Principal
            principal.LogonType = 3  # Interactive token
            
            # Register task
            root_folder.RegisterTaskDefinition(
                f'FileOrganizer_{job_id}',
                task_def,
                6,  # TASK_CREATE_OR_UPDATE
                None,
                None,
                3  # TASK_LOGON_INTERACTIVE_TOKEN
            )
            
            logger.info(f"Added Windows scheduled task for job {job_id}")
        except Exception as e:
            logger.warning(f"Could not add Windows task: {e}")
    
    def _remove_windows_task(self, job_id):
        """Remove task from Windows Task Scheduler"""
        if not WINDOWS_SUPPORT:
            return
            
        try:
            scheduler = win32com.client.Dispatch('Schedule.Service')
            scheduler.Connect()
            root_folder = scheduler.GetFolder('\\')
            root_folder.DeleteTask(f'FileOrganizer_{job_id}', 0)
            logger.info(f"Removed Windows scheduled task for job {job_id}")
        except Exception as e:
            logger.warning(f"Could not remove Windows task: {e}")
    
    def _get_weekday_mask(self, day):
        """Convert day name to Windows Task Scheduler mask"""
        days = {
            'monday': 2,
            'tuesday': 4,
            'wednesday': 8,
            'thursday': 16,
            'friday': 32,
            'saturday': 64,
            'sunday': 1
        }
        return days.get(day.lower(), 2)
    
    def start(self):
        """Start the scheduler"""
        if not self.running:
            self.running = True
            self.scheduler_thread = threading.Thread(target=self._run_scheduler)
            self.scheduler_thread.daemon = True
            self.scheduler_thread.start()
            logger.info("Scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        logger.info("Scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler in a separate thread"""
        while self.running:
            schedule.run_pending()
            time.sleep(1)