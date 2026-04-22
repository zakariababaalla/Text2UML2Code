README — Text2UML2Code
Prompt-Guided Multi-LLM MDA Pipeline with DSL Stabilization
================================================================================

1) Overview
-----------
This contribution introduces a robust Model-Driven Architecture (MDA)
pipeline that transforms textual software specifications into UML class diagrams
and executable code using a multi-LLM orchestration strategy.

The key idea is that no single model is optimal for all tasks. Therefore, the
pipeline dynamically selects specialized LLMs depending on:
- Semantic complexity of the input text
- Detected language (e.g., English/French/Arabic)
- Task type (UML extraction, DSL structuring, code generation)
- Available computational resources

A textual UML DSL is used as an intermediate representation to enforce strict
formatting, reduce hallucinations, and guarantee structural consistency.

2) Input / Output
-----------------
Input:
- Natural language specification (multilingual)
- Potentially long, ambiguous, or heterogeneous descriptions

Outputs:
- Textual UML DSL (strict structured format)
- UML class diagram (PIM-level model)
- Code artifacts (PSM/code-level), e.g. Python/Java/C#

3) Core Components
------------------

3.1 Prompt Engineering Layer (Multilingual)
-------------------------------------------
The pipeline uses carefully designed prompts that:
- Force a strict hierarchical output format
- Normalize class/attribute/method naming conventions
- Explicitly require UML relations and completeness
- Reduce variability via constraints (no free-form text allowed)

Optimization strategies:
- Few-shot prompting: examples of correct DSL output
- Chain-of-Thought guidance: internal reasoning before final output
- Self-consistency: multiple generations -> selection of most stable output

3.2 Intermediate DSL (Stabilization and Validation)
--------------------------------------------------
The textual UML DSL acts as a formal pivot:
- It standardizes the representation of UML entities
- It enables automatic parsing and validation
- It detects missing classes referenced in relations
- It reduces structural instability and hallucinated elements

Typical DSL structure:
- Class definitions with attributes + methods
- Relations expressed in single-line formal statements

3.3 Multi-LLM Orchestration Layer
--------------------------------
Multiple open-source LLMs are integrated and executed via:
- Local inference (Ollama) for lightweight deployment
- Remote/GPU inference for high-throughput scenarios

Models are selected based on strengths:
- LLaMA / Mistral: robust semantic extraction (long texts)
- DeepSeek-Coder: strong reasoning and method generation
- CodeLlama: best final code generation quality

4) Pipeline Execution (End-to-End)
----------------------------------
Step 1 — Input analysis
- Detect language
- Estimate text complexity and ambiguity

Step 2 — Concept extraction
- Select extraction-oriented LLM
- Generate initial UML DSL candidate

Step 3 — DSL validation and refinement
- Check structure and completeness
- Repair missing elements (classes/methods/relations)
- Enforce naming conventions

Step 4 — UML model generation
- Parse DSL -> UML model
- Generate UML diagram (class diagram)

Step 5 — Code generation
- Select code-oriented LLM (or code generator)
- Produce code aligned with UML structure
- Validate basic compilability / consistency

5) Experimental Evaluation
--------------------------
The evaluation measures:
A) UML extraction metrics:
- Precision / Recall / F1-score for:
  * Classes
  * Attributes
  * Methods
  * Relations

B) Code generation metrics:
- Compilation success rate
- Structural alignment UML -> code
- Completeness of generated classes/methods

Key observation:
- Best global robustness on long/ambiguous/multilingual texts
- Strong improvements on method extraction and complex relations
- Highest stability due to DSL enforcement + multi-model specialization

6) Strengths
------------
- Robustness to ambiguity and multilingual inputs
- Formal control using DSL intermediate representation
- Adaptive multi-LLM selection improves reliability
- Better code generation quality and UML-code consistency

7) Limitations
--------------
- Higher computational cost than single-model pipelines
- Requires orchestration logic and prompt maintenance
- Some edge cases still need human validation (implicit requirements)

8) Recommended usage
-------------------
Recommended when:
- Inputs are long, ambiguous, or multilingual
- Code generation is required (end-to-end automation)
- High structural consistency is needed for MDA integration
- Industrial-grade robustness is targeted
