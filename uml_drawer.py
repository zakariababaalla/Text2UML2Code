import tkinter as tk
import re
import math
from tkinter import messagebox

class UMLDiagramApp:
    def __init__(self, canvas):
        self.canvas = canvas
        self.uml_data = {}
        self.class_positions = {}

    # --------------------------------------------
    # 🧩 Étape 1 : Transformation DSL → Structure UML
    # --------------------------------------------
    def dsl_to_uml_data(self, dsl_text: str):
        uml_data = {"classes": [], "relations": []}
        current_class = None

        lines = [line.strip() for line in dsl_text.split("\n") if line.strip()]

        for line in lines:
            lower_line = line.lower()

            # --- Détection robuste des classes ---
            if lower_line.startswith("class"):
                parts = line.split(" ", 1)
                if len(parts) > 1:
                    class_name = parts[1].replace(":", "").strip()
                    current_class = {"name": class_name, "attributes": [], "methods": []}
                    uml_data["classes"].append(current_class)
                else:
                    continue  # ignorer les lignes mal formatées

            # --- Extraction des attributs ---
            elif lower_line.startswith("attributes") and current_class:
                try:
                    attrs = re.findall(r"[\w_]+", line.split(":", 1)[1])
                    current_class["attributes"].extend(attrs)
                except IndexError:
                    pass  # ignorer si ":" absent

            # --- Extraction des méthodes ---
            elif lower_line.startswith("methods") and current_class:
                try:
                    methods = re.findall(r"[\w_]+", line.split(":", 1)[1])
                    current_class["methods"].extend(methods)
                except IndexError:
                    pass

            # --- Détection des relations UML ---
            elif lower_line.startswith("relation"):
                try:
                    parts = line.split(":")[1].strip().split()
                    if len(parts) >= 3:
                        source, relation_type, target = parts[0], parts[1], parts[2]
                        uml_data["relations"].append({
                            "source": source,
                            "type": relation_type,
                            "target": target
                        })
                except IndexError:
                    pass

        self.current_uml_data = uml_data
        return uml_data


    # ==================================================
    # 🔹 Fonction principale : dessin du diagramme UML
    # ==================================================
    def draw_uml_diagram(self):
        """Draw UML classes and relationships on the canvas."""
        self.canvas.delete("all")
        self.class_positions.clear()

        class_x = 25
        class_y = 30
        class_width = 125
        class_spacing = 89
        line_height = 15
        padding = 10

        if not self.uml_data or not self.uml_data.get('classes'):
            messagebox.showwarning("Warning", "No UML classes detected.")
            return

        classes = (
            self.uml_data['classes']
            if isinstance(self.uml_data['classes'], list)
            else list(self.uml_data['classes'].values())
        )

        for cls_data in classes:
            cls = cls_data['name']
            attributes = cls_data.get('attributes', [])
            methods = cls_data.get('methods', [])

            # --- Calcul des hauteurs ---
            attr_height = line_height * max(len(attributes), 1)
            method_height = line_height * max(len(methods), 1)
            name_height = line_height + padding
            rest_height = attr_height + method_height + padding
            class_height = name_height + rest_height

            # --- Boîte principale ---
            self.canvas.create_rectangle(
                class_x, class_y,
                class_x + class_width, class_y + class_height,
                fill="lightgray"
            )

            # --- Ligne séparatrice nom / reste ---
            self.canvas.create_line(
                class_x, class_y + name_height,
                class_x + class_width, class_y + name_height
            )

            # --- Nom centré ---
            self.canvas.create_text(
                class_x + class_width / 2,
                class_y + name_height / 2,
                text=cls, font=("Arial", 10, "bold"), anchor="c"
            )

            # --- Attributs ---
            attr_y = class_y + name_height + padding // 2
            for attr in attributes:
                self.canvas.create_text(
                    class_x + 10, attr_y, anchor="nw",
                    text=f"- {attr}", font=("Arial", 8)
                )
                attr_y += line_height

            # --- Méthodes ---
            method_y = attr_y + padding // 2
            for method in methods:
                method_name = method.replace("()", "").strip()
                if method_name:
                    self.canvas.create_text(
                        class_x + 10, method_y, anchor="nw",
                        text=f"+ {method_name}()", font=("Arial", 8)
                    )
                    method_y += line_height

            # --- Stocker position et dimensions pour relations ---
            self.class_positions[cls] = {
                "x": class_x,
                "y": class_y,
                "width": class_width,
                "height": class_height,
                "name_height": name_height
            }

            # --- Disposition automatique ---
            class_x += class_width + class_spacing
            if class_x > self.canvas.winfo_width() - class_width:
                class_x = 25
                class_y += class_height + class_spacing

        # --- Dessiner toutes les relations ---
        self.draw_relations()

    def draw_relations(self):
        """Draw UML relations with vertical clarity and smart horizontal offset handling."""
        if not self.uml_data.get("relations"):
            return

        vertical_offset = 3        # décalage entre relations verticales
        horizontal_offset = 3      # décalage vertical entre relations horizontales superposées
        same_level_threshold = 40   # tolérance pour considérer deux classes sur le même niveau horizontal
        padding = 0

        unique_relations = set()
        filtered_relations = []

        # 🔹 Éliminer les doublons
        for relation in self.uml_data["relations"]:
            source = relation.get("source")
            target = relation.get("target")
            rel_type = relation.get("type", "").lower().strip()

            if not source or not target:
                continue

            key = tuple(sorted([source, target])) if rel_type in ["association", "aggregation", "composition"] else (source, target, rel_type)
            if key not in unique_relations:
                unique_relations.add(key)
                filtered_relations.append(relation)

        # 🔹 Compter les connexions horizontales pour ajuster les décalages
        horizontal_connections = {}
        for rel in filtered_relations:
            src = rel["source"]
            tgt = rel["target"]
            if src in self.class_positions and tgt in self.class_positions:
                src_y = self.class_positions[src]["y"]
                tgt_y = self.class_positions[tgt]["y"]
                if abs(src_y - tgt_y) < same_level_threshold:
                    key = tuple(sorted([src, tgt]))
                    horizontal_connections[key] = horizontal_connections.get(key, 0) + 1

        # 🔹 Dessiner les relations
        for index, relation in enumerate(filtered_relations):
            source = relation["source"]
            target = relation["target"]
            rel_type = relation.get("type", "").lower()

            if source not in self.class_positions or target not in self.class_positions:
                continue

            src = self.class_positions[source]
            tgt = self.class_positions[target]

            src_x, src_y, src_w, src_h = src["x"], src["y"], src["width"], src["height"]
            tgt_x, tgt_y, tgt_w, tgt_h = tgt["x"], tgt["y"], tgt["width"], tgt["height"]

            # 🔸 Coordonnées des centres
            src_cx = src_x + src_w / 2
            src_cy = src_y + src_h / 2
            tgt_cx = tgt_x + tgt_w / 2
            tgt_cy = tgt_y + tgt_h / 2

            same_level = abs(src_cy - tgt_cy) < same_level_threshold

            # 🔹 Cas réflexif (classe reliée à elle-même)
            if source == target:
                top_left_x = src_x
                top_left_y = src_y + src["name_height"]
                offset_x = -26
                offset_y = -7
                loop_size = 35
                self.canvas.create_arc(
                    top_left_x + offset_x,
                    top_left_y + offset_y - loop_size,
                    top_left_x + offset_x + loop_size,
                    top_left_y + offset_y,
                    start=0,
                    extent=300,
                    style="arc",
                    outline="#555555",
                    width=1
                )
                self.canvas.create_line(
                    top_left_x + offset_x + loop_size - 5,
                    top_left_y + offset_y - loop_size + 10,
                    top_left_x + offset_x + loop_size,
                    top_left_y + offset_y - loop_size + 15,
                    arrow=tk.LAST,
                    width=2,
                    fill="#555555"
                )
                continue

            # === 🔹 HORIZONTALE ===
            if same_level:
                if src_cx < tgt_cx:
                    start_x = src_x + src_w - padding
                    end_x = tgt_x + padding
                else:
                    start_x = src_x + padding
                    end_x = tgt_x + tgt_w - padding

                start_y = src_cy
                end_y = tgt_cy

                # ✅ Décalage vertical intelligent pour éviter la superposition
                key = tuple(sorted([source, target]))
                relation_index = list(horizontal_connections.keys()).index(key) if key in horizontal_connections else 0
                offset_dir = (-1)**relation_index  # alterne vers le haut/bas
                y_shift = relation_index * horizontal_offset * offset_dir
                start_y += y_shift
                end_y += y_shift

            # === 🔹 VERTICALE ===
            else:
                if src_cy < tgt_cy:
                    start_y = src_y + src_h - padding
                    end_y = tgt_y + padding
                else:
                    start_y = src_y + padding
                    end_y = tgt_y + tgt_h - padding

                start_x = src_cx + (index * vertical_offset)
                end_x = tgt_cx + (index * vertical_offset)

            # === 🔸 Dessin selon type ===
            if rel_type == "inheritance":
                self.draw_triangle(start_x, start_y, end_x, end_y)
            elif rel_type == "association":
                self.canvas.create_line(start_x, start_y, end_x, end_y, fill="#555555")
            elif rel_type == "aggregation":
                self.canvas.create_line(start_x, start_y, end_x, end_y, fill="#555555")
                self.draw_diamond(start_x, start_y, filled=False)
            elif rel_type == "composition":
                self.canvas.create_line(start_x, start_y, end_x, end_y, fill="#555555")
                self.draw_diamond(start_x, start_y, filled=True)
            elif rel_type == "dependency":
                self.canvas.create_line(start_x, start_y, end_x, end_y, dash=(4, 3), arrow="last", fill="#555555")
            elif rel_type == "realization":
                self.canvas.create_line(start_x, start_y, end_x, end_y, dash=(4, 2), arrow="last", fill="#1E90FF")
            elif rel_type == "implements":
                self.canvas.create_line(start_x, start_y, end_x, end_y, dash=(3, 2), arrow="last", fill="#8b008b")
            elif rel_type == "association_class":
                self.canvas.create_line(start_x, start_y, end_x, end_y, fill="#0066CC")
                self.canvas.create_text((start_x + end_x) / 2, (start_y + end_y) / 2 - 10,
                                        text="assoc.", font=("Arial", 8, "italic"), fill="#0066CC")
            elif rel_type == "operation":
                self.canvas.create_line(start_x, start_y, end_x, end_y, dash=(3, 2), arrow="last", fill="#0066CC", width=1.3)
                self.canvas.create_text((start_x + end_x) / 2, (start_y + end_y) / 2 - 10,
                                        text="op.", font=("Arial", 8, "italic"), fill="#0066CC")
            elif rel_type == "use":
                self.canvas.create_line(start_x, start_y, end_x, end_y, dash=(3, 2), fill="#FF6347")
            else:
                self.canvas.create_line(start_x, start_y, end_x, end_y, dash=(3, 2), fill="gray")
                self.canvas.create_text((start_x + end_x) / 2, (start_y + end_y) / 2 - 8,
                                        text=rel_type, font=("Arial", 8, "italic"), fill="gray")

    # ==================================================
    # 🔸 Formes pour les relations UML
    # ==================================================
    def draw_diamond(self, x: int, y: int, filled: bool = False):
        """Draw a diamond shape on the canvas."""
        size = 9
        points = [
            x, y - size,
            x + size, y,
            x, y + size,
            x - size, y
        ]
        self.canvas.create_polygon(
            points, outline="white" if filled else "#555555",
            fill="#555555" if filled else "white"
        )

    def draw_triangle(self, x1: int, y1: int, x2: int, y2: int):
        """Draw a triangle to represent inheritance."""
        arrow_size = 15
        angle = math.atan2(y2 - y1, x2 - x1)

        x_base1 = x1 + arrow_size * math.cos(angle - math.pi / 6)
        y_base1 = y1 + arrow_size * math.sin(angle - math.pi / 6)
        x_base2 = x1 + arrow_size * math.cos(angle + math.pi / 6)
        y_base2 = y1 + arrow_size * math.sin(angle + math.pi / 6)

        self.canvas.create_line(x1, y1, x2, y2, fill="#555555", width=1)
        self.canvas.create_polygon(
            x1, y1, x_base1, y_base1, x_base2, y_base2,
            fill="white", outline="black"
        )


    def uml_data_to_dsl(self):
        """Convertit le modèle UML (dictionnaire) en texte DSL pour la génération de code."""
        if not hasattr(self, "uml_data") or not self.uml_data:
            return ""

        lines = []
        for cls in self.uml_data.get("classes", []):
            lines.append(f"Class {cls['name']}:")
            lines.append(f"    Attributes: {', '.join(cls.get('attributes', []))}")
            lines.append(f"    Methods: {', '.join(cls.get('methods', []))}")
            lines.append("")

        for rel in self.uml_data.get("relations", []):
            lines.append(f"Relation: {rel['source']} {rel['type']} {rel['target']}")

        return "\n".join(lines)
    


    