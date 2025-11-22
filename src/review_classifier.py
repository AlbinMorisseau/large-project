import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json

class ReviewLabeler:
    def __init__(self, root):
        self.root = root
        self.root.title("Reviews Multi-Label Classifier")
        self.root.geometry("900x750")
        
        self.df = None
        self.current_index = 0
        self.labeled_reviews = []
        self.input_file_path = None
        self.output_path = None
        
        # État des checkboxes pour la review courante
        self.handicap_var = tk.IntVar(value=0)
        self.pet_var = tk.IntVar(value=0)
        self.child_var = tk.IntVar(value=0)
        
        self.setup_ui()
        self.check_existing_session()
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Button to load CSV
        self.load_btn = ttk.Button(main_frame, text="Charger un fichier CSV", 
                                    command=self.load_csv)
        self.load_btn.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Progress label
        self.progress_label = ttk.Label(main_frame, text="Chargez un fichier pour commencer.")
        self.progress_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        # Text zone for review display
        self.text_frame = ttk.LabelFrame(main_frame, text="Review", padding="10")
        self.text_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.review_text = tk.Text(self.text_frame, wrap=tk.WORD, height=15, 
                                    font=("Arial", 11), state=tk.DISABLED)
        self.review_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.text_frame, orient=tk.VERTICAL, 
                                  command=self.review_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.review_text.config(yscrollcommand=scrollbar.set)
        
        # Category selection frame
        category_frame = ttk.LabelFrame(main_frame, text="Catégories", padding="15")
        category_frame.grid(row=3, column=0, columnspan=2, pady=15, sticky=(tk.W, tk.E))
        
        # Checkboxes for categories
        self.handicap_check = ttk.Checkbutton(category_frame, text="♿ Handicap", 
                                              variable=self.handicap_var,
                                              state=tk.DISABLED)
        self.handicap_check.grid(row=0, column=0, padx=20, pady=5)
        
        self.pet_check = ttk.Checkbutton(category_frame, text="🐾 Pet", 
                                         variable=self.pet_var,
                                         state=tk.DISABLED)
        self.pet_check.grid(row=0, column=1, padx=20, pady=5)
        
        self.child_check = ttk.Checkbutton(category_frame, text="👶 Child", 
                                           variable=self.child_var,
                                           state=tk.DISABLED)
        self.child_check.grid(row=0, column=2, padx=20, pady=5)
        
        # Navigation buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        # Previous button
        self.prev_btn = ttk.Button(button_frame, text="⬅ Précédent", 
                                    command=self.previous_review, 
                                    state=tk.DISABLED)
        self.prev_btn.grid(row=0, column=0, padx=10, ipadx=15, ipady=10)
        
        # Save and next button
        self.next_btn = ttk.Button(button_frame, text="Enregistrer et Suivant ➡", 
                                    command=self.save_and_next, 
                                    state=tk.DISABLED)
        self.next_btn.grid(row=0, column=1, padx=10, ipadx=15, ipady=10)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        self.text_frame.columnconfigure(0, weight=1)
        self.text_frame.rowconfigure(0, weight=1)
        
        # Closing event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def check_existing_session(self):
        """Vérifier s'il existe une session en cours"""
        session_file = "review_labeler_session.json"
        if os.path.exists(session_file):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                if os.path.exists(session_data['input_file_path']):
                    response = messagebox.askyesno(
                        "Session trouvée",
                        f"Une session a été trouvée pour:\n{session_data['input_file_path']}\n\n"
                        f"Progression: {session_data['current_index']}/{session_data['total_reviews']} reviews\n\n"
                        f"Voulez-vous reprendre cette session ?"
                    )
                    
                    if response:
                        self.load_session(session_data)
                    else:
                        os.remove(session_file)
                else:
                    os.remove(session_file)
            except Exception as e:
                print(f"Erreur de chargement de session: {e}")
                if os.path.exists(session_file):
                    os.remove(session_file)
    
    def load_session(self, session_data):
        """Charger une session sauvegardée"""
        try:
            self.input_file_path = session_data['input_file_path']
            self.output_path = session_data.get('output_path')
            self.df = pd.read_csv(self.input_file_path)
            self.current_index = session_data['current_index']
            self.labeled_reviews = session_data['labeled_reviews']
            
            # Activer les contrôles
            self.handicap_check.config(state=tk.NORMAL)
            self.pet_check.config(state=tk.NORMAL)
            self.child_check.config(state=tk.NORMAL)
            self.next_btn.config(state=tk.NORMAL)
            self.prev_btn.config(state=tk.NORMAL if self.current_index > 0 else tk.DISABLED)
            
            # Afficher la review courante
            self.display_current_review()
            
            messagebox.showinfo("Session rechargée", 
                f"Session rechargée avec succès !\n"
                f"Reprise à la review {self.current_index + 1}/{len(self.df)}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du rechargement: {str(e)}")
    
    def generate_output_path(self):
        """Générer le chemin de sortie pour les reviews labellisées"""
        if self.input_file_path is None:
            return None
        
        # Créer le dossier de destination
        output_dir = os.path.join("..","data", "processed", "validation")
        os.makedirs(output_dir, exist_ok=True)
        
        # Obtenir le nom du fichier original
        base_name = os.path.splitext(os.path.basename(self.input_file_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}_labeled.csv")
        
        return output_path
    
    def save_labeled_data(self):
        """Sauvegarder les reviews labellisées jusqu'à présent"""
        if not self.labeled_reviews:
            return
        
        if self.output_path is None:
            self.output_path = self.generate_output_path()
        
        try:
            # Créer le DataFrame avec les reviews labellisées
            result_df = self.df.iloc[:len(self.labeled_reviews)][['review']].copy()
            
            # Ajouter les colonnes de labels
            for i, labels in enumerate(self.labeled_reviews):
                result_df.loc[result_df.index[i], 'handicap'] = labels['handicap']
                result_df.loc[result_df.index[i], 'pet'] = labels['pet']
                result_df.loc[result_df.index[i], 'child'] = labels['child']
            
            # Convertir en entiers
            result_df['handicap'] = result_df['handicap'].astype(int)
            result_df['pet'] = result_df['pet'].astype(int)
            result_df['child'] = result_df['child'].astype(int)
            
            # Sauvegarder le fichier
            result_df.to_csv(self.output_path, index=False)
            
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des données: {e}")
    
    def save_session(self):
        """Sauvegarder la session actuelle"""
        if self.df is None or self.input_file_path is None:
            return
        
        # Générer l'output_path si nécessaire
        if self.output_path is None:
            self.output_path = self.generate_output_path()
        
        session_data = {
            'input_file_path': self.input_file_path,
            'output_path': self.output_path,
            'current_index': self.current_index,
            'total_reviews': len(self.df),
            'labeled_reviews': self.labeled_reviews
        }
        
        session_file = "review_labeler_session.json"
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            # Sauvegarder également les données labellisées
            self.save_labeled_data()
            
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de session: {e}")
    
    def clear_session(self):
        """Supprimer le fichier de session"""
        session_file = "review_labeler_session.json"
        if os.path.exists(session_file):
            try:
                os.remove(session_file)
            except Exception as e:
                print(f"Erreur lors de la suppression du fichier de session: {e}")
    
    def load_csv(self):
        if self.df is not None:
            response = messagebox.askyesno(
                "Charger un nouveau fichier",
                "Charger un nouveau fichier effacera la session en cours.\n"
                "Voulez-vous continuer ?"
            )
            if not response:
                return
            self.clear_session()
        
        file_path = filedialog.askopenfilename(
            title="Sélectionner un fichier CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            self.df = pd.read_csv(file_path)
            self.input_file_path = file_path
            self.output_path = self.generate_output_path()
            
            if 'review' not in self.df.columns:
                messagebox.showerror("Erreur", 
                    "Le fichier ne contient pas de colonne 'review'")
                return
            
            self.current_index = 0
            self.labeled_reviews = []
            
            # Activer les contrôles
            self.handicap_check.config(state=tk.NORMAL)
            self.pet_check.config(state=tk.NORMAL)
            self.child_check.config(state=tk.NORMAL)
            self.next_btn.config(state=tk.NORMAL)
            
            # Afficher la première review
            self.display_current_review()
            
            messagebox.showinfo("Succès", 
                f"Fichier chargé avec succès !\n{len(self.df)} reviews à labelliser\n\n"
                f"Sauvegarde dans:\n{self.output_path}")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur de chargement: {str(e)}")
    
    def display_current_review(self):
        """Afficher la review courante"""
        if self.current_index >= len(self.df):
            self.finish_labeling()
            return
        
        review = self.df.loc[self.current_index, 'review']
        
        # Mise à jour du label de progression
        self.progress_label.config(
            text=f"Review {self.current_index + 1}/{len(self.df)}"
        )
        
        # Afficher la review
        self.review_text.config(state=tk.NORMAL)
        self.review_text.delete(1.0, tk.END)
        self.review_text.insert(1.0, str(review))
        self.review_text.config(state=tk.DISABLED)
        
        # Charger les labels existants si disponibles
        if self.current_index < len(self.labeled_reviews):
            labels = self.labeled_reviews[self.current_index]
            self.handicap_var.set(labels['handicap'])
            self.pet_var.set(labels['pet'])
            self.child_var.set(labels['child'])
        else:
            # Réinitialiser les checkboxes
            self.handicap_var.set(0)
            self.pet_var.set(0)
            self.child_var.set(0)
        
        # Gérer le bouton précédent
        self.prev_btn.config(state=tk.NORMAL if self.current_index > 0 else tk.DISABLED)
    
    def save_and_next(self):
        """Enregistrer les labels et passer à la review suivante"""
        # Sauvegarder les labels actuels
        labels = {
            'handicap': self.handicap_var.get(),
            'pet': self.pet_var.get(),
            'child': self.child_var.get()
        }
        
        # Mettre à jour ou ajouter les labels
        if self.current_index < len(self.labeled_reviews):
            self.labeled_reviews[self.current_index] = labels
        else:
            self.labeled_reviews.append(labels)
        
        # Passer à la review suivante
        self.current_index += 1
        
        # Sauvegarder la session et les données
        self.save_session()
        
        # Afficher la review suivante
        self.display_current_review()
    
    def previous_review(self):
        """Revenir à la review précédente"""
        if self.current_index > 0:
            self.current_index -= 1
            self.display_current_review()
    
    def finish_labeling(self):
        """Terminer la labellisation et sauvegarder le fichier"""
        # Sauvegarder une dernière fois
        self.save_labeled_data()
        
        # Supprimer la session
        self.clear_session()
        
        # Message de confirmation
        messagebox.showinfo("Terminé", 
            f"Labellisation terminée !\n\n"
            f"Fichier sauvegardé dans:\n{self.output_path}\n\n"
            f"Total: {len(self.labeled_reviews)} reviews labellisées")
        
        # Désactiver les contrôles
        self.handicap_check.config(state=tk.DISABLED)
        self.pet_check.config(state=tk.DISABLED)
        self.child_check.config(state=tk.DISABLED)
        self.next_btn.config(state=tk.DISABLED)
        self.prev_btn.config(state=tk.DISABLED)
        self.progress_label.config(text="Labellisation terminée")
        self.review_text.config(state=tk.NORMAL)
        self.review_text.delete(1.0, tk.END)
        self.review_text.config(state=tk.DISABLED)
    
    def on_closing(self):
        """Gestion de la fermeture de l'application"""
        if self.df is not None and self.current_index < len(self.df):
            response = messagebox.askyesnocancel(
                "Quitter",
                "Voulez-vous sauvegarder votre progression avant de quitter ?\n\n"
                "Oui: Sauvegarder et quitter\n"
                "Non: Quitter sans sauvegarder\n"
                "Annuler: Continuer à travailler"
            )
            
            if response is None:  # Annuler
                return
            elif response:  # Oui, sauvegarder
                self.save_session()
            else:  # Non, ne pas sauvegarder
                self.clear_session()
        
        self.root.destroy()

# Créer et lancer l'application
if __name__ == "__main__":
    root = tk.Tk()
    app = ReviewLabeler(root)
    root.mainloop()