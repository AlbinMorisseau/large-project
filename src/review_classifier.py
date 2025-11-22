import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json

class ReviewChunkLabeler:
    def __init__(self, root):
        self.root = root
        self.root.title("Reviews Multi-Label Classifier (Chunks)")
        self.root.geometry("900x750")
        
        self.df = None
        self.current_review_index = 0
        self.current_chunk_index = 0
        self.current_chunks = []
        self.labeled_chunks = []
        self.input_file_path = None
        self.output_path = None
        self.max_length = 128
        
        # État des checkboxes pour le chunk courant
        self.handicap_var = tk.IntVar(value=0)
        self.pet_var = tk.IntVar(value=0)
        self.child_var = tk.IntVar(value=0)
        
        self.setup_ui()
        self.check_existing_session()
    
    def split_review_chunks(self, review_text, max_length=128):
        """Divise une review en chunks de max_length tokens"""
        words = str(review_text).split()
        chunks = []
        current_chunk = []
        
        for word in words:
            current_chunk.append(word)
            if len(' '.join(current_chunk).split()) >= max_length - 20:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks if chunks else [review_text]
    
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
        
        # Chunk info label
        self.chunk_info_label = ttk.Label(main_frame, text="", font=("Arial", 9, "italic"))
        self.chunk_info_label.grid(row=2, column=0, columnspan=2, pady=2)
        
        # Text zone for chunk display
        self.text_frame = ttk.LabelFrame(main_frame, text="Chunk de la Review", padding="10")
        self.text_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        
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
        category_frame.grid(row=4, column=0, columnspan=2, pady=15, sticky=(tk.W, tk.E))
        
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
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        # Previous button
        self.prev_btn = ttk.Button(button_frame, text="⬅ Précédent", 
                                    command=self.previous_chunk, 
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
        main_frame.rowconfigure(3, weight=1)
        self.text_frame.columnconfigure(0, weight=1)
        self.text_frame.rowconfigure(0, weight=1)
        
        # Closing event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def check_existing_session(self):
        """Vérifier s'il existe une session en cours"""
        session_file = "review_chunk_labeler_session.json"
        if os.path.exists(session_file):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                if os.path.exists(session_data['input_file_path']):
                    total_chunks = sum(session_data['chunks_per_review'])
                    current_total = sum(session_data['chunks_per_review'][:session_data['current_review_index']]) + session_data['current_chunk_index']
                    
                    response = messagebox.askyesno(
                        "Session trouvée",
                        f"Une session a été trouvée pour:\n{session_data['input_file_path']}\n\n"
                        f"Progression: {current_total}/{total_chunks} chunks\n"
                        f"Review {session_data['current_review_index'] + 1}/{session_data['total_reviews']}\n\n"
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
            self.current_review_index = session_data['current_review_index']
            self.current_chunk_index = session_data['current_chunk_index']
            self.labeled_chunks = session_data['labeled_chunks']
            self.max_length = session_data.get('max_length', 128)
            
            # Activer les contrôles
            self.handicap_check.config(state=tk.NORMAL)
            self.pet_check.config(state=tk.NORMAL)
            self.child_check.config(state=tk.NORMAL)
            self.next_btn.config(state=tk.NORMAL)
            
            # Générer les chunks pour la review courante
            current_review = self.df.loc[self.current_review_index, 'review']
            self.current_chunks = self.split_review_chunks(current_review, self.max_length)
            
            # Afficher le chunk courant
            self.display_current_chunk()
            
            total_chunks = sum(session_data['chunks_per_review'])
            current_total = sum(session_data['chunks_per_review'][:self.current_review_index]) + self.current_chunk_index
            
            messagebox.showinfo("Session rechargée", 
                f"Session rechargée avec succès !\n"
                f"Reprise au chunk {current_total + 1}/{total_chunks}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du rechargement: {str(e)}")
    
    def generate_output_path(self):
        """Générer le chemin de sortie pour les chunks labellisés"""
        if self.input_file_path is None:
            return None
        
        # Créer le dossier de destination
        output_dir = os.path.join("..", "data", "processed", "validation")
        os.makedirs(output_dir, exist_ok=True)
        
        # Obtenir le nom du fichier original
        base_name = os.path.splitext(os.path.basename(self.input_file_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}_chunks_labeled.csv")
        
        return output_path
    
    def save_labeled_data(self):
        """Sauvegarder les chunks labellisés jusqu'à présent"""
        if not self.labeled_chunks:
            return
        
        if self.output_path is None:
            self.output_path = self.generate_output_path()
        
        try:
            # Créer le DataFrame avec les chunks labellisés
            chunks_data = []
            for chunk_info in self.labeled_chunks:
                chunks_data.append({
                    'chunk_text': chunk_info['chunk_text'],
                    'handicap': chunk_info['handicap'],
                    'pet': chunk_info['pet'],
                    'child': chunk_info['child']
                })
            
            result_df = pd.DataFrame(chunks_data)
            
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
        
        # Calculer le nombre de chunks par review
        chunks_per_review = []
        for idx in range(len(self.df)):
            review = self.df.loc[idx, 'review']
            chunks = self.split_review_chunks(review, self.max_length)
            chunks_per_review.append(len(chunks))
        
        session_data = {
            'input_file_path': self.input_file_path,
            'output_path': self.output_path,
            'current_review_index': self.current_review_index,
            'current_chunk_index': self.current_chunk_index,
            'total_reviews': len(self.df),
            'max_length': self.max_length,
            'chunks_per_review': chunks_per_review,
            'labeled_chunks': self.labeled_chunks
        }
        
        session_file = "review_chunk_labeler_session.json"
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            # Sauvegarder également les données labellisées
            self.save_labeled_data()
            
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de session: {e}")
    
    def clear_session(self):
        """Supprimer le fichier de session"""
        session_file = "review_chunk_labeler_session.json"
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
            
            self.current_review_index = 0
            self.current_chunk_index = 0
            self.labeled_chunks = []
            
            # Générer les chunks pour la première review
            first_review = self.df.loc[0, 'review']
            self.current_chunks = self.split_review_chunks(first_review, self.max_length)
            
            # Calculer le nombre total de chunks
            total_chunks = 0
            for idx in range(len(self.df)):
                review = self.df.loc[idx, 'review']
                chunks = self.split_review_chunks(review, self.max_length)
                total_chunks += len(chunks)
            
            # Activer les contrôles
            self.handicap_check.config(state=tk.NORMAL)
            self.pet_check.config(state=tk.NORMAL)
            self.child_check.config(state=tk.NORMAL)
            self.next_btn.config(state=tk.NORMAL)
            
            # Afficher le premier chunk
            self.display_current_chunk()
            
            messagebox.showinfo("Succès", 
                f"Fichier chargé avec succès !\n"
                f"{len(self.df)} reviews → {total_chunks} chunks à labelliser\n\n"
                f"Sauvegarde dans:\n{self.output_path}")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur de chargement: {str(e)}")
    
    def display_current_chunk(self):
        """Afficher le chunk courant"""
        if self.current_review_index >= len(self.df):
            self.finish_labeling()
            return
        
        if self.current_chunk_index >= len(self.current_chunks):
            # Passer à la review suivante
            self.current_review_index += 1
            self.current_chunk_index = 0
            
            if self.current_review_index >= len(self.df):
                self.finish_labeling()
                return
            
            # Générer les chunks pour la nouvelle review
            current_review = self.df.loc[self.current_review_index, 'review']
            self.current_chunks = self.split_review_chunks(current_review, self.max_length)
        
        chunk_text = self.current_chunks[self.current_chunk_index]
        
        # Calculer la progression totale
        total_chunks_before = 0
        for idx in range(self.current_review_index):
            review = self.df.loc[idx, 'review']
            chunks = self.split_review_chunks(review, self.max_length)
            total_chunks_before += len(chunks)
        
        current_chunk_global = total_chunks_before + self.current_chunk_index + 1
        
        # Calculer le nombre total de chunks
        total_chunks = 0
        for idx in range(len(self.df)):
            review = self.df.loc[idx, 'review']
            chunks = self.split_review_chunks(review, self.max_length)
            total_chunks += len(chunks)
        
        # Mise à jour des labels de progression
        self.progress_label.config(
            text=f"Chunk {current_chunk_global}/{total_chunks}"
        )
        
        self.chunk_info_label.config(
            text=f"Review {self.current_review_index + 1}/{len(self.df)} - "
                 f"Chunk {self.current_chunk_index + 1}/{len(self.current_chunks)}"
        )
        
        # Afficher le chunk
        self.review_text.config(state=tk.NORMAL)
        self.review_text.delete(1.0, tk.END)
        self.review_text.insert(1.0, chunk_text)
        self.review_text.config(state=tk.DISABLED)
        
        # Charger les labels existants si disponibles
        existing_label = None
        for label in self.labeled_chunks:
            if (label['review_index'] == self.current_review_index and 
                label['chunk_index'] == self.current_chunk_index):
                existing_label = label
                break
        
        if existing_label:
            self.handicap_var.set(existing_label['handicap'])
            self.pet_var.set(existing_label['pet'])
            self.child_var.set(existing_label['child'])
        else:
            # Réinitialiser les checkboxes
            self.handicap_var.set(0)
            self.pet_var.set(0)
            self.child_var.set(0)
        
        # Gérer le bouton précédent
        is_first_chunk = (self.current_review_index == 0 and self.current_chunk_index == 0)
        self.prev_btn.config(state=tk.NORMAL if not is_first_chunk else tk.DISABLED)
    
    def save_and_next(self):
        """Enregistrer les labels et passer au chunk suivant"""
        # Sauvegarder les labels actuels
        chunk_label = {
            'review_index': self.current_review_index,
            'chunk_index': self.current_chunk_index,
            'chunk_text': self.current_chunks[self.current_chunk_index],
            'handicap': self.handicap_var.get(),
            'pet': self.pet_var.get(),
            'child': self.child_var.get()
        }
        
        # Mettre à jour ou ajouter les labels
        existing_idx = None
        for idx, label in enumerate(self.labeled_chunks):
            if (label['review_index'] == self.current_review_index and 
                label['chunk_index'] == self.current_chunk_index):
                existing_idx = idx
                break
        
        if existing_idx is not None:
            self.labeled_chunks[existing_idx] = chunk_label
        else:
            self.labeled_chunks.append(chunk_label)
        
        # Passer au chunk suivant
        self.current_chunk_index += 1
        
        # Sauvegarder la session et les données
        self.save_session()
        
        # Afficher le chunk suivant
        self.display_current_chunk()
    
    def previous_chunk(self):
        """Revenir au chunk précédent"""
        if self.current_chunk_index > 0:
            self.current_chunk_index -= 1
        elif self.current_review_index > 0:
            # Revenir à la review précédente
            self.current_review_index -= 1
            prev_review = self.df.loc[self.current_review_index, 'review']
            self.current_chunks = self.split_review_chunks(prev_review, self.max_length)
            self.current_chunk_index = len(self.current_chunks) - 1
        
        self.display_current_chunk()
    
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
            f"Total: {len(self.labeled_chunks)} chunks labellisés")
        
        # Désactiver les contrôles
        self.handicap_check.config(state=tk.DISABLED)
        self.pet_check.config(state=tk.DISABLED)
        self.child_check.config(state=tk.DISABLED)
        self.next_btn.config(state=tk.DISABLED)
        self.prev_btn.config(state=tk.DISABLED)
        self.progress_label.config(text="Labellisation terminée")
        self.chunk_info_label.config(text="")
        self.review_text.config(state=tk.NORMAL)
        self.review_text.delete(1.0, tk.END)
        self.review_text.config(state=tk.DISABLED)
    
    def on_closing(self):
        """Gestion de la fermeture de l'application"""
        if self.df is not None:
            # Vérifier s'il reste des chunks à labelliser
            total_chunks = 0
            for idx in range(len(self.df)):
                review = self.df.loc[idx, 'review']
                chunks = self.split_review_chunks(review, self.max_length)
                total_chunks += len(chunks)
            
            if len(self.labeled_chunks) < total_chunks:
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
    app = ReviewChunkLabeler(root)
    root.mainloop()