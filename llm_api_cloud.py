import subprocess
import json
import re
import requests
# ===============================
# ⚙️ Fonction pour interroger Ollama
# ===============================

def query_ollama(prompt, model="phi3:mini", host="http://localhost:11434"):
    try:
        url = f"{host}/api/generate"
        payload = {"model": model, "prompt": prompt, "stream": False}
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()
    except requests.exceptions.RequestException as e:
        return f"❌ Erreur de connexion à Ollama : {e}"
    except json.JSONDecodeError:
        return f"⚠️ Réponse non JSON : {response.text}"
    except Exception as ex:
        return f"⚠️ Erreur inattendue : {ex}"
    
# ===============================
# 🧹 Filtrage intelligent du DSL généré
# ===============================
def clean_generated_dsl(dsl: str) -> str:
    """
    Filtre intelligent et non destructif du DSL généré :
    - Supprime les commentaires (//, #)
    - Élimine les attributs et méthodes "None" ou "None()"
    - Nettoie les explications parasites et les parenthèses inutiles
    - Corrige les erreurs courantes entre attributs et méthodes
    - Conserve la structure et les relations du DSL
    """

    if not dsl or not isinstance(dsl, str):
        return dsl

    lines = []
    current_section = None

    for raw_line in dsl.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # 🔹 Supprimer les commentaires et phrases narratives
        line = re.sub(r"//.*", "", line)
        line = re.sub(r"#.*", "", line)
        line = re.sub(r"\s*(However|This relation|Since the specification|For example|Similarly).*", "", line, flags=re.IGNORECASE)

        # 🔹 Identifier la section actuelle
        if line.lower().startswith("class "):
            current_section = "class"
        elif line.lower().startswith("attributes"):
            current_section = "attributes"
        elif line.lower().startswith("methods"):
            current_section = "methods"
        elif line.lower().startswith("relation"):
            current_section = "relation"

        # 🔹 Normalisation douce des balises
        line = re.sub(r"^class\b", "Class", line, flags=re.IGNORECASE)
        line = re.sub(r"^attributes\b", "Attributes", line, flags=re.IGNORECASE)
        line = re.sub(r"^methods\b", "Methods", line, flags=re.IGNORECASE)
        line = re.sub(r"^relation\b", "Relation", line, flags=re.IGNORECASE)

        # Correction automatique selon le contexte
        if current_section == "attributes":
            # Supprime les parenthèses ou explications
            line = re.sub(r"\([^)]*\)", "", line)
            line = re.sub(r"Attributes:\s*([A-Za-z_]\w*).*", r"Attributes: \1", line)

            # Cas : attribut contient des parenthèses → c’est une méthode
            if re.search(r"\w+\s*\(.*\)", raw_line):
                attr_name = re.sub(r".*?(\w+)\s*\(.*", r"\1", raw_line)
                line = f"Methods: {attr_name}()"
                current_section = "methods"

        elif current_section == "methods":
            # Nettoyage des parenthèses et explications
            line = re.sub(r"\([^)]*\)", "()", line)
            line = re.sub(r"Methods:\s*([A-Za-z_]\w*)\s*\(.*", r"Methods: \1()", line)
            line = re.sub(r"\)\s+\w+.*", "()", line)

        # Supprimer les lignes inutiles ou incohérentes
        if re.search(r"\b(None|none)\b", line):  # attributs ou méthodes "None"
            continue
        if re.search(r"Methods:\s*\(\)", line):  # ligne "Methods: ()"
            continue
        if re.search(r"Attributes:\s*$", line):  # ligne vide d’attributs
            continue
        if re.search(r"Methods:\s*$", line):  # ligne vide de méthodes
            continue
        if len(line.split()) > 12 and not line.startswith(("Class", "Attributes", "Methods", "Relation")):
            continue

        if line:
            lines.append(line.strip())

    # 🔹 Nettoyage final (espaces, doublons, retours multiples)
    cleaned_dsl = "\n".join(dict.fromkeys(lines))  # supprime les doublons tout en gardant l’ordre
    cleaned_dsl = re.sub(r"\n{3,}", "\n\n", cleaned_dsl).strip()

    return cleaned_dsl

def ensure_all_classes_exist(dsl: str) -> str:
    """
    Vérifie que toutes les classes mentionnées dans les relations existent dans le DSL.
    Si certaines sont manquantes, elles sont ajoutées automatiquement, sauf si :
      - Elles existent déjà.
      - Leur nom semble invalide (ex: 'Class', 'Relation', 'Attribute', etc.).
      - Elles contiennent des mots-clés réservés non qualifiables comme noms de classe.
    """

    if not dsl or not isinstance(dsl, str):
        return dsl

    # --- 1️⃣ Extraire toutes les classes déjà définies ---
    defined_classes = set(re.findall(r'\bClass\s+(\w+)\s*:', dsl))

    # --- 2️⃣ Extraire toutes les classes mentionnées dans les relations ---
    related_classes = set()
    for match in re.findall(r'Relation:\s*(\w+)\s+\w+\s+(\w+)', dsl):
        related_classes.update(match)

    # --- 3️⃣ Liste de mots réservés / noms non valides ---
    invalid_class_names = {
        "class", "relation", "relations", "attribute", "attributes",
        "method", "methods", "composition", "aggregation", "association",
        "inheritance", "with", "of", "in", "from", "to", "type", "data",
        "entity", "object", "model", "none"
    }

    # --- 4️⃣ Identifier les classes manquantes et valides ---
    missing_classes = set()
    for cls in related_classes:
        cls_lower = cls.lower()
        if cls in defined_classes:
            continue  # déjà définie
        if any(cls_lower.startswith(invalid) or cls_lower.endswith(invalid)
               for invalid in invalid_class_names):
            continue  # nom non qualifiable
        if cls_lower in invalid_class_names:
            continue  # mot-clé réservé
        missing_classes.add(cls)

    # --- 5️⃣ Ajouter les classes manquantes ---
    if missing_classes:
        additions = "\n\n".join([
            f"Class {cls}:\n    Attributes:\n    Methods:" for cls in sorted(missing_classes)
        ])
        dsl = dsl.strip() + "\n\n# ------------------------------------🔧 Auto-added missing classes 🔧------------------------------------\n\n" + additions

    return dsl


def check_dsl_structure(dsl_text: str) -> list:
    """
    Checks the structure of the generated DSL line by line.
    Returns a list of diagnostic messages (in English) describing anomalies or inconsistencies.
    """

    if not dsl_text or not isinstance(dsl_text, str):
        return ["❌ The DSL text is empty or invalid."]

    issues = []
    lines = dsl_text.splitlines()

    valid_class_pattern = re.compile(r"^Class\s+\w+\s*:$")
    valid_attr_pattern = re.compile(r"^Attributes:\s*(.*)$")
    valid_method_pattern = re.compile(r"^Methods:\s*(.*)$")
    valid_relation_pattern = re.compile(r"^Relation:\s+\w+\s+\w+\s+\w+$")

    for idx, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()

        # Ignore empty lines and comments
        if not line or line.startswith("#"):
            continue

        # ✅ Valid patterns
        if valid_class_pattern.match(line):
            continue

        elif valid_attr_pattern.match(line):
            if "()" in line or re.search(r"\bNone\b", line, re.IGNORECASE):
                issues.append(f"⚠️ Line {idx}: Suspicious attribute → {line}")
            continue

        elif valid_method_pattern.match(line):
            if re.search(r"\bNone\b", line, re.IGNORECASE):
                issues.append(f"⚠️ Line {idx}: Method 'None()' should be removed.")
            elif not re.search(r"\w+\(\)", line):
                issues.append(f"⚠️ Line {idx}: Invalid method signature → {line}")
            continue

        elif valid_relation_pattern.match(line):
            continue

        else:
            # ❌ Unknown structure
            issues.append(f"❌ Line {idx}: Invalid DSL structure → '{line}'")

    if not issues:
        issues.append("✅ No structural anomalies detected in the DSL.")
    else:
        issues.insert(0, "🔎 DSL structure audit completed with the following remarks:")

    return issues


# ===============================
# 🧩 Étape 1 : Spécifications → DSL
# ===============================
def get_dsl_from_spec(spec_text, model_name="phi3:mini"):
    prompt = f"""
    Tu es un expert en modélisation UML et en ingénierie dirigée par les modèles (MDA).
    Ta mission est de générer un **DSL UML textuel, structuré et exploitable automatiquement** à partir du texte suivant décrivant un système.

    ---

    ### Objectif
    Produis un **DSL UML complet et strictement formaté**, comprenant :
    - Toutes les classes identifiées.
    - Leurs attributs (noms uniquement, séparés par des virgules).
    - Leurs méthodes (noms uniquement, sans paramètres).
    - Toutes les relations UML pertinentes entre les classes.

    ---

    ### Structure OBLIGATOIRE

    Chaque classe et relation doit être écrite **exactement** de cette manière :

    Class NomClasse:
        Attributes: attr1, attr2, attr3
        Methods: meth1(), meth2()

    Relation: ClasseSource type_relation ClasseCible

    Où :
    - `type_relation` ∈ {"association", "aggregation", "composition", "dependency", "realization", "implements", "operation", "use", "inheritance", "association_class","Autre"}
    - **Aucune explication, cardinalité, commentaire ou texte narratif n’est autorisé.**

    ---

    ### Exemples à suivre

    Exemple 1 :
    Class Library:
        Attributes: libraryId
        Methods: getLibraries()

    Class Book:
        Attributes: title, author, publicationYear, ISBN
        Methods: getBookDetails()

    Class Reader:
        Attributes: name, address, cardNumber
        Methods: borrowBook()

    Relation: Library composition Book
    Relation: Reader association Book

    ---

    Exemple 2 :
    Class Client:
        Attributes: clientId, name
        Methods:

    Class Account:
        Attributes: accountNumber, type, balance
        Methods:

    Class Transaction:
        Attributes: amount, date, transactionType
        Methods:

    Relation: Client composition Account
    Relation: Account composition Transaction

    ---

    ### Contraintes strictes

    1. Structure :
    - Chaque classe doit contenir trois lignes : `Class`, `Attributes`, `Methods`.
    - Si une section est vide, garde la ligne (ex. `Methods:`).

    2. Relations UML :
    - Chaque relation sur une seule ligne :  
        `Relation: ClasseSource type_relation ClasseCible`
    - Ne pas inclure de cardinalités, ni de texte descriptif.
    - Si une 'relation réflexive' est détectée (une classe en relation avec elle-même),  
     ➜ Alors la 'classe source et la classe cible sont identiques'.  
     ➜ Autrement dit : `ClasseSource = ClasseCible`.  
     ➜ Exemple :
       ```
       Relation: Employee association Employee
       ```
       Cela indique qu’un employé est en relation avec un autre employé ou avec lui-même (hiérarchie, supervision, etc.).


    3. Complétude :
    - Toute classe citée dans une relation doit être définie.
    - Si une classe implicite apparaît, crée-la avec une structure minimale.

    4. Normalisation :
    - Classes : PascalCase.
    - Attributs et méthodes : camelCase.
    - Aucune indentation inutile ni commentaire.

    ---

    ### Types de relations à détecter
    Analyse le texte et identifie les relations suivantes :
    - association : lien simple entre deux classes.
    - aggregation : lien "part-of" faible.
    - composition : lien "contains" fort.
    - dependency : utilisation ponctuelle.
    - realization / implements : relation interface/implémentation.
    - inheritance : généralisation ("is a type of").
    - operation / use : interaction explicite.
    - association_class : relation porteuse d’attributs (facultatif).
    - Reflexive_relation : une classe est en relation avec elle-même. ➜ Dans ce cas, 'ClasseSource = ClasseCible' (exemple : `Relation: Employee association Employee`).
    - Autre : si la relation détectée ne figure pas dans la liste précedente, il suffit d'affecter le nom de cette nouvelle reltion au Type_relation.

    ---

    ### 🚫 Interdictions
    - ❌ Aucun commentaire (`//`, `#`, `/* */`...).
    - ❌ Aucune phrase narrative.
    - ❌ Aucune cardinalité (`1..*`, `n`, etc.).
    - ❌ Aucune ponctuation superflue.
    - ❌ Aucun mot hors DSL.

    ---

    ### Sortie attendue
    Uniquement le **DSL final**, propre et conforme à la structure demandée.  
    Aucune phrase, explication ou texte avant/après.

    ---

    ### Voici la spécification utilisateur :
    {spec_text}
    """

    
    # ✅ Exécution sur le serveur Ollama distant avec le modèle choisi
    raw_dsl = query_ollama(prompt, model=model_name, host="http://localhost:11434")

    # ✅ Nettoyage et validation
    cleaned_dsl = clean_generated_dsl(raw_dsl)
    final_dsl = ensure_all_classes_exist(cleaned_dsl)

    return final_dsl
# ===============================
# 🧩 Étape 2 : UML → Code Python
# ===============================
def get_code_from_uml(uml_description, language="Python", model_name="phi3:mini"):
    """
    Génère le code source (Python, Java, etc.) à partir d'un modèle UML
    en utilisant le modèle LLM sélectionné.
    """
    prompt = f"""
    À partir du modèle UML suivant, génère le code {language} correspondant,
    en respectant les classes, leurs attributs, méthodes et relations.

    - Le code doit être directement exécutable.
    - Supprime toute explication ou commentaire en dehors du code.
    - Respecte les conventions syntaxiques et POO du langage choisi.
    - Si une méthode d'une classe n'est pas définie dans le modèle UML, tu dois l'implémnter.
    
    UML Model :
    {uml_description}
    """

    # ✅ Envoi du prompt au modèle choisi
    raw_code = query_ollama(prompt, model=model_name, host="http://localhost:11434")

    return raw_code.strip()

