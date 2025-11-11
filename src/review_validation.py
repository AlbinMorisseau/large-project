import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import random
import os
import json

class ReviewValidator:
    def __init__(self, root):
        self.root = root
        self.root.title("Reviews Validator")
        self.root.geometry("900x700")
        
        self.df = None
        self.sample_indices = []
        self.current_index = 0
        self.validated_reviews = []
        self.rejected_reviews = []
        self.input_file_path = None
        self.session_file = None
        
        self.setup_ui()
        self.check_existing_session()
    
    def setup_ui(self):
        # ain frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configuration frame
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.grid(row=0, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        # Purcentage to validate
        ttk.Label(config_frame, text="Purcentage to validate:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.percentage_var = tk.StringVar(value="10")
        self.percentage_entry = ttk.Entry(config_frame, textvariable=self.percentage_var, width=10)
        self.percentage_entry.grid(row=0, column=1, padx=5)
        ttk.Label(config_frame, text="%").grid(row=0, column=2, sticky=tk.W)
        
        # Random choice or sequential
        ttk.Label(config_frame, text="Selection mode:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.selection_mode = tk.StringVar(value="random")
        self.random_radio = ttk.Radiobutton(config_frame, text="Random", 
                                            variable=self.selection_mode, value="random",
                                            command=self.toggle_start_index)
        self.random_radio.grid(row=1, column=1, padx=5, sticky=tk.W)
        self.sequential_radio = ttk.Radiobutton(config_frame, text="Sequential", 
                                                variable=self.selection_mode, value="sequential",
                                                command=self.toggle_start_index)
        self.sequential_radio.grid(row=1, column=2, padx=5, sticky=tk.W)
        
        # Beginning index (only for sequential)
        ttk.Label(config_frame, text="begining index:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.start_index_var = tk.StringVar(value="0")
        self.start_index_entry = ttk.Entry(config_frame, textvariable=self.start_index_var, 
                                           width=10, state=tk.DISABLED)
        self.start_index_entry.grid(row=2, column=1, padx=5)
        
        # Button to load a CSV
        self.load_btn = ttk.Button(main_frame, text="Load a CSV file", 
                                    command=self.load_csv)
        self.load_btn.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Label progression
        self.progress_label = ttk.Label(main_frame, text="Load a file to begin with.")
        self.progress_label.grid(row=2, column=0, columnspan=2, pady=5)
        
        # Text zone to print the review
        self.text_frame = ttk.LabelFrame(main_frame, text="Review ", padding="10")
        self.text_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.review_text = tk.Text(self.text_frame, wrap=tk.WORD, height=20, 
                                    font=("Arial", 11))
        self.review_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.text_frame, orient=tk.VERTICAL, 
                                  command=self.review_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.review_text.config(yscrollcommand=scrollbar.set)
        
        # Frame for validation buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        # Button "Reject"
        self.reject_btn = ttk.Button(button_frame, text="❌ Reject", 
                                      command=self.reject_review, state=tk.DISABLED)
        self.reject_btn.grid(row=0, column=0, padx=10, ipadx=20, ipady=10)
        
        # Button "Validate"
        self.validate_btn = ttk.Button(button_frame, text="✓ Validate", 
                                        command=self.validate_review, state=tk.DISABLED)
        self.validate_btn.grid(row=0, column=1, padx=10, ipadx=20, ipady=10)
        
        # Dimension configuration
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        self.text_frame.columnconfigure(0, weight=1)
        self.text_frame.rowconfigure(0, weight=1)
        
        # Closing event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def toggle_start_index(self):
        if self.selection_mode.get() == "sequential":
            self.start_index_entry.config(state=tk.NORMAL)
        else:
            self.start_index_entry.config(state=tk.DISABLED)
    
    def check_existing_session(self):
        """Verify if there is an exisiitng session"""
        session_file = "review_validator_session.json"
        if os.path.exists(session_file):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                # verify that the CSV file still exist
                if os.path.exists(session_data['input_file_path']):
                    response = messagebox.askyesno(
                        "Session found",
                        f"A session has been found for:\n{session_data['input_file_path']}\n\n"
                        f"Progression: {session_data['current_index']}/{session_data['total_reviews']} reviews\n"
                        f"Validated: {len(session_data['validated_reviews'])}\n"
                        f"Rejected: {len(session_data['rejected_reviews'])}\n\n"
                        f"Do you want to keep working on this session ?"
                    )
                    
                    if response:
                        self.load_session(session_data)
                    else:
                        # supress the session if not
                        os.remove(session_file)
                else:
                    # supress session if CSV file is note here anymore
                    os.remove(session_file)
            except Exception as e:
                print(f"CSV loading error: {e}")
                if os.path.exists(session_file):
                    os.remove(session_file)
    
    def load_session(self, session_data):
        """Load a saved session"""
        try:
            self.input_file_path = session_data['input_file_path']
            self.df = pd.read_csv(self.input_file_path)
            
            # Reload configuration
            self.percentage_var.set(str(session_data['percentage']))
            self.selection_mode.set(session_data['selection_mode'])
            self.start_index_var.set(str(session_data['start_index']))
            self.toggle_start_index()
            
            # Reload validation data
            self.sample_indices = session_data['sample_indices']
            self.current_index = session_data['current_index']
            self.validated_reviews = session_data['validated_reviews']
            self.rejected_reviews = session_data['rejected_reviews']
            
            # Activate buttons
            self.validate_btn.config(state=tk.NORMAL)
            self.reject_btn.config(state=tk.NORMAL)
            
            # Print current review
            self.display_current_review()
            
            messagebox.showinfo("Session reloaded", 
                f"Session reloaded with success !\n"
                f"Keep going from review {self.current_index + 1}/{len(self.sample_indices)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error while reloading session: {str(e)}")
    
    def save_session(self):
        """Save current session"""
        if self.df is None or self.input_file_path is None:
            return
        
        session_data = {
            'input_file_path': self.input_file_path,
            'percentage': float(self.percentage_var.get()),
            'selection_mode': self.selection_mode.get(),
            'start_index': int(self.start_index_var.get()),
            'sample_indices': self.sample_indices,
            'current_index': self.current_index,
            'total_reviews': len(self.sample_indices),
            'validated_reviews': self.validated_reviews,
            'rejected_reviews': self.rejected_reviews
        }
        
        session_file = "review_validator_session.json"
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error while saving the session: {e}")
    
    def clear_session(self):
        """Delete session file"""
        session_file = "review_validator_session.json"
        if os.path.exists(session_file):
            try:
                os.remove(session_file)
            except Exception as e:
                print(f"Error while supressing session file: {e}")
    
    def on_closing(self):
        """Application closing gestion"""
        if self.df is not None and self.current_index < len(self.sample_indices):
            # if there is an active session
            response = messagebox.askyesnocancel(
                "Leaving",
                "Do you want to save your current state before leaving ?\n\n"
                "Yes\n"
                "No:\n"
                "Cancel: Continue to work"
            )
            
            if response is None:  # Cancel
                return
            elif response:  # Yes, save
                self.save_session()
                self.save_progress_files()
            else:  # No, don't save
                self.clear_session()
        
        self.root.destroy()
    
    def save_progress_files(self):
        """save intermediate progresses"""
        # Creat destination file if it does not exist
        output_dir = os.path.join("..","data", "processed", "validation")
        os.makedirs(output_dir, exist_ok=True)
        
        # get file name  without extension
        base_name = os.path.splitext(os.path.basename(self.input_file_path))[0]
        
        # save validated reviews
        if len(self.validated_reviews) > 0:
            validated_df = pd.DataFrame(self.validated_reviews)
            positive_path = os.path.join(output_dir, f"{base_name}_positive.csv")
            validated_df.to_csv(positive_path, index=False)
        
        # Save rejected reviews
        if len(self.rejected_reviews) > 0:
            rejected_df = pd.DataFrame(self.rejected_reviews)
            negative_path = os.path.join(output_dir, f"{base_name}_negative.csv")
            rejected_df.to_csv(negative_path, index=False)
    
    def load_csv(self):
        # Erase current session if loading a new CSV file
        if self.df is not None:
            response = messagebox.askyesno(
                "Loading a new file",
                "Loading a new file will erase the current session.\n"
                "Do you want to continue ?"
            )
            if not response:
                return
            self.clear_session()
        
        file_path = filedialog.askopenfilename(
            title="Select a CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            self.df = pd.read_csv(file_path)
            self.input_file_path = file_path
            
            if 'review' not in self.df.columns:
                messagebox.showerror("Error", 
                    "Le file does not contains 'review' column")
                return
            
            # Validate purcentage
            try:
                percentage = float(self.percentage_var.get())
                if percentage <= 0 or percentage > 100:
                    raise ValueError()
            except ValueError:
                messagebox.showerror("Error", 
                    "Purcentage must be between 0 and 100")
                return
            
            # Calculate sample size
            sample_size = max(1, int(len(self.df) * percentage / 100))
            
            # Select indexes depending on the mode
            if self.selection_mode.get() == "random":
                self.sample_indices = random.sample(range(len(self.df)), sample_size)
            else:
                # Sequential mode
                try:
                    start_idx = int(self.start_index_var.get())
                    if start_idx < 0 or start_idx >= len(self.df):
                        raise ValueError()
                except ValueError:
                    messagebox.showerror("Error", 
                        f"The starting index must be between 0 and {len(self.df)-1}")
                    return
                
                end_idx = min(start_idx + sample_size, len(self.df))
                self.sample_indices = list(range(start_idx, end_idx))
            
            self.current_index = 0
            self.validated_reviews = []
            self.rejected_reviews = []
            
            # Buttons activation
            self.validate_btn.config(state=tk.NORMAL)
            self.reject_btn.config(state=tk.NORMAL)
            
            # Print first review
            self.display_current_review()
            
            mode_text = "random" if self.selection_mode.get() == "random" else "sequential"
            messagebox.showinfo("Sucess", 
                f"File loaded with success \n{len(self.sample_indices)} reviews to validate "
                f"({percentage}% of total)\nMode: {mode_text}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Loading error: {str(e)}")
    
    def display_current_review(self):
        if self.current_index >= len(self.sample_indices):
            self.finish_validation()
            return
        
        # get original index from the dataframe
        original_index = self.sample_indices[self.current_index]
        review = self.df.loc[original_index, 'review']
        
        # Update label progression
        self.progress_label.config(
            text=f"Review {self.current_index + 1}/{len(self.sample_indices)} - "
                 f"Indice original: {original_index}"
        )
        
        # Print the review
        self.review_text.config(state=tk.NORMAL)
        self.review_text.delete(1.0, tk.END)
        self.review_text.insert(1.0, str(review))
    
    def validate_review(self):
        original_index = self.sample_indices[self.current_index]
        # Get the text
        review = self.review_text.get(1.0, tk.END).strip()
        
        self.validated_reviews.append({
            'original_index': original_index,
            'review': review
        })
        
        self.current_index += 1
        # Save the session after validation
        self.save_session()
        self.display_current_review()
    
    def reject_review(self):
        original_index = self.sample_indices[self.current_index]
        # Get the text
        review = self.review_text.get(1.0, tk.END).strip()
        
        self.rejected_reviews.append({
            'original_index': original_index,
            'review': review
        })
        
        self.current_index += 1
        # Save the session after each reject
        self.save_session()
        self.display_current_review()
    
    def finish_validation(self):
        # Create the destination folder if it does note exists
        output_dir = os.path.join("data", "processes", "validation")
        os.makedirs(output_dir, exist_ok=True)
        
        # Get the original file name without extension
        base_name = os.path.splitext(os.path.basename(self.input_file_path))[0]
        positive_path = os.path.join(output_dir, f"{base_name}_positive.csv")
        negative_path = os.path.join(output_dir, f"{base_name}_negative.csv")
        
        # Save the validated reviews
        if len(self.validated_reviews) > 0:
            validated_df = pd.DataFrame(self.validated_reviews)
            validated_df.to_csv(positive_path, index=False)
        
        # Save the rejected reviews
        if len(self.rejected_reviews) > 0:
            rejected_df = pd.DataFrame(self.rejected_reviews)
            rejected_df.to_csv(negative_path, index=False)
        
        # Delete the ended session
        self.clear_session()
        
        # Confirmation message
        message = "Validation ended!\n\n"
        if len(self.validated_reviews) > 0:
            message += f"✓ {len(self.validated_reviews)} validated reviews saved in:\n{positive_path}\n\n"
        if len(self.rejected_reviews) > 0:
            message += f"✗ {len(self.rejected_reviews)} rejected reviews saved in:\n{negative_path}"
        
        if len(self.validated_reviews) == 0 and len(self.rejected_reviews) == 0:
            message = "Validation ended !\nNo reviews processed."
        
        messagebox.showinfo("Ended", message)
        
        # Deactivate buttons
        self.validate_btn.config(state=tk.DISABLED)
        self.reject_btn.config(state=tk.DISABLED)
        self.progress_label.config(text="Validation ended")
        self.review_text.config(state=tk.NORMAL)
        self.review_text.delete(1.0, tk.END)

# Create and launch the app
if __name__ == "__main__":
    root = tk.Tk()
    app = ReviewValidator(root)
    root.mainloop()