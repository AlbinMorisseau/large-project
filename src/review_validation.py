import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import random

class ReviewValidator:
    def __init__(self, root):
        self.root = root
        self.root.title("Reviews Validator")
        self.root.geometry("800x600")
        
        self.df = None
        self.sample_indices = []
        self.current_index = 0
        self.rejected_reviews = []
        
        self.setup_ui()
    
    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Bouton pour charger le fichier
        self.load_btn = ttk.Button(main_frame, text="Load CSV File", 
                                    command=self.load_csv)
        self.load_btn.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Label de progression
        self.progress_label = ttk.Label(main_frame, text="Load a file to start")
        self.progress_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Zone de texte pour afficher la review
        self.text_frame = ttk.LabelFrame(main_frame, text="Review", padding="10")
        self.text_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.review_text = tk.Text(self.text_frame, wrap=tk.WORD, height=20, 
                                    font=("Arial", 11))
        self.review_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar pour le texte
        scrollbar = ttk.Scrollbar(self.text_frame, orient=tk.VERTICAL, 
                                  command=self.review_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.review_text.config(yscrollcommand=scrollbar.set)
        
        # Frame pour les boutons de validation
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        # Bouton "Ne pas valider"
        self.reject_btn = ttk.Button(button_frame, text="❌ Not valid", 
                                      command=self.reject_review, state=tk.DISABLED)
        self.reject_btn.grid(row=0, column=0, padx=10, ipadx=20, ipady=10)
        
        # Bouton "Valider"
        self.validate_btn = ttk.Button(button_frame, text="✓ Valid", 
                                        command=self.validate_review, state=tk.DISABLED)
        self.validate_btn.grid(row=0, column=1, padx=10, ipadx=20, ipady=10)
        
        # Configuration du redimensionnement
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        self.text_frame.columnconfigure(0, weight=1)
        self.text_frame.rowconfigure(0, weight=1)
    
    def load_csv(self):
        file_path = filedialog.askopenfilename(
            title="Seelct a CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            self.df = pd.read_csv(file_path)
            
            if 'review' not in self.df.columns:
                messagebox.showerror("Erreur", 
                    "The file does not contain a column 'review'")
                return
            
            # Sélectionner 10% des données aléatoirement
            sample_size = max(1, int(len(self.df) * 0.1))
            self.sample_indices = random.sample(range(len(self.df)), sample_size)
            self.current_index = 0
            self.rejected_reviews = []
            
            # Activer les boutons
            self.validate_btn.config(state=tk.NORMAL)
            self.reject_btn.config(state=tk.NORMAL)
            
            # Afficher la première review
            self.display_current_review()
            
            messagebox.showinfo("Sucess", 
                f"File loaded with !\n{sample_size} reviewsto validate (10% of total)")
            
        except Exception as e:
            messagebox.showerror("Error", f"Loading error: {str(e)}")
    
    def display_current_review(self):
        if self.current_index >= len(self.sample_indices):
            self.finish_validation()
            return
        
        # Obtenir l'indice dans le dataframe original
        original_index = self.sample_indices[self.current_index]
        review = self.df.loc[original_index, 'review']
        
        # Mettre à jour le label de progression
        self.progress_label.config(
            text=f"Review {self.current_index + 1}/{len(self.sample_indices)} - "
                 f"Indice original: {original_index}"
        )
        
        # Afficher la review
        self.review_text.config(state=tk.NORMAL)
        self.review_text.delete(1.0, tk.END)
        self.review_text.insert(1.0, str(review))
        self.review_text.config(state=tk.DISABLED)
    
    def validate_review(self):
        self.current_index += 1
        self.display_current_review()
    
    def reject_review(self):
        original_index = self.sample_indices[self.current_index]
        review = self.df.loc[original_index, 'review']
        
        self.rejected_reviews.append({
            'original_index': original_index,
            'review': review
        })
        
        self.current_index += 1
        self.display_current_review()
    
    def finish_validation(self):
        if len(self.rejected_reviews) > 0:
            # Créer un dataframe avec les reviews rejetées
            rejected_df = pd.DataFrame(self.rejected_reviews)
            
            # Sauvegarder dans un fichier CSV
            save_path = filedialog.asksaveasfilename(
                title="Sauvegarder les reviews non validées",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if save_path:
                rejected_df.to_csv(save_path, index=False)
                messagebox.showinfo("Terminé", 
                    f"Validation terminée!\n"
                    f"{len(self.rejected_reviews)} reviews non validées sauvegardées.")
            else:
                messagebox.showinfo("Terminé", 
                    "Validation terminée mais fichier non sauvegardé.")
        else:
            messagebox.showinfo("Terminé", 
                "Validation terminée!\nAucune review rejetée.")
        
        # Désactiver les boutons
        self.validate_btn.config(state=tk.DISABLED)
        self.reject_btn.config(state=tk.DISABLED)
        self.progress_label.config(text="Validation terminée")
        self.review_text.config(state=tk.NORMAL)
        self.review_text.delete(1.0, tk.END)
        self.review_text.config(state=tk.DISABLED)

# Créer et lancer l'application
if __name__ == "__main__":
    root = tk.Tk()
    app = ReviewValidator(root)
    root.mainloop()