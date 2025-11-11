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
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Frame de configuration
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.grid(row=0, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        # Pourcentage à valider
        ttk.Label(config_frame, text="Pourcentage à valider:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.percentage_var = tk.StringVar(value="10")
        self.percentage_entry = ttk.Entry(config_frame, textvariable=self.percentage_var, width=10)
        self.percentage_entry.grid(row=0, column=1, padx=5)
        ttk.Label(config_frame, text="%").grid(row=0, column=2, sticky=tk.W)
        
        # Choix aléatoire ou séquentiel
        ttk.Label(config_frame, text="Mode de sélection:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.selection_mode = tk.StringVar(value="random")
        self.random_radio = ttk.Radiobutton(config_frame, text="Aléatoire", 
                                            variable=self.selection_mode, value="random",
                                            command=self.toggle_start_index)
        self.random_radio.grid(row=1, column=1, padx=5, sticky=tk.W)
        self.sequential_radio = ttk.Radiobutton(config_frame, text="Séquentiel", 
                                                variable=self.selection_mode, value="sequential",
                                                command=self.toggle_start_index)
        self.sequential_radio.grid(row=1, column=2, padx=5, sticky=tk.W)
        
        # Indice de départ (seulement pour mode séquentiel)
        ttk.Label(config_frame, text="Indice de départ:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.start_index_var = tk.StringVar(value="0")
        self.start_index_entry = ttk.Entry(config_frame, textvariable=self.start_index_var, 
                                           width=10, state=tk.DISABLED)
        self.start_index_entry.grid(row=2, column=1, padx=5)
        
        # Bouton pour charger le fichier
        self.load_btn = ttk.Button(main_frame, text="Charger un fichier CSV", 
                                    command=self.load_csv)
        self.load_btn.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Label de progression
        self.progress_label = ttk.Label(main_frame, text="Charger un fichier pour commencer")
        self.progress_label.grid(row=2, column=0, columnspan=2, pady=5)
        
        # Zone de texte pour afficher la review
        self.text_frame = ttk.LabelFrame(main_frame, text="Review (modifiable)", padding="10")
        self.text_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
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
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        # Bouton "Rejeter"
        self.reject_btn = ttk.Button(button_frame, text="❌ Rejeter", 
                                      command=self.reject_review, state=tk.DISABLED)
        self.reject_btn.grid(row=0, column=0, padx=10, ipadx=20, ipady=10)
        
        # Bouton "Valider"
        self.validate_btn = ttk.Button(button_frame, text="✓ Valider", 
                                        command=self.validate_review, state=tk.DISABLED)
        self.validate_btn.grid(row=0, column=1, padx=10, ipadx=20, ipady=10)
        
        # Configuration du redimensionnement
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        self.text_frame.columnconfigure(0, weight=1)
        self.text_frame.rowconfigure(0, weight=1)
        
        # Gérer la fermeture de la fenêtre
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def toggle_start_index(self):
        if self.selection_mode.get() == "sequential":
            self.start_index_entry.config(state=tk.NORMAL)
        else:
            self.start_index_entry.config(state=tk.DISABLED)
    
    def check_existing_session(self):
        """Vérifie s'il existe une session en cours à reprendre"""
        session_file = "review_validator_session.json"
        if os.path.exists(session_file):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                # Vérifier que le fichier CSV existe toujours
                if os.path.exists(session_data['input_file_path']):
                    response = messagebox.askyesno(
                        "Session trouvée",
                        f"Une session en cours a été trouvée pour:\n{session_data['input_file_path']}\n\n"
                        f"Progression: {session_data['current_index']}/{session_data['total_reviews']} reviews\n"
                        f"Validées: {len(session_data['validated_reviews'])}\n"
                        f"Rejetées: {len(session_data['rejected_reviews'])}\n\n"
                        f"Voulez-vous reprendre cette session?"
                    )
                    
                    if response:
                        self.load_session(session_data)
                    else:
                        # Supprimer la session si l'utilisateur ne veut pas reprendre
                        os.remove(session_file)
                else:
                    # Le fichier n'existe plus, supprimer la session
                    os.remove(session_file)
            except Exception as e:
                print(f"Erreur lors de la lecture de la session: {e}")
                if os.path.exists(session_file):
                    os.remove(session_file)
    
    def load_session(self, session_data):
        """Charge une session sauvegardée"""
        try:
            self.input_file_path = session_data['input_file_path']
            self.df = pd.read_csv(self.input_file_path)
            
            # Restaurer la configuration
            self.percentage_var.set(str(session_data['percentage']))
            self.selection_mode.set(session_data['selection_mode'])
            self.start_index_var.set(str(session_data['start_index']))
            self.toggle_start_index()
            
            # Restaurer les données de validation
            self.sample_indices = session_data['sample_indices']
            self.current_index = session_data['current_index']
            self.validated_reviews = session_data['validated_reviews']
            self.rejected_reviews = session_data['rejected_reviews']
            
            # Activer les boutons
            self.validate_btn.config(state=tk.NORMAL)
            self.reject_btn.config(state=tk.NORMAL)
            
            # Afficher la review courante
            self.display_current_review()
            
            messagebox.showinfo("Session restaurée", 
                f"Session restaurée avec succès!\n"
                f"Reprise à la review {self.current_index + 1}/{len(self.sample_indices)}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la restauration de la session: {str(e)}")
    
    def save_session(self):
        """Sauvegarde la session en cours"""
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
            print(f"Erreur lors de la sauvegarde de la session: {e}")
    
    def clear_session(self):
        """Supprime le fichier de session"""
        session_file = "review_validator_session.json"
        if os.path.exists(session_file):
            try:
                os.remove(session_file)
            except Exception as e:
                print(f"Erreur lors de la suppression de la session: {e}")
    
    def on_closing(self):
        """Gère la fermeture de l'application"""
        if self.df is not None and self.current_index < len(self.sample_indices):
            # Il y a une session en cours non terminée
            response = messagebox.askyesnocancel(
                "Quitter",
                "Voulez-vous sauvegarder votre progression avant de quitter?\n\n"
                "Oui: Sauvegarder et quitter\n"
                "Non: Quitter sans sauvegarder\n"
                "Annuler: Continuer à travailler"
            )
            
            if response is None:  # Annuler
                return
            elif response:  # Oui, sauvegarder
                self.save_session()
                self.save_progress_files()
            else:  # Non, ne pas sauvegarder
                self.clear_session()
        
        self.root.destroy()
    
    def save_progress_files(self):
        """Sauvegarde les fichiers de progression intermédiaire"""
        # Créer le dossier de destination s'il n'existe pas
        output_dir = os.path.join("..","data", "processed", "validation")
        os.makedirs(output_dir, exist_ok=True)
        
        # Récupérer le nom du fichier original sans extension
        base_name = os.path.splitext(os.path.basename(self.input_file_path))[0]
        
        # Sauvegarder les reviews validées
        if len(self.validated_reviews) > 0:
            validated_df = pd.DataFrame(self.validated_reviews)
            positive_path = os.path.join(output_dir, f"{base_name}_positive.csv")
            validated_df.to_csv(positive_path, index=False)
        
        # Sauvegarder les reviews rejetées
        if len(self.rejected_reviews) > 0:
            rejected_df = pd.DataFrame(self.rejected_reviews)
            negative_path = os.path.join(output_dir, f"{base_name}_negative.csv")
            rejected_df.to_csv(negative_path, index=False)
    
    def load_csv(self):
        # Effacer la session en cours si on charge un nouveau fichier
        if self.df is not None:
            response = messagebox.askyesno(
                "Charger un nouveau fichier",
                "Charger un nouveau fichier effacera la session en cours.\n"
                "Voulez-vous continuer?"
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
            
            if 'review' not in self.df.columns:
                messagebox.showerror("Erreur", 
                    "Le fichier ne contient pas de colonne 'review'")
                return
            
            # Valider le pourcentage
            try:
                percentage = float(self.percentage_var.get())
                if percentage <= 0 or percentage > 100:
                    raise ValueError()
            except ValueError:
                messagebox.showerror("Erreur", 
                    "Le pourcentage doit être un nombre entre 0 et 100")
                return
            
            # Calculer le nombre d'échantillons
            sample_size = max(1, int(len(self.df) * percentage / 100))
            
            # Sélectionner les indices selon le mode
            if self.selection_mode.get() == "random":
                self.sample_indices = random.sample(range(len(self.df)), sample_size)
            else:
                # Mode séquentiel
                try:
                    start_idx = int(self.start_index_var.get())
                    if start_idx < 0 or start_idx >= len(self.df):
                        raise ValueError()
                except ValueError:
                    messagebox.showerror("Erreur", 
                        f"L'indice de départ doit être entre 0 et {len(self.df)-1}")
                    return
                
                end_idx = min(start_idx + sample_size, len(self.df))
                self.sample_indices = list(range(start_idx, end_idx))
            
            self.current_index = 0
            self.validated_reviews = []
            self.rejected_reviews = []
            
            # Activer les boutons
            self.validate_btn.config(state=tk.NORMAL)
            self.reject_btn.config(state=tk.NORMAL)
            
            # Afficher la première review
            self.display_current_review()
            
            mode_text = "aléatoire" if self.selection_mode.get() == "random" else "séquentiel"
            messagebox.showinfo("Succès", 
                f"Fichier chargé avec succès!\n{len(self.sample_indices)} reviews à valider "
                f"({percentage}% du total)\nMode: {mode_text}")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur de chargement: {str(e)}")
    
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
        
        # Afficher la review (éditable)
        self.review_text.config(state=tk.NORMAL)
        self.review_text.delete(1.0, tk.END)
        self.review_text.insert(1.0, str(review))
    
    def validate_review(self):
        original_index = self.sample_indices[self.current_index]
        # Récupérer le texte (potentiellement modifié)
        review = self.review_text.get(1.0, tk.END).strip()
        
        self.validated_reviews.append({
            'original_index': original_index,
            'review': review
        })
        
        self.current_index += 1
        # Sauvegarder la session après chaque validation
        self.save_session()
        self.display_current_review()
    
    def reject_review(self):
        original_index = self.sample_indices[self.current_index]
        # Récupérer le texte (potentiellement modifié)
        review = self.review_text.get(1.0, tk.END).strip()
        
        self.rejected_reviews.append({
            'original_index': original_index,
            'review': review
        })
        
        self.current_index += 1
        # Sauvegarder la session après chaque rejet
        self.save_session()
        self.display_current_review()
    
    def finish_validation(self):
        # Créer le dossier de destination s'il n'existe pas
        output_dir = os.path.join("data", "processes", "validation")
        os.makedirs(output_dir, exist_ok=True)
        
        # Récupérer le nom du fichier original sans extension
        base_name = os.path.splitext(os.path.basename(self.input_file_path))[0]
        positive_path = os.path.join(output_dir, f"{base_name}_positive.csv")
        negative_path = os.path.join(output_dir, f"{base_name}_negative.csv")
        
        # Sauvegarder les reviews validées
        if len(self.validated_reviews) > 0:
            validated_df = pd.DataFrame(self.validated_reviews)
            validated_df.to_csv(positive_path, index=False)
        
        # Sauvegarder les reviews rejetées
        if len(self.rejected_reviews) > 0:
            rejected_df = pd.DataFrame(self.rejected_reviews)
            rejected_df.to_csv(negative_path, index=False)
        
        # Supprimer la session terminée
        self.clear_session()
        
        # Message de confirmation
        message = "Validation terminée!\n\n"
        if len(self.validated_reviews) > 0:
            message += f"✓ {len(self.validated_reviews)} reviews validées sauvegardées dans:\n{positive_path}\n\n"
        if len(self.rejected_reviews) > 0:
            message += f"✗ {len(self.rejected_reviews)} reviews rejetées sauvegardées dans:\n{negative_path}"
        
        if len(self.validated_reviews) == 0 and len(self.rejected_reviews) == 0:
            message = "Validation terminée!\nAucune review traitée."
        
        messagebox.showinfo("Terminé", message)
        
        # Désactiver les boutons
        self.validate_btn.config(state=tk.DISABLED)
        self.reject_btn.config(state=tk.DISABLED)
        self.progress_label.config(text="Validation terminée")
        self.review_text.config(state=tk.NORMAL)
        self.review_text.delete(1.0, tk.END)

# Créer et lancer l'application
if __name__ == "__main__":
    root = tk.Tk()
    app = ReviewValidator(root)
    root.mainloop()