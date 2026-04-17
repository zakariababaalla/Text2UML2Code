import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from llm_api_cloud import get_dsl_from_spec, get_code_from_uml, check_dsl_structure
from uml_drawer import UMLDiagramApp
from PIL import Image, ImageTk
import io
import json
import re
import tempfile

class PipelineGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Smart UML Studio")
        self.geometry("1250x850")
        self.configure(bg="#f8f9fa")

        # --- Bande image sous le titre ---
        banner_image = Image.open("logo3.jpg")
        banner_image = banner_image.resize((1267, 80))  # largeur = taille fenêtre
        self.banner_photo = ImageTk.PhotoImage(banner_image)
        tk.Label(self, image=self.banner_photo, bg="#f8f9fa", borderwidth=0, highlightthickness=0).pack(fill="x", padx=0, pady=(0, 0))
        
        self.create_spec_and_dsl_area()
        self.create_uml_canvas()
        self.create_code_and_logs()

        self.uml_app = UMLDiagramApp(self.uml_canvas)
        

    # ----------------------------
    # Zone combinée : Spécifications + DSL
    # ----------------------------
    def create_spec_and_dsl_area(self):
        container = tk.Frame(self)
        container.pack(fill="x", pady=(0, 0))

        # === Zone Spécifications ===
        spec_frame = ttk.Frame(container)
        spec_frame.pack(side="left", fill="both", padx=(5, 0))

        # En-tête avec label et boutons
        spec_header = tk.Frame(spec_frame)
        spec_header.pack(fill="x", pady=(0, 0))
        tk.Label(spec_header, text="📝", font=("Arial", 16, "bold"), fg="#505151").pack(side="left", padx=5)
        tk.Label(spec_header, text="Requirements", font=("Broadway", 12, "bold"), fg="#505151").pack(side="left", padx=0)

        # --- Zone de choix du modèle (placée entre Generate et Clear) ---
        self.model_var = tk.StringVar(value="Select a model")
        model_list = ["phi3:mini", "llama3:8b", "deepseek-coder:6.7b","mistral:7b","gemma:2b","codellama:7b","neural-chat:7b"]

        # Boutons à droite
        tk.Button(spec_header, text="Clear all", command=self.clear_all,  width=8, height=1, font=("Arial", 9, "bold"), bg="steelblue", fg="white", activebackground="tomato", activeforeground="white").pack(side="right", padx=(2, 20))

        # Combobox avec label "Model:"
        model_frame = tk.Frame(spec_header, bg="white")
        model_frame.pack(side="right", padx=(2,2))
        model_selector = ttk.Combobox(model_frame, textvariable=self.model_var, values=model_list, state="readonly", width=20)
        model_selector.pack(side="left")

        tk.Button(spec_header, text="Generate DSL from", command=self.generate_dsl,  width=16, height=1, font=("Arial", 9, "bold"), bg="steelblue", fg="white", activebackground="tomato", activeforeground="white").pack(side="right", padx=2)
        tk.Button(spec_header, text="Load file", command=self.load_spec_file, width=8, height=1, font=("Arial", 9, "bold"), bg="steelblue", fg="white", activebackground="tomato", activeforeground="white").pack(side="right", padx=2)
        # Zone de texte avec hauteur contrôlée
        spec_container = tk.Frame(spec_frame)
        spec_container.pack(fill="both", expand=False)
        spec_scroll = tk.Scrollbar(spec_container, orient="vertical")
        self.spec_text = tk.Text(spec_container, wrap="word", height=6, width=85, font=("times new roman", 11), bg="#ffffff", yscrollcommand=spec_scroll.set, padx=10, pady=4)
        self.spec_text.pack(side="left", fill="both", expand=True)
        spec_scroll.pack(side="right", fill="y")
        spec_scroll.config(command=self.spec_text.yview)

        # === Zone DSL ===
        dsl_frame = ttk.Frame(container)
        dsl_frame.pack(side="left", fill="both", padx=(0, 2))

        dsl_header = tk.Frame(dsl_frame)
        dsl_header.pack(fill="x", pady=(0, 0))
        tk.Label(dsl_header, text="Structured DSL", font=("Broadway", 12, "bold"), fg="#505151").pack(side="left", padx=0)
        tk.Button(dsl_header, text="Save UML diagram", command=self.save_uml_as_png, width=15, height=1, font=("Arial", 9, "bold"), bg="steelblue", fg="white", activebackground="tomato", activeforeground="white").pack(side="right", padx=(2, 20))

        tk.Button(dsl_header, text="Generate UML diagram", command=self.generate_uml, width=19, height=1, font=("Arial", 9, "bold"), bg="steelblue", fg="white", activebackground="tomato", activeforeground="white").pack(side="right", padx=(2, 2))
        tk.Button(dsl_header, text="Save DSL", command=self.save_dsl_to_file, width=8, height=1, font=("Arial", 9, "bold"), bg="steelblue", fg="white", activebackground="tomato", activeforeground="white").pack(side="right", padx=(2, 2))

        tk.Button(dsl_header, text="Load DSL", command=self.load_dsl_from_file, width=8, height=1, font=("Arial", 9, "bold"), bg="steelblue", fg="white", activebackground="tomato", activeforeground="white").pack(side="right", padx=2)

        dsl_container = tk.Frame(dsl_frame)
        dsl_container.pack(fill="both", expand=False)
        dsl_scroll_y = tk.Scrollbar(dsl_container, orient="vertical")
        self.dsl_text = tk.Text(dsl_container, wrap="none", height=6, width=87, font=("Arial", 11), bg="#ffffff", yscrollcommand=dsl_scroll_y.set, padx=10, pady=4)
        self.dsl_text.grid(row=0, column=0, sticky="nsew")
        dsl_scroll_y.grid(row=0, column=1, sticky="ns")
        dsl_container.grid_rowconfigure(0, weight=1)
        dsl_container.grid_columnconfigure(0, weight=1)

    # ----------------------------
    # Zone UML
    # ----------------------------
    def create_uml_canvas(self):
        frame = ttk.LabelFrame(self, padding=0)
        frame.pack(fill="both", expand=False, padx=5, pady=(0, 0))
        
        # === Bouton placé AU-DESSUS du diagramme UML ===
        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill="x", pady=(0, 0))  # marge en haut et en bas
        #tk.Label(btn_frame, text="Generated UML diagram", font=("Broadway", 12, "bold"), fg="#505151").pack(side="left", padx=0)
        #tk.Button(btn_frame, text="Save UML class diagram", command=self.save_uml_as_png, width=20, height=1, font=("Arial", 9, "bold"), bg="dim gray", fg="white", activebackground="tomato", activeforeground="white").pack(side="right", padx=(2, 20))

        # === Zone du diagramme UML ===
        container = tk.Frame(frame, height=800)
        container.pack(fill="both", expand=True)
        y_scroll = tk.Scrollbar(container, orient="vertical")

        self.uml_canvas = tk.Canvas(container, bg="white", highlightthickness=0, scrollregion=(0, 0, 2000, 1200), yscrollcommand=y_scroll.set)
        self.uml_canvas.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        y_scroll.config(command=self.uml_canvas.yview)


    # ----------------------------
    # Zone Code + Logs
    # ----------------------------
    def create_code_and_logs(self):
        # === Zone Code généré ===
        code_frame = ttk.Frame(self)
        code_frame.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=(0, 5))

        # En-tête avec label et boutons
        code_header = tk.Frame(code_frame)
        code_header.pack(fill="x", pady=(0, 0))
        tk.Label(code_header, text="Generated code", font=("Broadway", 12, "bold"), fg="#505151").pack(side="left", padx=0)

        tk.Button(code_header, text="Save code", command=self.save_code_to_file, width=10, height=1, font=("Arial", 9, "bold"), bg="steelblue", fg="white", activebackground="tomato", activeforeground="white").pack(side="right", padx=(2, 20))
        self.language_var = tk.StringVar(value="Select programming language")
        lang_menu = ttk.Combobox(code_header, textvariable=self.language_var, values=["Python", "Java", "C#"], width=28, state="readonly")
        lang_menu.pack(side="right", padx=(2, 2))
        tk.Button(code_header, text="Generate code", command=self.generate_code, width=12, height=1, font=("Arial", 9, "bold"), bg="steelblue", fg="white", activebackground="tomato", activeforeground="white").pack(side="right", padx=2)
        
        # Zone de texte
        code_container = tk.Frame(code_frame)
        code_container.pack(fill="both", expand=True)
        code_scroll = tk.Scrollbar(code_container, orient="vertical")
        self.code_text = tk.Text(code_container, wrap="word", height=6, width=68, font=("Consolas", 11),fg="#0028DC", bg="#ffffff", yscrollcommand=code_scroll.set, padx=10, pady=4)
        self.code_text.pack(side="left", fill="both", expand=True)
        code_scroll.pack(side="right", fill="y")
        code_scroll.config(command=self.code_text.yview)

        # === Zone Journal d’exécution ===
        log_frame = ttk.Frame(self,  width=605)
        log_frame.pack(side="left", fill="both", expand=True, padx=(0, 2), pady=(0, 5))
        log_frame.pack_propagate(False)

        log_header = tk.Frame(log_frame)
        log_header.pack(fill="x", pady=(0, 0))
        tk.Label(log_header, text="Execution Log", font=("Broadway", 12, "bold"), fg="#505151").pack(side="left", padx=0)
        tk.Button(log_header, text="Save report", command=self.save_logs, width=10, height=1, font=("Arial", 9, "bold"), bg="steelblue", fg="white", activebackground="tomato", activeforeground="white").pack(side="right", padx=(2, 20))

        # Zone texte + scroll
        log_container = tk.Frame(log_frame)
        log_container.pack(fill="both", expand=True)
        log_scroll = tk.Scrollbar(log_container, orient="vertical")
        self.log_box = tk.Text(log_container, wrap="word", height=6, font=("Consolas", 10), bg="#f1f3f4", yscrollcommand=log_scroll.set, state="disabled", padx=10, pady=4)
        self.log_box.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")
        log_scroll.config(command=self.log_box.yview)

    # =====================================================
    # Fonctions utilitaires
    # =====================================================
    def load_spec_file(self):
        """Load a .txt file into the specification area and clear all other areas automatically."""
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if not file_path:
            return

        try:
            # Clear all areas before loading the new file
            self.spec_text.delete("1.0", tk.END)
            self.dsl_text.delete("1.0", tk.END)
            self.uml_canvas.delete("all")
            self.code_text.delete("1.0", tk.END)
            self.log_box.config(state="normal")
            self.log_box.delete("1.0", tk.END)
            self.log_box.config(state="disabled")

            # Load the selected file
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
                self.spec_text.insert("1.0", content)
            self.log(f"📂 Specifications loaded from: {file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load the file:\n{e}")
            self.log(f"❌ Error loading file: {e}")

            
    def clear_all(self):
        """Clear all areas (specifications, DSL, UML, code, logs) with confirmation and safety checks."""
        # Check if all areas are already empty
        if (
            not self.spec_text.get("1.0", tk.END).strip()
            and not self.dsl_text.get("1.0", tk.END).strip()
            and not self.code_text.get("1.0", tk.END).strip()
            and not self.uml_canvas.find_all()
            and not self.log_box.get("1.0", tk.END).strip()
        ):
            messagebox.showinfo(
                "Nothing to clear",
                "All areas are already empty. There is nothing to clear."
            )
            self.log("ℹ️ Nothing to clear — all areas are empty.")
            return

        # Ask for confirmation
        confirm = messagebox.askyesno(
            "Confirm deletion",
            "Are you sure you want to clear all areas?\n\n"
            "This action cannot be undone."
        )

        if not confirm:
            self.log("❎ Clear action cancelled by user.")
            return

        # Clear all text and graphic zones
        self.spec_text.delete("1.0", tk.END)
        self.dsl_text.delete("1.0", tk.END)
        self.uml_canvas.delete("all")
        self.code_text.delete("1.0", tk.END)

        # Clear the log box entirely
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", tk.END)
        self.log_box.config(state="disabled")

        # (Optional) Keep or remove the final log
        # self.log("🧹 All areas have been cleared.") 

    

    def save_uml_as_png(self):
        """Sauvegarde le diagramme UML complet (y compris hors écran) en image PNG avec taille correcte."""

        items = self.uml_canvas.find_all()
        if not items:
            messagebox.showwarning("Warning", "The UML canvas is empty. Nothing to save.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            # Récupérer les limites du diagramme (tout le contenu, pas seulement visible)
            scroll_region = self.uml_canvas.bbox("all")
            if not scroll_region:
                messagebox.showwarning("Warning", "No region found to capture.") ,
                return

            x1, y1, x2, y2 = scroll_region
            width = x2 - x1
            height = y2 - y1

            # Générer un fichier PostScript temporaire à taille réelle
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ps") as tmpfile:
                ps_path = tmpfile.name
                self.uml_canvas.postscript(
                    file=ps_path,
                    colormode="color",
                    x=x1,
                    y=y1,
                    width=width,
                    height=height,
                    pagewidth=width - 1,
                    pageheight=height - 1
                )

            # Charger le PostScript et convertir en image réelle
            image = Image.open(ps_path)

            # Forcer la mise à l’échelle correcte (conversion points → pixels)
            dpi = 300  # résolution écran standard
            scale = dpi / 72.0  # car PS utilise 72 dpi
            image = image.resize((int(width * scale), int(height * scale)), Image.LANCZOS)

            image.save(file_path, "PNG")
            messagebox.showinfo("Success", f"UML diagram saved:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Unable to save the diagram: {e}")


    def save_code_to_file(self):
        """Sauvegarde le code généré (Python, Java, C#...) et affiche une confirmation."""
        code = self.code_text.get("1.0", tk.END).strip()
        if not code:
            messagebox.showwarning("Error", "No code to save.")
            return

        # Choix de l’extension selon le type de code sélectionné
        selected_lang = getattr(self, "selected_language", "Python")  # suppose que tu as une variable qui stocke le langage choisi
        extensions = {
            "Python": ".py",
            "Java": ".java",
            "C#": ".cs"
        }
        ext = extensions.get(selected_lang, ".txt")

        filetypes = [
            ("Python file", "*.py"),
            ("Java file", "*.java"),
            ("C# file", "*.cs"),
            ("All files", "*.*")
        ]

        file_path = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=filetypes,
            title=f"Save code {selected_lang}"
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)

            self.log(f"💾 Code saved in: {file_path}")

            # Boîte de confirmation finale
            messagebox.showinfo(
                "Save successful",
                f"The code has been successfully saved in:\n{os.path.basename(file_path)}"
            )

        except Exception as e:
            messagebox.showerror("Error", f"Unable to save code: {e}")
            self.log(f"❌ Code save error: {e}")


    # =====================================================
    # Étapes du pipeline
    # =====================================================
    def generate_dsl(self):
        """Generate DSL from specifications and clear previous outputs (DSL, UML, Code, Logs)."""
        spec_text = self.spec_text.get("1.0", tk.END).strip()
        if not spec_text:
            messagebox.showwarning("Error", "Please enter textual specifications.")
            return

        # Récupération du modèle sélectionné
        selected_model = self.model_var.get().strip() if hasattr(self, "model_var") else ""

        # Vérification : modèle sélectionné ?
        invalid_choices = {"", "select model", "select a model", "choose model", "choose a model"}
        if selected_model.lower() in invalid_choices:
            messagebox.showwarning("Model not selected", "Please select a model before generating the DSL.")
            self.log("⚠️ No model selected. DSL generation canceled.")
            return

        # Nettoyage des zones
        self.dsl_text.delete("1.0", tk.END)
        self.uml_canvas.delete("all")
        self.code_text.delete("1.0", tk.END)
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", tk.END)
        self.log_box.config(state="disabled")

        self.log(f"☁️ Sending text to cloud model ({selected_model})...")

        try:
            # Génération du DSL avec le modèle choisi
            dsl_result = get_dsl_from_spec(spec_text, selected_model)

            # Vérifier la réponse du serveur
            if not dsl_result or not dsl_result.strip():
                error_msg = (
                    "❌ Error: No response received from the cloud model.\n"
                    "Please check your internet connection or try again later."
                )
                self.dsl_text.insert("1.0", error_msg)
                self.dsl_text.tag_add("error", "1.0", "end")
                self.dsl_text.tag_config("error", foreground="steelblue")
                self.log("❌ Cloud model returned an empty or invalid response.")
                return

            # Afficher le résultat si valide
            self.dsl_text.insert("1.0", dsl_result)
            self.highlight_dsl()

            self.log(f"✅ DSL generated successfully using model: {selected_model}")

        except Exception as e:
            error_msg = f"❌ Cloud Error:\n{e}"
            self.dsl_text.insert("1.0", error_msg)
            self.dsl_text.tag_add("error", "1.0", "end")
            self.dsl_text.tag_config("error", foreground="steelblue")
            messagebox.showerror("Cloud Error", str(e))
            self.log(f"❌ Cloud error: {e}")



    def generate_uml(self):
        """Generate UML from either DSL text or JSON-formatted UML entities."""
        import json

        dsl_text = self.dsl_text.get("1.0", tk.END).strip()
        if not dsl_text:
            messagebox.showwarning("Warning", "Please generate or paste a DSL first.")
            return

        self.log("🔎 Checking DSL or JSON structure...", level="info")

        # --- Try to detect if the content is JSON ---
        is_json = False
        parsed_content = None
        try:
            parsed_content = json.loads(dsl_text)
            is_json = isinstance(parsed_content, dict)
        except json.JSONDecodeError:
            is_json = False

        # === CASE 1 : JSON input ===
        if is_json:
            self.log("📘 JSON structure detected — interpreting as UML data.", level="info")

            # Vérifier si le JSON contient directement des entités UML
            if "uml_entities" in parsed_content or "classes" in parsed_content:
                uml_data = parsed_content
                self.uml_app.uml_data = uml_data
                self.uml_app.draw_uml_diagram()
                self.log("✅ UML diagram successfully generated from JSON entities.", level="success")

            # Vérifier si c’est un DSL encodé dans un JSON
            elif "content" in parsed_content:
                dsl_content = parsed_content["content"]
                self.log("🧾 DSL content extracted from JSON — parsing as DSL.", level="info")

                # --- DSL Validation ---
                issues = check_dsl_structure(dsl_content)
                if issues:
                    for issue in issues:
                        issue_lower = issue.lower()
                        if any(word in issue_lower for word in ["error", "invalid", "missing"]):
                            self.log(issue, level="error")
                        elif any(word in issue_lower for word in ["warning", "inconsistency", "attention"]):
                            self.log(issue, level="warning")
                        else:
                            self.log(issue, level="info")
                else:
                    self.log("✅ No structural issues detected in the DSL.", level="success")

                # --- DSL → UML Transformation ---
                self.log("⚙️ Transforming DSL into UML model...", level="info")
                uml_data = self.uml_app.dsl_to_uml_data(dsl_content)
                self.uml_app.uml_data = uml_data
                self.uml_app.draw_uml_diagram()
                self.log("✅ UML diagram successfully generated from DSL (JSON).", level="success")

            else:
                messagebox.showwarning("Unsupported JSON", "This JSON format does not contain recognizable UML or DSL data.")
                self.log("⚠️ Unsupported JSON structure.", level="warning")
                return

        # === CASE 2 : Plain DSL input ===
        else:
            self.log("📄 Plain DSL structure detected — parsing as text.", level="info")

            # --- DSL Validation ---
            issues = check_dsl_structure(dsl_text)
            if issues:
                for issue in issues:
                    issue_lower = issue.lower()
                    if any(word in issue_lower for word in ["error", "invalid", "missing"]):
                        self.log(issue, level="error")
                    elif any(word in issue_lower for word in ["warning", "inconsistency", "attention"]):
                        self.log(issue, level="warning")
                    else:
                        self.log(issue, level="info")
            else:
                self.log("✅ No structural issues detected in the DSL.", level="success")

            # --- DSL → UML Transformation ---
            self.log("⚙️ Transforming DSL into UML model...", level="info")
            uml_data = self.uml_app.dsl_to_uml_data(dsl_text)
            self.uml_app.uml_data = uml_data
            self.uml_app.draw_uml_diagram()
            self.log("✅ UML diagram successfully generated from DSL.", level="success")


    def generate_code(self): 
        """Generate source code from the UML model using the selected cloud model."""
        self.log("☁️ Sending UML model (PIM) to cloud model for code generation...")

        try:
            # Vérifier la présence du modèle UML
            if (
                not hasattr(self.uml_app, "uml_data") 
                or not self.uml_app.uml_data
                or not self.uml_app.uml_data.get("classes")  # aucune classe détectée
                or self.uml_canvas.find_all() == ()          # canvas vide
            ):
                messagebox.showwarning(
                    "Error", 
                    "The UML diagram is empty.\nPlease generate or load a UML model before generating code."
                )
                self.log("⚠️ UML area is empty. Code generation canceled.")
                return

            # Récupérer le langage choisi
            lang = self.language_var.get().strip()
            if lang in ("", "Select programming language"):
                messagebox.showwarning("Missing language", "Please select a programming language before generating code.")
                self.log("⚠️ No language selected. Code generation canceled.")
                return

            # Récupérer le modèle cloud choisi
            selected_model = self.model_var.get().strip()
            invalid_models = {"", "select model", "select a model", "choose model", "choose a model"}
            if selected_model.lower() in invalid_models:
                messagebox.showwarning("Missing model", "Please select a cloud model before generating code.")
                self.log("⚠️ No model selected. Code generation canceled.")
                return

            # Conversion UML → DSL
            uml_dsl = self.uml_app.uml_data_to_dsl()

            # Appel au modèle cloud
            code = get_code_from_uml(uml_dsl, language=lang, model_name=selected_model)

            # Nettoyage avant affichage
            self.code_text.delete("1.0", tk.END)

            # --- Vérification du résultat ---
            if not code or not code.strip():
                error_msg = (
                    f"❌ Error: No response received from the cloud model ({selected_model}).\n"
                    "Please check your connection or try again later."
                )
                self.code_text.insert("1.0", error_msg)
                self.code_text.tag_add("error", "1.0", "end")
                self.code_text.tag_config("error", foreground="steelblue")
                self.log("❌ Cloud model returned an empty or invalid code response.")
                messagebox.showerror("Cloud Error", "No response received from the model.")
                return

            # Si le code contient explicitement une erreur détectée
            if "error" in code.lower() or "exception" in code.lower():
                self.code_text.insert("1.0", code)
                self.code_text.tag_add("error", "1.0", "end")
                self.code_text.tag_config("error", foreground="steelblue")
                self.log("❌ The model returned an error message during code generation.")
                return

            # Sinon, affichage du code généré et coloration syntaxique
            self.code_text.insert("1.0", code)
            self.highlight_code(lang)
            self.log(f"✅ {lang} code successfully generated using model: {selected_model}.")

        except Exception as e:
            # Gestion globale des erreurs
            error_msg = f"❌ Code generation error: {e}"
            self.code_text.delete("1.0", tk.END)
            self.code_text.insert("1.0", error_msg)
            self.code_text.tag_add("error", "1.0", "end")
            self.code_text.tag_config("error", foreground="steelblue")
            self.log(error_msg)
            messagebox.showerror("Code generation error", str(e))


    def save_dsl_to_file(self):
        """Save the current DSL either as .txt or .json with proper JSON structure."""
        import json
        dsl_text = self.dsl_text.get("1.0", tk.END).strip()
        if not dsl_text:
            messagebox.showwarning("Warning", "No DSL content to save.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Text file", "*.txt"),
                ("JSON file", "*.json")
            ]
        )
        if not file_path:
            return

        try:
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()

            # === Case 1: Save as plain text ===
            if ext == ".txt":
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(dsl_text)
                self.log(f"✅ DSL saved as text: {file_path}")
                messagebox.showinfo(
                    "Save successful",
                    f"The DSL has been successfully saved as a text file:\n\n{os.path.basename(file_path)}"
                )

            # === Case 2: Save as structured JSON ===
            elif ext == ".json":
                # Créer une structure JSON valide
                dsl_json = {
                    "file_type": "dsl",
                    "version": "1.0",
                    "content": dsl_text
                }

                # Vérifier que le JSON est bien sérialisable
                json_str = json.dumps(dsl_json, ensure_ascii=False, indent=4)

                with open(file_path, "w", encoding="utf-8") as fjson:
                    fjson.write(json_str)

                self.log(f"✅ DSL saved as JSON: {file_path}")
                messagebox.showinfo(
                    "Save successful",
                    f"The DSL has been successfully saved as a valid JSON file:\n\n{os.path.basename(file_path)}"
                )

            else:
                messagebox.showwarning(
                    "Unsupported format",
                    "Please choose either .txt or .json format only."
                )

        except Exception as e:
            messagebox.showerror("Error", f"Unable to save the DSL:\n{e}")
            self.log(f"❌ DSL save error: {e}")


    def load_dsl_from_file(self):
        """Load a DSL from a .txt or .json file and clear other areas first."""
        file_path = filedialog.askopenfilename(
            filetypes=[("Text file", "*.txt"), ("JSON file", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return

        # Clear other areas BEFORE loading DSL
        self.spec_text.delete("1.0", tk.END)
        self.uml_canvas.delete("all")
        self.code_text.delete("1.0", tk.END)
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", tk.END)
        self.log_box.config(state="disabled")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # If it's a JSON file, extract the DSL text if possible
            if file_path.endswith(".json"):
                import json
                data = json.loads(content)
                if isinstance(data, dict):
                    if "dsl" in data:
                        content = data["dsl"]
                    elif "dsl_content" in data:  # compatibilité avec ton format précédent
                        content = data["dsl_content"]

            # Insert DSL into the DSL text zone
            self.dsl_text.delete("1.0", tk.END)
            self.dsl_text.insert("1.0", content)
            self.log(f"📂 DSL loaded from: {file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Unable to load DSL: {e}")
            self.log(f"❌ DSL loading error: {e}")


    def log(self, msg, level="info"):
        """
        Display a log message in the execution panel with color styling
        depending on the message level.
        Levels: info (default), success, warning, error
        """
        # Enable editing temporarily
        self.log_box.config(state="normal")

        # Define colors for each log level
        colors = {
            "info": "#0078D7",      # blue
            "success": "#0A9B00",   # green
            "warning": "#E6A100",   # orange
            "error": "#FF6347"      # Tomate
        }

        color = colors.get(level, "#333333")

        # Create tags dynamically if not already present
        if level not in self.log_box.tag_names():
            self.log_box.tag_configure(level, foreground=color, font=("Consolas", 10, "normal"))

        # Insert the message
        self.log_box.insert(tk.END, msg + "\n", level)
        self.log_box.see(tk.END)

        # Make the box read-only again
        self.log_box.config(state="disabled")

    def save_logs(self):
        """Save only DSL anomaly or correction messages from the execution log."""
        try:
            # Récupération du contenu complet du log
            logs = self.log_box.get("1.0", tk.END).strip()
            if not logs:
                messagebox.showinfo("Information", "The log is empty. Nothing to save.")
                return

            # Filtrage : on garde uniquement les messages importants (warnings, errors, corrections)
            filtered_lines = []
            for line in logs.splitlines():
                if any(keyword in line.lower() for keyword in [
                    "error", "invalid", "warning", "fix", "adjust", "line", "missing", "remove", "correct"
                ]):
                    filtered_lines.append(line)

            # Si aucun message d’anomalie n’est trouvé
            if not filtered_lines:
                messagebox.showinfo("No anomalies", "No anomalies or correction hints detected in the log.")
                return

            # Boîte de dialogue pour choisir l’emplacement
            file_path = tk.filedialog.asksaveasfilename(
                title="Save anomaly report",
                defaultextension=".txt",
                filetypes=[("Text file", "*.txt"), ("All files", "*.*")]
            )
            if not file_path:
                return

            # Écriture dans le fichier
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("=" * 120 + "\n")
                f.write("DSL Correction Report\n")
                f.write("=" * 120 + "\n\n")
                for line in filtered_lines:
                    f.write(line.strip() + "\n")

            self.log(f"📝 DSL correction report saved: {file_path}", level="success")
            messagebox.showinfo("Success", f"DSL correction report saved in:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Unable to save DSL correction report: {e}")
            self.log(f"❌ Error while saving DSL correction report: {e}", level="error")


    def highlight_dsl(self):
        """Coloration syntaxique simple pour le DSL UML affiché."""
        text_widget = self.dsl_text

        # 1️--Nettoyage des anciens tags
        for tag in text_widget.tag_names():
            text_widget.tag_delete(tag)

        # 2--Définir les styles de coloration
        colors = {
            "keyword": "#0077cc",   # Bleu pour Class, Relation
            "section": "#cc5500",   # Orange pour Attributes / Methods
            #"attribute": "#444444", # Gris foncé pour les noms d’attributs
            #"method": "#008000",    # Vert pour les méthodes
            "relation_type": "#8b008b", # Violet pour les relations

        }

        # Création des tags
        for tag, color in colors.items():
            text_widget.tag_config(tag, foreground=color, font=("Arial", 11, "normal" if tag in ["keyword", "section"] else "normal"))

        # 3️--Récupérer le texte complet
        dsl_text = text_widget.get("1.0", "end-1c")

        # 4️--Coloration par expressions régulières

        # Mots-clés principaux
        for match in re.finditer(r"\b(Class|Relation)\b", dsl_text):
            text_widget.tag_add("keyword", f"1.0+{match.start()}c", f"1.0+{match.end()}c")

        # Sections Attributes / Methods
        for match in re.finditer(r"\b(Attributes|Methods)\b", dsl_text):
            text_widget.tag_add("section", f"1.0+{match.start()}c", f"1.0+{match.end()}c")

        # Attributs après "Attributes:"
        for match in re.finditer(r"Attributes:\s*(.*)", dsl_text):
            start = match.start(1)
            end = match.end(1)
            text_widget.tag_add("attribute", f"1.0+{start}c", f"1.0+{end}c")

        # Méthodes après "Methods:"
        for match in re.finditer(r"Methods:\s*(.*)", dsl_text):
            start = match.start(1)
            end = match.end(1)
            text_widget.tag_add("method", f"1.0+{start}c", f"1.0+{end}c")

        # Types de relation : composition, aggregation, association
        for match in re.finditer(r"\b(composition|aggregation|association|inheritance|dependency|realization|implements|operation|use|association_class)\b", dsl_text, flags=re.IGNORECASE):
            text_widget.tag_add("relation_type", f"1.0+{match.start()}c", f"1.0+{match.end()}c")


    # --------------------------------------------
    # Coloration syntaxique multi-langage
    # --------------------------------------------
    def highlight_code(self, lang: str):
        """Applique une coloration syntaxique simple selon le langage choisi."""

        # 1️--Nettoyer les tags existants
        for tag in self.code_text.tag_names():
            self.code_text.tag_delete(tag)

        # 2️--Définir les couleurs selon le langage
        colors = {
            "keyword": "#0077cc",   # Bleu pour mots-clés
            "string": "#008000",    # Vert pour chaînes
            "comment": "#999999",   # Gris pour commentaires
            "class": "#8b008b",     # Violet pour 'class'
            "func": "#cc5500"       # Orange pour 'def' ou 'void'
        }

        # Créer les tags de couleur
        for tag, color in colors.items():
            self.code_text.tag_config(tag, foreground=color)

        # 3️--Récupérer le texte
        code = self.code_text.get("1.0", "end-1c")

        # 4️--Définir les règles par langage
        if lang.lower() == "python":
            keywords = r"\b(False|class|finally|is|return|None|continue|for|lambda|try|True|def|from|nonlocal|while|and|del|global|not|with|as|elif|if|or|yield|assert|else|import|pass|break|except|in|raise)\b"
            comment = r"#.*"
            string = r"(\".*?\"|\'.*?\')"

        elif lang.lower() == "java":
            keywords = r"\b(abstract|assert|boolean|break|byte|case|catch|char|class|continue|default|do|double|else|enum|extends|final|finally|float|for|if|implements|import|instanceof|int|interface|long|native|new|null|package|private|protected|public|return|short|static|strictfp|super|switch|synchronized|this|throw|throws|transient|try|void|volatile|while)\b"
            comment = r"//.*|/\*[\s\S]*?\*/"
            string = r"(\".*?\"|\'.*?\')"

        elif lang.lower() in ["c#", "csharp"]:
            keywords = r"\b(abstract|as|base|bool|break|byte|case|catch|char|checked|class|const|continue|decimal|default|delegate|do|double|else|enum|event|explicit|extern|false|finally|fixed|float|for|foreach|goto|if|implicit|in|int|interface|internal|is|lock|long|namespace|new|null|object|operator|out|override|params|private|protected|public|readonly|ref|return|sbyte|sealed|short|sizeof|stackalloc|static|string|struct|switch|this|throw|true|try|typeof|uint|ulong|unchecked|unsafe|ushort|using|virtual|void|volatile|while)\b"
            comment = r"//.*|/\*[\s\S]*?\*/"
            string = r"(\".*?\"|\'.*?\')"
        else:
            return  # Aucun langage connu → pas de coloration

        # 5️--Appliquer la coloration avec regex
        for match in re.finditer(keywords, code):
            self.code_text.tag_add("keyword", f"1.0+{match.start()}c", f"1.0+{match.end()}c")

        for match in re.finditer(comment, code):
            self.code_text.tag_add("comment", f"1.0+{match.start()}c", f"1.0+{match.end()}c")

        for match in re.finditer(string, code):
            self.code_text.tag_add("string", f"1.0+{match.start()}c", f"1.0+{match.end()}c")

        # Classes et fonctions (bonus)
        for match in re.finditer(r"\bclass\b", code):
            self.code_text.tag_add("class", f"1.0+{match.start()}c", f"1.0+{match.end()}c")

        for match in re.finditer(r"\b(def|void|function)\b", code):
            self.code_text.tag_add("func", f"1.0+{match.start()}c", f"1.0+{match.end()}c")




if __name__ == "__main__":
    import sys, os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))  # 🔹 assure que les modules locaux sont visibles
    
    try:
        app = PipelineGUI()
        app.mainloop()
    except Exception as e:
        print(f"❌ Error when launching the application: {e}")
