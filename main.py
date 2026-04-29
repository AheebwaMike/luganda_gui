import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from deep_translator import GoogleTranslator
import time
import threading
import os
from datetime import datetime
import socket

class LugandaTranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Luganda Batch Translator App")
        self.root.geometry("800x750")  # Increased height for footer
        self.root.minsize(700, 650)
        self.root.configure(bg='#f5f5f5')
        
        # Allow window to be resizable
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Set icon if exists
        try:
            self.root.iconbitmap("app_icon.ico")
        except:
            pass
        
        # Variables
        self.input_file_path = None
        self.translation_thread = None
        self.is_translating = False
        self.start_time = None
        self.elapsed_time = 0  # Track elapsed time for counter
        self.error_occurred = False  # Track if error has occurred
        
        # Initialize translator
        self.translator = GoogleTranslator(source='auto', target='lg')
        
        self.create_widgets()
        
        # Start the time counter update
        self.update_time_counter()
        
    def create_widgets(self):
        # Create main canvas with scrollbar for the entire window
        main_canvas = tk.Canvas(self.root, bg='#f5f5f5', highlightthickness=0)
        main_scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        self.scrollable_frame = tk.Frame(main_canvas, bg='#f5f5f5')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=main_canvas.winfo_width())
        main_canvas.configure(yscrollcommand=main_scrollbar.set)
        
        # Bind canvas resize
        def _on_canvas_resize(event):
            main_canvas.itemconfig(1, width=event.width)
        main_canvas.bind('<Configure>', _on_canvas_resize)
        
        # Pack scrollbar and canvas
        main_scrollbar.pack(side="right", fill="y")
        main_canvas.pack(side="left", fill="both", expand=True)
        
        # Main container with padding
        main_frame = tk.Frame(self.scrollable_frame, bg='#f5f5f5')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header Section
        header_frame = tk.Frame(main_frame, bg='#2c3e50', height=100)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="📝 Luganda Batch Translator", 
                               font=('Arial', 20, 'bold'), bg='#2c3e50', fg='white')
        title_label.pack(expand=True)
        
        subtitle_label = tk.Label(header_frame, text="Translate text files to Luganda with resume support", 
                                 font=('Arial', 11), bg='#2c3e50', fg='#ecf0f1')
        subtitle_label.pack()
        
        # File Selection Section
        file_section = tk.LabelFrame(main_frame, text="📁 File Selection", 
                                     font=('Arial', 12, 'bold'), bg='#f5f5f5', fg='#2c3e50',
                                     padx=15, pady=15)
        file_section.pack(fill=tk.X, pady=(0, 15))
        
        # Browse button and file info
        btn_frame = tk.Frame(file_section, bg='#f5f5f5')
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.btn_browse = tk.Button(btn_frame, text="📂 SELECT TEXT FILE", 
                                   command=self.select_file,
                                   bg='#3498db', fg='white', font=('Arial', 11, 'bold'),
                                   cursor='hand2', padx=30, pady=10)
        self.btn_browse.pack(side=tk.LEFT, padx=(0, 15))
        
        self.file_label = tk.Label(btn_frame, text="No file selected", 
                                  bg='#f5f5f5', fg='#7f8c8d', font=('Arial', 10))
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # File info frame
        self.file_info_frame = tk.Frame(file_section, bg='#f5f5f5')
        self.file_info_frame.pack(fill=tk.X)
        
        self.file_size_label = tk.Label(self.file_info_frame, text="", 
                                       bg='#f5f5f5', fg='#7f8c8d', font=('Arial', 10))
        self.file_size_label.pack(anchor='w', pady=2)
        
        self.file_lines_label = tk.Label(self.file_info_frame, text="", 
                                        bg='#f5f5f5', fg='#7f8c8d', font=('Arial', 10))
        self.file_lines_label.pack(anchor='w', pady=2)
        
        # Progress Section
        progress_section = tk.LabelFrame(main_frame, text="📊 Translation Progress", 
                                        font=('Arial', 12, 'bold'), bg='#f5f5f5', fg='#2c3e50',
                                        padx=15, pady=15)
        progress_section.pack(fill=tk.X, pady=(0, 15))
        
        # Progress bar
        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(progress_section, length=400, mode='determinate',
                                           variable=self.progress_var)
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Progress labels
        progress_info_frame = tk.Frame(progress_section, bg='#f5f5f5')
        progress_info_frame.pack(fill=tk.X)
        
        self.progress_percent_label = tk.Label(progress_info_frame, text="0%", 
                                              bg='#f5f5f5', fg='#2c3e50', font=('Arial', 11, 'bold'))
        self.progress_percent_label.pack(side=tk.LEFT)
        
        # Changed to show batch progress instead of line progress
        self.progress_count_label = tk.Label(progress_info_frame, text="0/0 batches", 
                                            bg='#f5f5f5', fg='#7f8c8d', font=('Arial', 10))
        self.progress_count_label.pack(side=tk.RIGHT)
        
        # Statistics Section
        stats_section = tk.LabelFrame(main_frame, text="📈 Statistics", 
                                     font=('Arial', 12, 'bold'), bg='#f5f5f5', fg='#2c3e50',
                                     padx=15, pady=10)
        stats_section.pack(fill=tk.X, pady=(0, 15))
        
        stats_grid = tk.Frame(stats_section, bg='#f5f5f5')
        stats_grid.pack(fill=tk.X)
        
        # Stats labels
        self.stats_labels = {}
        stats_info = [
            ("Total Lines:", "0"),
            ("Total Batches:", "0"),
            ("Translated Lines:", "0"),
            ("Completed Batches:", "0"),
            ("Remaining Lines:", "0"),
            ("Remaining Batches:", "0"),
            ("Time Elapsed:", "00:00:00"),
            ("Estimated Remaining:", "Calculating...")
        ]
        
        for i, (label, value) in enumerate(stats_info):
            row = i // 2
            col = (i % 2) * 2
            frame = tk.Frame(stats_grid, bg='#f5f5f5')
            frame.grid(row=row, column=col, sticky='w', padx=(0, 30), pady=5)
            
            tk.Label(frame, text=label, bg='#f5f5f5', fg='#7f8c8d', font=('Arial', 10)).pack(side=tk.LEFT)
            self.stats_labels[label] = tk.Label(frame, text=value, bg='#f5f5f5', fg='#2c3e50', 
                                               font=('Arial', 10, 'bold'))
            self.stats_labels[label].pack(side=tk.LEFT, padx=(5, 0))
        
        # Status Section
        status_section = tk.LabelFrame(main_frame, text="ℹ️ Status Information", 
                                      font=('Arial', 12, 'bold'), bg='#f5f5f5', fg='#2c3e50',
                                      padx=15, pady=10)
        status_section.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Status text with scrollbar
        status_text_frame = tk.Frame(status_section, bg='#f5f5f5')
        status_text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_text = tk.Text(status_text_frame, height=6, wrap=tk.WORD,
                                  font=('Consolas', 9), bg='#fef9e7', fg='#2c3e50')
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        status_scrollbar = tk.Scrollbar(status_text_frame, command=self.status_text.yview)
        status_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.config(yscrollcommand=status_scrollbar.set)
        
        # Current operation status
        self.current_status_label = tk.Label(status_section, text="✅ Ready - Please select a file", 
                                            bg='#f5f5f5', fg='#27ae60', font=('Arial', 10, 'bold'))
        self.current_status_label.pack(anchor='w', pady=(5, 0))
        
        # ACTION BUTTONS SECTION
        button_container = tk.Frame(main_frame, bg='#f5f5f5')
        button_container.pack(fill=tk.X, pady=(20, 10))
        
        # Separator line
        separator = tk.Frame(button_container, height=2, bg='#bdc3c7')
        separator.pack(fill=tk.X, pady=(0, 15))
        
        # Buttons frame with grid layout for better control
        button_frame = tk.Frame(button_container, bg='#f5f5f5')
        button_frame.pack(fill=tk.X)
        
        # Start button
        self.btn_start = tk.Button(button_frame, text="▶ START TRANSLATION", 
                                  command=self.start_translation,
                                  bg='#27ae60', fg='white', font=('Arial', 12, 'bold'),
                                  cursor='hand2', padx=30, pady=12,
                                  state=tk.DISABLED, relief=tk.RAISED, bd=2)
        self.btn_start.pack(side=tk.LEFT, padx=(0, 10), expand=True, fill=tk.X)
        
        # Pause button
        self.btn_stop = tk.Button(button_frame, text="⏸ PAUSE", 
                                 command=self.stop_translation,
                                 bg='#e67e22', fg='white', font=('Arial', 12, 'bold'),
                                 cursor='hand2', padx=30, pady=12, 
                                 state=tk.DISABLED, relief=tk.RAISED, bd=2)
        self.btn_stop.pack(side=tk.LEFT, padx=(0, 10), expand=True, fill=tk.X)
        
        # Reset button
        self.btn_reset = tk.Button(button_frame, text="🔄 RESET PROGRESS", 
                                  command=self.reset_progress,
                                  bg='#95a5a6', fg='white', font=('Arial', 12, 'bold'),
                                  cursor='hand2', padx=30, pady=12,
                                  state=tk.DISABLED, relief=tk.RAISED, bd=2)
        self.btn_reset.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        # Debug label
        self.debug_label = tk.Label(button_container, text="Buttons disabled until file selected", 
                                   bg='#f5f5f5', fg='#7f8c8d', font=('Arial', 8))
        self.debug_label.pack(pady=(10, 0))
        
        # ============ COPYRIGHT / FOOTER SECTION ============
        footer_frame = tk.Frame(main_frame, bg='#f5f5f5')
        footer_frame.pack(fill=tk.X, pady=(20, 5))
        
        # Subtle separator line above footer
        footer_separator = tk.Frame(footer_frame, height=1, bg='#d5d8dc')
        footer_separator.pack(fill=tk.X, pady=(0, 10))
        
        # Footer content frame
        footer_content = tk.Frame(footer_frame, bg='#f5f5f5')
        footer_content.pack()
        
        # Copyright text with appropriate wording
        copyright_text = "© 2026 Luganda Project"
        copyright_label = tk.Label(footer_content, text=copyright_text, 
                                   font=('Arial', 12, 'italic'), 
                                   bg='#f5f5f5', fg='#95a5a6')
        copyright_label.pack()
        
        # Version info
        version_text = "Developed by Michael | michaelaheebwa357@gmail.com | +256 745 401097"
        version_label = tk.Label(footer_content, text=version_text,
                                font=('Arial', 10), 
                                bg='#f5f5f5', fg='#bdc3c7')
        version_label.pack(pady=(2, 0))
        
        # Optional: Add a tooltip or hover effect (simple)
        def on_enter(event):
            copyright_label.config(fg='#7f8c8d')
        def on_leave(event):
            copyright_label.config(fg='#95a5a6')
        
        copyright_label.bind("<Enter>", on_enter)
        copyright_label.bind("<Leave>", on_leave)
        
        # Configure grid weights for stats
        stats_grid.columnconfigure(0, weight=1)
        stats_grid.columnconfigure(2, weight=1)
        
        # Add initial status message
        self.add_status_message("✅ Application started. Please click 'SELECT TEXT FILE' to begin.")
    
    def check_internet_connection(self):
        """Check if internet connection is available"""
        try:
            # Try to connect to Google's DNS server
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False
    
    def show_error_popup(self, error_message, error_type="Connection Error"):
        """Show a popup window for errors with detailed information"""
        # Create a custom popup window
        popup = tk.Toplevel(self.root)
        popup.title(f"⚠️ {error_type}")
        popup.geometry("550x300")
        popup.configure(bg='#f5f5f5')
        popup.resizable(False, False)
        
        # Center the popup on the main window
        popup.transient(self.root)
        popup.grab_set()
        
        # Make it modal
        popup.focus_force()
        
        # Icon and title frame
        icon_frame = tk.Frame(popup, bg='#f5f5f5')
        icon_frame.pack(pady=(20, 10))
        
        # Error icon
        error_icon = tk.Label(icon_frame, text="⚠️", font=('Arial', 48), bg='#f5f5f5', fg='#e74c3c')
        error_icon.pack()
        
        # Error title
        title_label = tk.Label(icon_frame, text=error_type, 
                              font=('Arial', 14, 'bold'), 
                              bg='#f5f5f5', fg='#e74c3c')
        title_label.pack(pady=(5, 0))
        
        # Error message
        message_frame = tk.Frame(popup, bg='#f5f5f5')
        message_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        message_label = tk.Label(message_frame, text=error_message, 
                                font=('Arial', 10), 
                                bg='#f5f5f5', fg='#2c3e50',
                                wraplength=450, justify=tk.CENTER)
        message_label.pack(pady=10)
        
        # Additional info
        info_label = tk.Label(message_frame, 
                            text="✓ Your progress has been saved\n✓ Check your internet connection\n✓ Click 'START TRANSLATION' to resume", 
                            font=('Arial', 9, 'italic'), 
                            bg='#f5f5f5', fg='#7f8c8d',
                            justify=tk.LEFT)
        info_label.pack(pady=10)
        
        # Button frame
        button_frame = tk.Frame(popup, bg='#f5f5f5')
        button_frame.pack(pady=(0, 20))
        
        def on_ok():
            popup.destroy()
            # Flash the start button to draw attention
            self.flash_button(self.btn_start)
        
        ok_button = tk.Button(button_frame, text="OK - Resume Translation", 
                             command=on_ok,
                             bg='#3498db', fg='white', 
                             font=('Arial', 10, 'bold'),
                             cursor='hand2', padx=20, pady=8)
        ok_button.pack()
        
        # Play a simple system beep to alert user (optional)
        try:
            self.root.bell()
        except:
            pass
        
        # Bring popup to front
        popup.lift()
        popup.attributes('-topmost', True)
        popup.after(100, lambda: popup.attributes('-topmost', False))
    
    def update_time_counter(self):
        """Update the time elapsed counter in real-time"""
        if self.is_translating and self.start_time:
            # Calculate elapsed time
            self.elapsed_time = time.time() - self.start_time
            
            # Format the time
            hours = int(self.elapsed_time // 3600)
            minutes = int((self.elapsed_time % 3600) // 60)
            seconds = int(self.elapsed_time % 60)
            time_string = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            # Update the stats label
            self.stats_labels["Time Elapsed:"].config(text=time_string)
        
        # Schedule the next update (every second)
        self.root.after(1000, self.update_time_counter)
    
    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Text File to Translate",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            self.input_file_path = file_path
            filename = os.path.basename(file_path)
            self.file_label.config(text=filename, fg='#2c3e50', font=('Arial', 10, 'bold'))
            
            # Get file info
            try:
                file_size = os.path.getsize(file_path)
                if file_size < 1024:
                    size_str = f"{file_size} bytes"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size / 1024:.2f} KB"
                else:
                    size_str = f"{file_size / (1024 * 1024):.2f} MB"
                
                self.file_size_label.config(text=f"📄 File Size: {size_str}")
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = [line.strip() for line in f if line.strip()]
                    line_count = len(lines)
                self.file_lines_label.config(text=f"📊 Total Lines: {line_count}")
                
                # Calculate batch info
                BATCH_SIZE = 30
                total_batches = (line_count + BATCH_SIZE - 1) // BATCH_SIZE
                
                self.stats_labels["Total Lines:"].config(text=str(line_count))
                self.stats_labels["Total Batches:"].config(text=str(total_batches))
                self.stats_labels["Remaining Lines:"].config(text=str(line_count))
                self.stats_labels["Remaining Batches:"].config(text=str(total_batches))
                
                self.add_status_message(f"✓ File selected: {filename} ({line_count} lines, {total_batches} batches, {size_str})")
                
                # ENABLE THE BUTTONS NOW!
                self.btn_start.config(state=tk.NORMAL)
                self.btn_reset.config(state=tk.NORMAL)
                self.debug_label.config(text="✓ Buttons enabled! Click START TRANSLATION", fg='#27ae60')
                self.current_status_label.config(text="✅ File loaded - Ready to translate", fg='#27ae60')
                
                # Flash the start button to draw attention
                self.flash_button(self.btn_start)
                
                # Also scroll to show the buttons
                self.scroll_to_bottom()
                
                # Check for existing translation
                self.check_existing_translation()
                
            except Exception as e:
                self.add_status_message(f"❌ Error reading file: {str(e)}", error=True)
    
    def scroll_to_bottom(self):
        """Scroll the canvas to show the buttons"""
        # Update the canvas to ensure we can scroll to the bottom
        self.root.update_idletasks()
        # Find the main canvas (first canvas in the root)
        for child in self.root.winfo_children():
            if isinstance(child, tk.Canvas):
                child.yview_moveto(1.0)  # Scroll to bottom
                break
    
    def flash_button(self, button, count=3):
        """Flash a button to draw user attention"""
        def flash():
            original_bg = button.cget('bg')
            original_text = button.cget('text')
            for i in range(count):
                button.config(bg='#f1c40f', text='👉 CLICK HERE 👈')
                button.update()
                time.sleep(0.15)
                button.config(bg=original_bg, text=original_text)
                button.update()
                time.sleep(0.15)
        threading.Thread(target=flash, daemon=True).start()
    
    def check_existing_translation(self):
        """Check if there's an existing translation and show resume info"""
        if not self.input_file_path:
            return
            
        dir_name = os.path.dirname(self.input_file_path)
        base_name = os.path.basename(self.input_file_path)
        output_dir = os.path.join(dir_name, "translated")
        output_path = os.path.join(output_dir, f"translated_{base_name}")
        
        if os.path.exists(output_path):
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    translated_lines = sum(1 for line in f)
                
                with open(self.input_file_path, 'r', encoding='utf-8') as f:
                    total_lines = sum(1 for line in f if line.strip())
                
                BATCH_SIZE = 30
                total_batches = (total_lines + BATCH_SIZE - 1) // BATCH_SIZE
                completed_batches = (translated_lines + BATCH_SIZE - 1) // BATCH_SIZE
                
                if translated_lines > 0 and translated_lines < total_lines:
                    self.add_status_message(f"⚠️ Found existing translation ({translated_lines}/{total_lines} lines, {completed_batches}/{total_batches} batches completed). Will resume from where it stopped.")
                    
                    self.stats_labels["Translated Lines:"].config(text=str(translated_lines))
                    self.stats_labels["Completed Batches:"].config(text=str(completed_batches))
                    self.stats_labels["Remaining Lines:"].config(text=str(total_lines - translated_lines))
                    self.stats_labels["Remaining Batches:"].config(text=str(total_batches - completed_batches))
                    
                    # Update progress based on batches
                    batch_progress = int((completed_batches / total_batches) * 100)
                    self.progress_var.set(batch_progress)
                    self.progress_percent_label.config(text=f"{batch_progress}%")
                    self.progress_count_label.config(text=f"{completed_batches}/{total_batches} batches")
                    
                    self.current_status_label.config(text="ℹ️ Existing translation found - Click START to resume", fg='#3498db')
                    self.btn_start.config(state=tk.NORMAL)
                    self.debug_label.config(text="✓ Existing translation found - Click START to resume", fg='#3498db')
                elif translated_lines >= total_lines:
                    self.add_status_message("✅ File already fully translated!")
                    self.current_status_label.config(text="✅ Already translated - No action needed", fg='#27ae60')
                    self.btn_start.config(state=tk.DISABLED)
                    self.debug_label.config(text="File already translated", fg='#95a5a6')
            except Exception as e:
                self.add_status_message(f"⚠️ Error checking existing translation: {str(e)}", error=True)
    
    def add_status_message(self, message, error=False):
        """Add a timestamped message to the status text area"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        
        # Color code based on message type
        if "❌" in message or error:
            self.status_text.tag_add("error", f"end-2l", "end-1l")
            self.status_text.tag_config("error", foreground="#e74c3c")
        elif "⚠️" in message:
            self.status_text.tag_add("warning", f"end-2l", "end-1l")
            self.status_text.tag_config("warning", foreground="#f39c12")
        else:
            self.status_text.tag_add("info", f"end-2l", "end-1l")
            self.status_text.tag_config("info", foreground="#2c3e50")
    
    def update_stats(self, current_lines, total_lines, current_batches, total_batches, elapsed_time):
        """Update statistics display"""
        self.stats_labels["Translated Lines:"].config(text=str(current_lines))
        self.stats_labels["Completed Batches:"].config(text=str(current_batches))
        self.stats_labels["Remaining Lines:"].config(text=str(total_lines - current_lines))
        self.stats_labels["Remaining Batches:"].config(text=str(total_batches - current_batches))
        
        # Calculate estimated remaining time based on batches
        if current_batches > 0:
            time_per_batch = elapsed_time / current_batches
            remaining_batches = total_batches - current_batches
            remaining_time = time_per_batch * remaining_batches
            
            rem_hours = int(remaining_time // 3600)
            rem_minutes = int((remaining_time % 3600) // 60)
            rem_seconds = int(remaining_time % 60)
            
            if remaining_time < 60:
                self.stats_labels["Estimated Remaining:"].config(text=f"{rem_seconds} seconds")
            elif remaining_time < 3600:
                self.stats_labels["Estimated Remaining:"].config(text=f"{rem_minutes}m {rem_seconds}s")
            else:
                self.stats_labels["Estimated Remaining:"].config(text=f"{rem_hours}h {rem_minutes}m")
    
    def update_progress_ui(self, progress, current_batches, total_batches):
        """Update progress bar and labels from main thread - based on batches"""
        self.progress_var.set(progress)
        self.progress_percent_label.config(text=f"{progress}%")
        self.progress_count_label.config(text=f"{current_batches}/{total_batches} batches")
    
    def translate_logic(self):
        try:
            BATCH_SIZE = 30
            RATE_LIMIT = 1
            
            # Get file paths
            dir_name = os.path.dirname(self.input_file_path)
            base_name = os.path.basename(self.input_file_path)
            output_dir = os.path.join(dir_name, "translated")
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"translated_{base_name}")
            
            # Load all original phrases
            with open(self.input_file_path, 'r', encoding='utf-8') as file:
                all_phrases = [line.strip() for line in file if line.strip()]
            
            total_phrases = len(all_phrases)
            total_batches = (total_phrases + BATCH_SIZE - 1) // BATCH_SIZE
            
            # Check how many already translated
            lines_already_done = 0
            if os.path.exists(output_path):
                with open(output_path, 'r', encoding='utf-8') as f:
                    lines_already_done = sum(1 for line in f)
            
            # Calculate completed batches
            completed_batches = (lines_already_done + BATCH_SIZE - 1) // BATCH_SIZE
            
            # Filter to only get the remaining phrases
            phrases_to_translate = all_phrases[lines_already_done:]
            
            if not phrases_to_translate:
                self.add_status_message("✅ File already fully translated!")
                self.current_status_label.config(text="✅ Translation complete!", fg='#27ae60')
                self.root.after(0, self.translation_finished)
                return
            
            self.add_status_message(f"🚀 Starting translation from line {lines_already_done + 1}")
            self.add_status_message(f"📝 Total lines to translate: {len(phrases_to_translate)}")
            self.add_status_message(f"📦 Total batches to process: {(len(phrases_to_translate) + BATCH_SIZE - 1) // BATCH_SIZE}")
            
            # Translate remaining
            for i in range(0, len(phrases_to_translate), BATCH_SIZE):
                if not self.is_translating:
                    self.add_status_message("⏸ Translation paused by user")
                    self.current_status_label.config(text="⏸ Paused - Click START to resume", fg='#e67e22')
                    break
                
                batch = phrases_to_translate[i:i + BATCH_SIZE]
                current_batch_num = completed_batches + (i // BATCH_SIZE) + 1
                
                self.add_status_message(f"🔄 Translating batch {current_batch_num}/{total_batches} ({len(batch)} lines)...")
                
                try:
                    translations = self.translator.translate_batch(batch)
                    
                    # Append to file
                    with open(output_path, 'a', encoding='utf-8') as file:
                        for original, translated in zip(batch, translations):
                            file.write(f"{original}\t{translated}\n")
                    
                    # Update progress based on BATCHES
                    current_total_done_lines = lines_already_done + i + len(batch)
                    current_batches_done = (current_total_done_lines + BATCH_SIZE - 1) // BATCH_SIZE
                    batch_progress = int((current_batches_done / total_batches) * 100)
                    
                    # Update UI from main thread
                    self.root.after(0, self.update_progress_ui, batch_progress, current_batches_done, total_batches)
                    
                    # Update stats (elapsed_time will be handled by the counter)
                    elapsed_time = time.time() - self.start_time
                    self.root.after(0, self.update_stats, current_total_done_lines, total_phrases, 
                                  current_batches_done, total_batches, elapsed_time)
                    
                    time.sleep(RATE_LIMIT)
                    
                except Exception as e:
                    error_message = str(e)
                    self.add_status_message(f"❌ Translation error: {error_message}", error=True)
                    self.add_status_message("💾 Progress saved - Will resume from last successful batch on next run")
                    
                    # Show popup alert for connection/network errors
                    error_type = "Connection Error"
                    if "timeout" in error_message.lower():
                        error_type = "Network Timeout Error"
                    elif "connection" in error_message.lower():
                        error_type = "Internet Connection Error"
                    elif "ssl" in error_message.lower():
                        error_type = "SSL Certificate Error"
                    
                    # Show popup in main thread
                    self.root.after(0, self.show_error_popup, 
                                  f"Translation stopped due to: {error_message}\n\nPlease check your internet connection and click START to resume.",
                                  error_type)
                    
                    self.root.after(0, self.translation_finished)
                    return
            
            if self.is_translating:
                self.add_status_message("🎉 Translation completed successfully!")
                self.current_status_label.config(text="✅ Translation complete!", fg='#27ae60')
                self.root.after(0, self.translation_finished)
            
        except Exception as e:
            error_message = str(e)
            self.add_status_message(f"❌ Critical error: {error_message}", error=True)
            
            # Show popup for critical errors
            self.root.after(0, self.show_error_popup, 
                          f"Critical error occurred: {error_message}\n\nPlease check your internet connection and click START to resume.",
                          "Critical Error")
            
            self.root.after(0, self.translation_finished)
    
    def start_translation(self):
        if not self.input_file_path or not os.path.isfile(self.input_file_path):
            messagebox.showerror("Error", "Please select a valid file first!")
            return
        
        if self.is_translating:
            messagebox.showinfo("Info", "Translation already in progress!")
            return
        
        # Check internet connection before starting
        if not self.check_internet_connection():
            self.show_error_popup(
                "No internet connection detected!\n\nPlease connect to the internet and try again.",
                "No Internet Connection"
            )
            return
        
        # Reset and start
        self.is_translating = True
        self.start_time = time.time()
        self.elapsed_time = 0
        self.error_occurred = False
        
        # Update button states
        self.btn_start.config(state=tk.DISABLED, text="⏳ TRANSLATING...", bg='#219a52')
        self.btn_stop.config(state=tk.NORMAL)
        self.btn_reset.config(state=tk.DISABLED)
        self.btn_browse.config(state=tk.DISABLED)
        
        self.current_status_label.config(text="🔄 Translating... Please wait", fg='#3498db')
        self.debug_label.config(text="Translation in progress...", fg='#3498db')
        self.add_status_message("▶ Translation started...")
        
        # Start translation in thread
        self.translation_thread = threading.Thread(target=self.translate_logic, daemon=True)
        self.translation_thread.start()
    
    def stop_translation(self):
        if self.is_translating:
            self.is_translating = False
            self.add_status_message("⏸ Pausing translation...")
            self.current_status_label.config(text="⏸ Pausing...", fg='#e67e22')
    
    def translation_finished(self):
        """Clean up after translation finishes or pauses"""
        self.is_translating = False
        self.btn_start.config(state=tk.NORMAL, text="▶ START TRANSLATION", bg='#27ae60')
        self.btn_stop.config(state=tk.DISABLED)
        self.btn_reset.config(state=tk.NORMAL)
        self.btn_browse.config(state=tk.NORMAL)
        
        # Re-enable start button if file exists and not fully translated
        if self.input_file_path and os.path.exists(self.input_file_path):
            # Check if already fully translated
            dir_name = os.path.dirname(self.input_file_path)
            base_name = os.path.basename(self.input_file_path)
            output_path = os.path.join(dir_name, "translated", f"translated_{base_name}")
            
            if os.path.exists(output_path):
                with open(self.input_file_path, 'r', encoding='utf-8') as f:
                    total_lines = sum(1 for line in f if line.strip())
                with open(output_path, 'r', encoding='utf-8') as f:
                    translated_lines = sum(1 for line in f)
                
                if translated_lines >= total_lines:
                    self.btn_start.config(state=tk.DISABLED)
                    self.current_status_label.config(text="✅ Translation complete!", fg='#27ae60')
                    self.debug_label.config(text="Translation complete!", fg='#27ae60')
            else:
                self.current_status_label.config(text="✅ Ready - Click START to begin", fg='#27ae60')
                self.debug_label.config(text="✓ Buttons enabled - Ready to translate", fg='#27ae60')
    
    def reset_progress(self):
        """Delete the translated file to start fresh"""
        if not self.input_file_path:
            return
        
        if self.is_translating:
            messagebox.showwarning("Warning", "Please pause translation before resetting!")
            return
        
        dir_name = os.path.dirname(self.input_file_path)
        base_name = os.path.basename(self.input_file_path)
        output_dir = os.path.join(dir_name, "translated")
        output_path = os.path.join(output_dir, f"translated_{base_name}")
        
        if os.path.exists(output_path):
            if messagebox.askyesno("Confirm Reset", "This will delete all translated progress. Are you sure?"):
                os.remove(output_path)
                self.add_status_message("🔄 Translation progress reset. Starting fresh next time.")
                self.progress_var.set(0)
                self.progress_percent_label.config(text="0%")
                self.progress_count_label.config(text="0/0 batches")
                
                # Get total lines and batches
                with open(self.input_file_path, 'r', encoding='utf-8') as f:
                    total_lines = sum(1 for line in f if line.strip())
                
                BATCH_SIZE = 30
                total_batches = (total_lines + BATCH_SIZE - 1) // BATCH_SIZE
                
                self.stats_labels["Translated Lines:"].config(text="0")
                self.stats_labels["Completed Batches:"].config(text="0")
                self.stats_labels["Remaining Lines:"].config(text=str(total_lines))
                self.stats_labels["Remaining Batches:"].config(text=str(total_batches))
                self.stats_labels["Time Elapsed:"].config(text="00:00:00")
                self.stats_labels["Estimated Remaining:"].config(text="Calculating...")
                self.current_status_label.config(text="✅ Reset complete - Ready to translate", fg='#27ae60')
                self.debug_label.config(text="✓ Reset complete - Ready to translate", fg='#27ae60')
                
                # Re-enable start button
                self.btn_start.config(state=tk.NORMAL)
                
                # Flash the start button
                self.flash_button(self.btn_start)
        else:
            messagebox.showinfo("Info", "No translation file found to reset!")

if __name__ == "__main__":
    root = tk.Tk()
    app = LugandaTranslatorApp(root)
    root.mainloop()