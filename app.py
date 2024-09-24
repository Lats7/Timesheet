import os
import sys
import json
import time
import csv
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import simpledialog, filedialog
from pathlib import Path

# Adjust data file path to be in the user's home directory
DATA_FILE = os.path.join(Path.home(), 'timesheet.json')

def load_data():
    data_defaults = {
        "projects": {}  # {project_name: project_data}
    }
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                messagebox.showerror("Data Error", "Failed to read data file. It may be corrupted.")
                data = data_defaults
            # Ensure all necessary keys are present
            for key, default_value in data_defaults.items():
                if key not in data:
                    data[key] = default_value
    else:
        data = data_defaults
    return data

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def start_project(project_name):
    data = load_data()
    if project_name in data['projects']:
        messagebox.showinfo("Project Exists", f"Project '{project_name}' already exists.")
        return
    project = {
        'status': 'Stopped',
        'sessions': [],
        'total_time': 0
    }

    # Start a new session
    project['status'] = 'Running'
    project['sessions'].append({
        'start_time': time.time(),
        'end_time': None,
        'lap_time': 0,
        'pauses': [],
        'total_paused_time': 0
    })

    data['projects'][project_name] = project
    save_data(data)
    messagebox.showinfo("Project Started", f"Started working on project '{project_name}'")
    app.update_tree()

def stop_project(project_name):
    data = load_data()
    project = data['projects'].get(project_name)

    if not project:
        messagebox.showinfo("Project Not Found", f"Project '{project_name}' does not exist.")
        return

    if project['status'] not in ['Running', 'Paused']:
        messagebox.showinfo("Project Not Active", f"Project '{project_name}' is not currently running or paused.")
        return

    # Stop the current session
    current_session = project['sessions'][-1]

    if project['status'] == 'Paused':
        # End the current pause
        pause = current_session['pauses'][-1]
        pause_end_time = time.time()
        pause['pause_end'] = pause_end_time
        paused_duration = pause_end_time - pause['pause_start']
        current_session['total_paused_time'] += paused_duration

    current_session['end_time'] = time.time()
    elapsed_time = (current_session['end_time'] - current_session['start_time']) - current_session.get('total_paused_time', 0)
    current_session['lap_time'] = elapsed_time

    project['total_time'] += elapsed_time
    project['status'] = 'Stopped'

    data['projects'][project_name] = project
    save_data(data)
    messagebox.showinfo(
        "Project Stopped",
        f"Stopped working on project '{project_name}'\nTime spent this session: {format_time(elapsed_time)}"
    )
    app.update_tree()

def pause_project(project_name):
    data = load_data()
    project = data['projects'].get(project_name)
    
    if not project or project['status'] != 'Running':
        messagebox.showinfo("Cannot Pause", f"Project '{project_name}' is not running.")
        return

    # Get the current session
    current_session = project['sessions'][-1]
    # Start a new pause
    pause_start_time = time.time()
    current_session['pauses'].append({'pause_start': pause_start_time, 'pause_end': None})
    # Update status
    project['status'] = 'Paused'

    data['projects'][project_name] = project
    save_data(data)
    messagebox.showinfo("Project Paused", f"Paused project '{project_name}'")
    app.update_tree()

def resume_paused_project(project_name):
    data = load_data()
    project = data['projects'].get(project_name)
    
    if not project or project['status'] != 'Paused':
        messagebox.showinfo("Cannot Resume", f"Project '{project_name}' is not paused.")
        return

    # Get the current session
    current_session = project['sessions'][-1]
    # End the current pause
    pause = current_session['pauses'][-1]
    pause_end_time = time.time()
    pause['pause_end'] = pause_end_time
    # Calculate paused duration
    paused_duration = pause_end_time - pause['pause_start']
    current_session['total_paused_time'] += paused_duration
    # Update status
    project['status'] = 'Running'

    data['projects'][project_name] = project
    save_data(data)
    messagebox.showinfo("Project Resumed", f"Resumed project '{project_name}' from pause")
    app.update_tree()

def resume_project(project_name):
    data = load_data()
    project = data['projects'].get(project_name)

    if not project:
        messagebox.showinfo("Project Not Found", f"Project '{project_name}' does not exist.")
        return

    if project['status'] != 'Stopped':
        messagebox.showinfo("Cannot Resume Project", f"Project '{project_name}' is not stopped.")
        return

    # Start a new session
    project['status'] = 'Running'
    project['sessions'].append({
        'start_time': time.time(),
        'end_time': None,
        'lap_time': 0,
        'pauses': [],
        'total_paused_time': 0
    })

    data['projects'][project_name] = project
    save_data(data)
    messagebox.showinfo("Project Resumed", f"Resumed working on project '{project_name}'")
    app.update_tree()

def delete_project(project_name):
    data = load_data()
    if project_name in data['projects']:
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete project '{project_name}'?")
        if confirm:
            del data['projects'][project_name]
            save_data(data)
            messagebox.showinfo("Project Deleted", f"Project '{project_name}' has been deleted.")
            app.update_tree()
    else:
        messagebox.showinfo("Project Not Found", f"Project '{project_name}' does not exist.")

def edit_project_name(old_project_name, new_project_name):
    data = load_data()
    if old_project_name not in data['projects']:
        messagebox.showinfo("Project Not Found", f"Project '{old_project_name}' does not exist.")
        return
    if new_project_name in data['projects']:
        messagebox.showinfo("Name Conflict", f"A project named '{new_project_name}' already exists.")
        return
    # Rename the project
    data['projects'][new_project_name] = data['projects'].pop(old_project_name)
    save_data(data)
    messagebox.showinfo("Project Renamed", f"Project '{old_project_name}' has been renamed to '{new_project_name}'.")
    app.update_tree()

def status():
    data = load_data()
    running_projects = [name for name, proj in data['projects'].items() if proj['status'] == 'Running']
    paused_projects = [name for name, proj in data['projects'].items() if proj['status'] == 'Paused']
    if not running_projects and not paused_projects:
        messagebox.showinfo("Status", "No projects are currently running or paused.")
    else:
        status_text = ""
        if running_projects:
            status_text += "Currently running projects:\n"
            for project_name in running_projects:
                project = data['projects'][project_name]
                current_session = project['sessions'][-1]
                elapsed_time = (time.time() - current_session['start_time']) - current_session.get('total_paused_time', 0)
                status_text += f" - {project_name}: {format_time(elapsed_time)}\n"
        if paused_projects:
            status_text += "\nCurrently paused projects:\n"
            for project_name in paused_projects:
                project = data['projects'][project_name]
                current_session = project['sessions'][-1]
                elapsed_time = (current_session['pauses'][-1]['pause_start'] - current_session['start_time']) - current_session.get('total_paused_time', 0)
                status_text += f" - {project_name}: {format_time(elapsed_time)} (Paused)\n"
        messagebox.showinfo("Status", status_text)

def report():
    data = load_data()
    if not data['projects']:
        messagebox.showinfo("Report", "No time recorded yet.")
        return

    report_text = "Total time spent on projects:\n"
    total_all_projects = 0
    for project_name, project in data['projects'].items():
        total_seconds = project['total_time']
        report_text += f" - {project_name}: {format_time(total_seconds)}\n"
        total_all_projects += total_seconds
    report_text += f"\nTotal time spent on all projects: {format_time(total_all_projects)}"

    # Show the report with an option to export detailed report to a CSV file
    response = messagebox.askyesno("Report", f"{report_text}\n\nDo you want to export detailed report to a CSV file?")
    if response:
        export_report_to_csv(data)

def export_report_to_csv(data):
    # Open file dialog to select where to save the CSV file
    file_path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV files', '*.csv')])
    if file_path:
        try:
            with open(file_path, 'w', newline='') as csvfile:
                fieldnames = ['Project Name', 'Session', 'Start Time', 'End Time', 'Lap Time (h:m:s)', 'Total Time (h:m:s)', 'Pauses']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for project_name, project in data['projects'].items():
                    total_time_formatted = format_time(project['total_time'])
                    for idx, session in enumerate(project['sessions'], start=1):
                        start_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(session['start_time']))
                        end_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(session['end_time'])) if session['end_time'] else 'Running'
                        lap_time_formatted = format_time(session['lap_time']) if session['lap_time'] else 'Running'
                        pauses_info = ''
                        for pause in session.get('pauses', []):
                            pause_start = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(pause['pause_start']))
                            pause_end = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(pause['pause_end'])) if pause.get('pause_end') else 'Ongoing'
                            pauses_info += f"Start: {pause_start}, End: {pause_end}; "
                        writer.writerow({
                            'Project Name': project_name,
                            'Session': idx,
                            'Start Time': start_time_str,
                            'End Time': end_time_str,
                            'Lap Time (h:m:s)': lap_time_formatted,
                            'Total Time (h:m:s)': total_time_formatted,
                            'Pauses': pauses_info
                        })
            messagebox.showinfo("Export Successful", f"Report exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"An error occurred while exporting the report:\n{e}")

def clear_all_data():
    confirm = messagebox.askyesno("Confirm Clear All", "Are you sure you want to clear all data? This action cannot be undone.")
    if confirm:
        # Reset the data
        data = {"projects": {}}
        save_data(data)
        messagebox.showinfo("Data Cleared", "All data has been cleared.")
        # Update the GUI
        app.update_tree()
    else:
        messagebox.showinfo("Cancelled", "Clear all data operation cancelled.")

def format_time(seconds):
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours}h {minutes}m {seconds}s"

# GUI Implementation
class TimeTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stefan's Timesheet Tracker")

        # Use ttk for modern widgets
        self.style = ttk.Style()
        self.current_theme = 'clam'  # Default light theme

        # Top Frame for Dark Mode Toggle and Title
        top_frame = ttk.Frame(root)
        top_frame.pack(fill='x')

        # Title Label
        title_label = ttk.Label(top_frame, text="Stefan's Timesheet Tracker", font=("Arial", 16))
        title_label.pack(side='left', padx=10, pady=5)

        # Dark Mode Toggle Button
        self.dark_mode_var = tk.BooleanVar(value=False)
        self.dark_mode_button = ttk.Checkbutton(
            top_frame, text="Dark Mode", variable=self.dark_mode_var, command=self.toggle_dark_mode
        )
        self.dark_mode_button.pack(side='right', padx=10, pady=5)

        # Main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill='both', expand=True)

        # Project List Label
        project_list_label = ttk.Label(main_frame, text="Projects:", font=("Arial", 14))
        project_list_label.pack(pady=(0, 5))

        # Project List Treeview
        columns = ('Project Name', 'Time Spent', 'Status')
        self.tree = ttk.Treeview(main_frame, columns=columns, show='headings', selectmode='browse')
        self.tree.heading('Project Name', text='Project Name')
        self.tree.heading('Time Spent', text='Total Time')
        self.tree.heading('Status', text='Status')
        self.tree.column('Project Name', width=200)
        self.tree.column('Time Spent', width=100)
        self.tree.column('Status', width=80)
        self.tree.pack(fill='both', expand=True)

        # Bind selection event to update buttons
        self.tree.bind('<<TreeviewSelect>>', lambda event: self.update_buttons())

        # Buttons Frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill='x', pady=(10, 0))

        # Create buttons
        self.start_button = ttk.Button(buttons_frame, text="Start Project", command=self.start_project)
        self.stop_button = ttk.Button(buttons_frame, text="Stop Project", command=self.stop_project)
        self.pause_button = ttk.Button(buttons_frame, text="Pause", command=self.pause_project)
        self.resume_pause_button = ttk.Button(buttons_frame, text="Resume from Pause", command=self.resume_paused_project)
        self.resume_button = ttk.Button(buttons_frame, text="Resume Project", command=self.resume_project)
        self.delete_button = ttk.Button(buttons_frame, text="Delete Project", command=self.delete_project)
        self.edit_button = ttk.Button(buttons_frame, text="Edit Project", command=self.edit_project)
        self.view_sessions_button = ttk.Button(buttons_frame, text="View Sessions", command=self.view_sessions)
        self.status_button = ttk.Button(buttons_frame, text="Status", command=status)
        self.report_button = ttk.Button(buttons_frame, text="Report", command=report)
        self.clear_button = ttk.Button(buttons_frame, text="Clear All", command=clear_all_data)
        self.exit_button = ttk.Button(buttons_frame, text="Exit", command=root.quit)

        # Place buttons
        self.start_button.pack(side='left', expand=True, fill='x', padx=2)
        self.stop_button.pack(side='left', expand=True, fill='x', padx=2)
        self.pause_button.pack(side='left', expand=True, fill='x', padx=2)
        self.resume_pause_button.pack(side='left', expand=True, fill='x', padx=2)
        self.resume_button.pack(side='left', expand=True, fill='x', padx=2)
        self.delete_button.pack(side='left', expand=True, fill='x', padx=2)
        self.edit_button.pack(side='left', expand=True, fill='x', padx=2)
        self.view_sessions_button.pack(side='left', expand=True, fill='x', padx=2)
        self.status_button.pack(side='left', expand=True, fill='x', padx=2)
        self.report_button.pack(side='left', expand=True, fill='x', padx=2)
        self.clear_button.pack(side='left', expand=True, fill='x', padx=2)
        self.exit_button.pack(side='left', expand=True, fill='x', padx=2)

        # Disable buttons that require selection
        self.stop_button.config(state='disabled')
        self.pause_button.config(state='disabled')
        self.resume_pause_button.config(state='disabled')
        self.resume_button.config(state='disabled')
        self.delete_button.config(state='disabled')
        self.edit_button.config(state='disabled')
        self.view_sessions_button.config(state='disabled')

        # Initialize timer update
        self.update_timer()

    def start_project(self):
        project_name = simpledialog.askstring("Start Project", "Enter new project name:")
        if project_name:
            start_project(project_name)

    def stop_project(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("No Selection", "Please select a project to stop.")
            return
        selected_item = selected_items[0]
        project_name = self.tree.item(selected_item)['values'][0]
        stop_project(project_name)

    def pause_project(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("No Selection", "Please select a project to pause.")
            return
        selected_item = selected_items[0]
        project_name = self.tree.item(selected_item)['values'][0]
        pause_project(project_name)

    def resume_paused_project(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("No Selection", "Please select a project to resume from pause.")
            return
        selected_item = selected_items[0]
        project_name = self.tree.item(selected_item)['values'][0]
        resume_paused_project(project_name)

    def resume_project(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("No Selection", "Please select a project to resume.")
            return
        selected_item = selected_items[0]
        project_name = self.tree.item(selected_item)['values'][0]
        resume_project(project_name)

    def delete_project(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("No Selection", "Please select a project to delete.")
            return
        selected_item = selected_items[0]
        project_name = self.tree.item(selected_item)['values'][0]
        delete_project(project_name)

    def edit_project(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("No Selection", "Please select a project to edit.")
            return
        selected_item = selected_items[0]
        old_project_name = self.tree.item(selected_item)['values'][0]
        new_project_name = simpledialog.askstring("Edit Project", f"Enter new name for project '{old_project_name}':")
        if new_project_name:
            edit_project_name(old_project_name, new_project_name)

    def view_sessions(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("No Selection", "Please select a project to view sessions.")
            return
        selected_item = selected_items[0]
        project_name = self.tree.item(selected_item)['values'][0]
        data = load_data()
        project = data['projects'].get(project_name)
        if not project:
            messagebox.showinfo("No Data", f"No data found for project '{project_name}'.")
            return

        # Create a new window to display sessions
        sessions_window = tk.Toplevel(self.root)
        sessions_window.title(f"Sessions for {project_name}")

        # Sessions Treeview
        columns = ('Session', 'Start Time', 'End Time', 'Lap Time', 'Paused Time')
        sessions_tree = ttk.Treeview(sessions_window, columns=columns, show='headings')
        sessions_tree.heading('Session', text='Session')
        sessions_tree.heading('Start Time', text='Start Time')
        sessions_tree.heading('End Time', text='End Time')
        sessions_tree.heading('Lap Time', text='Lap Time')
        sessions_tree.heading('Paused Time', text='Paused Time')
        sessions_tree.column('Session', width=80)
        sessions_tree.column('Start Time', width=150)
        sessions_tree.column('End Time', width=150)
        sessions_tree.column('Lap Time', width=100)
        sessions_tree.column('Paused Time', width=100)
        sessions_tree.pack(fill='both', expand=True)

        # Insert session data
        for idx, session in enumerate(project['sessions'], start=1):
            start_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(session['start_time']))
            end_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(session['end_time'])) if session['end_time'] else 'Running'
            lap_time_formatted = format_time(session['lap_time']) if session['lap_time'] else 'Running'
            paused_time_formatted = format_time(session.get('total_paused_time', 0))
            sessions_tree.insert('', 'end', values=(f"Session {idx}", start_time_str, end_time_str, lap_time_formatted, paused_time_formatted))

    def update_timer(self):
        self.update_tree()
        self.root.after(1000, self.update_timer)

    def update_tree(self):
        data = load_data()

        # Save the currently selected project names
        selected_items = self.tree.selection()
        selected_projects = []
        for item_id in selected_items:
            project_name = self.tree.item(item_id)['values'][0]
            selected_projects.append(project_name)

        # Get all existing items
        existing_items = {self.tree.item(item)['values'][0]: item for item in self.tree.get_children()}

        # Update existing items and add new ones
        for project_name, project in data['projects'].items():
            total_time = project['total_time']
            if project['status'] in ['Running', 'Paused']:
                # Add elapsed time from current session, subtracting paused time
                current_session = project['sessions'][-1]
                if project['status'] == 'Paused':
                    elapsed_time = (current_session['pauses'][-1]['pause_start'] - current_session['start_time']) - current_session.get('total_paused_time', 0)
                else:
                    elapsed_time = (time.time() - current_session['start_time']) - current_session.get('total_paused_time', 0)
                display_time = format_time(total_time + elapsed_time)
            else:
                display_time = format_time(total_time)

            if project_name in existing_items:
                # Update existing item
                item_id = existing_items[project_name]
                self.tree.item(item_id, values=(project_name, display_time, project['status']))
            else:
                # Insert new item
                item_id = self.tree.insert('', 'end', values=(project_name, display_time, project['status']))
                existing_items[project_name] = item_id  # Update existing_items

        # Remove items that are no longer in data
        for project_name in list(existing_items.keys()):
            if project_name not in data['projects']:
                self.tree.delete(existing_items[project_name])
                del existing_items[project_name]

        # Restore the selection
        new_selected_items = []
        for project_name in selected_projects:
            item_id = existing_items.get(project_name)
            if item_id:
                new_selected_items.append(item_id)
        self.tree.selection_set(new_selected_items)

        # Update button states
        self.update_buttons()

    def update_buttons(self):
        selected_items = self.tree.selection()
        if not selected_items:
            # Disable buttons that require selection
            self.stop_button.config(state='disabled')
            self.pause_button.config(state='disabled')
            self.resume_pause_button.config(state='disabled')
            self.resume_button.config(state='disabled')
            self.delete_button.config(state='disabled')
            self.edit_button.config(state='disabled')
            self.view_sessions_button.config(state='disabled')
        else:
            selected_item = selected_items[0]
            project_name = self.tree.item(selected_item)['values'][0]
            data = load_data()
            project = data['projects'].get(project_name)
            status = project['status']
            self.delete_button.config(state='normal')
            self.edit_button.config(state='normal')
            self.view_sessions_button.config(state='normal')
            if status == 'Running':
                self.stop_button.config(state='normal')
                self.pause_button.config(state='normal')
                self.resume_pause_button.config(state='disabled')
                self.resume_button.config(state='disabled')
            elif status == 'Paused':
                self.stop_button.config(state='normal')
                self.pause_button.config(state='disabled')
                self.resume_pause_button.config(state='normal')
                self.resume_button.config(state='disabled')
            elif status == 'Stopped':
                self.stop_button.config(state='disabled')
                self.pause_button.config(state='disabled')
                self.resume_pause_button.config(state='disabled')
                self.resume_button.config(state='normal')
            else:
                # Default to disabling action buttons
                self.stop_button.config(state='disabled')
                self.pause_button.config(state='disabled')
                self.resume_pause_button.config(state='disabled')
                self.resume_button.config(state='disabled')

    def toggle_dark_mode(self):
        if self.dark_mode_var.get():
            # Switch to dark mode
            self.set_dark_mode()
        else:
            # Switch to light mode
            self.set_light_mode()

    def set_dark_mode(self):
        # Configure dark theme
        self.style.theme_use('alt')
        self.style.configure('.', background='#2e2e2e', foreground='white')
        self.style.configure('Treeview', background='#2e2e2e', foreground='white', fieldbackground='#2e2e2e')
        self.style.map('Treeview', background=[('selected', '#4d4d4d')], foreground=[('selected', 'white')])
        self.style.configure('TButton', background='#4d4d4d', foreground='white')
        self.style.configure('TLabel', background='#2e2e2e', foreground='white')
        self.style.configure('TFrame', background='#2e2e2e')
        self.style.configure('TCheckbutton', background='#2e2e2e', foreground='white')
        self.style.map('TCheckbutton',
            background=[('active', '#4d4d4d'), ('!active', '#2e2e2e')],
            foreground=[('active', 'white'), ('!active', 'white')])

        # Update all widgets
        self.update_widget_colors('#2e2e2e', 'white')

    def set_light_mode(self):
        # Configure light theme
        self.style.theme_use('clam')
        self.style.configure('.', background='SystemButtonFace', foreground='black')
        self.style.configure('Treeview', background='white', foreground='black', fieldbackground='white')
        self.style.map('Treeview', background=[('selected', 'SystemHighlight')], foreground=[('selected', 'white')])
        self.style.configure('TButton', background='SystemButtonFace', foreground='black')
        self.style.configure('TLabel', background='SystemButtonFace', foreground='black')
        self.style.configure('TFrame', background='SystemButtonFace')
        self.style.configure('TCheckbutton', background='SystemButtonFace', foreground='black')
        self.style.map('TCheckbutton',
            background=[('active', 'SystemButtonFace'), ('!active', 'SystemButtonFace')],
            foreground=[('active', 'black'), ('!active', 'black')])

        # Update all widgets
        self.update_widget_colors('SystemButtonFace', 'black')

    def update_widget_colors(self, bg_color, fg_color):
        widgets = [self.root] + list(self.root.children.values())
        for widget in widgets:
            try:
                widget.configure(background=bg_color, foreground=fg_color)
            except tk.TclError:
                pass  # Some widgets may not support these options
            for child in widget.winfo_children():
                try:
                    child.configure(background=bg_color, foreground=fg_color)
                except tk.TclError:
                    pass

def main():
    global app
    root = tk.Tk()
    app = TimeTrackerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
