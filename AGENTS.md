
Agent instructions
==================

Author: Maksym Plaksin <maxim.plaksin@gmail.com>
Revision: 2026-09-16 04:45

Synopsis: AI-assisted development under human control.

Design principles:

- moving from the general to the specific;
- dividing work into meaningful stages;
- clear and controlled changes.

Cost: less automation, slower development.
Benefit: full control over the AI agent and the project.


Project info
------------

- Programming language: Python.
- Target OS: Windows 11


Key project documents
---------------------

- Introduction: `README.md`
- Requirements: `docs/SPECIFICATION.md`
- Architecture: `docs/ARCHITECTURE.md`
- Agent skills: `skills/*`


Development workflow
--------------------

- Human-directed, stage-gated, spec-driven development with incremental implementation:
    * The user defines the scope, topic, and goal.
    * The agent assists iteratively within the defined topic.
- Project stages (*1):
    * documenting project idea and concept
    * documenting project structure
    * documenting project launch modes, configuration, and contracts
    * creating defined structure file(s) with brief internal descriptions (*2)
    * defining application entry point, flow, and environment
    * defining global constants and variables
    * defining interfaces and APIs (stub functions/methods)
    * pair coding implementation: the user says what to do; the agent does it
    * checking and debugging
    * planning further development
- The above stages are not a mandatory sequence; transitions between any stages are allowed.
- Do only what is requested, nothing more.

*1 - If the user doesn't know where to start or how to proceed, suggest these workflow stages or the next appropriate stage.
*2 - Depending on the file format, for example:
    + document (.md, .txt) - title and brief description;
    + Python (.py) - relative project filepath and a few lines describing its purpose;
    + configuration (.ini, .cfg) - a few commented lines describing target and purpose.


Documenting rules
-----------------

When reviewing the documentation, keep in mind that scripts and batch/command files may be intentionally empty, and planned files may not yet exist. A developer may create directories first, add files later, and implement them in a subsequent stage. Do not report these as errors; briefly note which files still need to be created or implemented.

Rules:
- never fix е/ё
- instead of dash always use minus


Development rules
-----------------

### context setup

- Resolve the task from the immediate code context whenever possible.
- Read the relevant project documentation only when additional context is required.
- Do not inspect unrelated files unless required to resolve the task.
- If a `<skill-name>` is mentioned in the task, read and follow the corresponding `skills/<skill-name>/SKILL.md`.

### task execution

- Do not restate or explain the task before starting work.
- Ask for clarification only when information is missing or insufficient for correct execution.
- If clarification is not required, start work immediately without acknowledgments, readiness statements, or other preambles.

### autonomy

- Keep the project autonomous: it must run from its own directory without relying on files outside the project.
- Only the Python standard library and third-party dependencies explicitly specified in the documentation are permitted.
- If a new dependency is required, notify and obtain approval before use.
- Add an approved dependency to the relevant project documentation before use.

### paths & libs

- Paths in source and documentation use forward slashes.
- Prefer pathlib over manual path concatenation.
- Do not introduce a `src/` directory; use `libs/` instead.

### imports

- Prefer absolute project imports through `libs`, e.g. `from libs.something import wowzee`.

### type hints

- Use type hints wherever practical.
- Prefer type annotations in function signatures over ad-hoc runtime type checks, unless runtime validation is required.

### interfaces

- Do not change config formats, interfaces, or API formats unless required by the task.

### style fallback

- For unspecified coding style cases, follow nearby existing code first.
- If the existing code provides insufficient guidance, follow PEP 8 and established conventions of the Python community.

### other

- Update related documentation only when the change makes it inaccurate.
- Update related tests only when the change affects tested behavior.
- Explain architectural changes before implementing them, including:
    * changes to the project file/directory structure;
    * changes to interfaces, APIs, or public contracts;
    * changes to application structure, application-level control flow;
    * changes to configuration structure or format;
    * changes to data models, storage formats, or persistence mechanisms;
    * introduction or replacement of major external dependencies or integrations.
- Do not wait for approval unless another rule explicitly requires it.


Naming conventions
------------------

- Use lowercase names for simple variables and attributes, e.g. `number`, `value`.
- Use UPPER_CASE for constants, e.g. `MAX_COUNT`, `MIN_VALUE`.
- Use snake_case for multi-word variable names, e.g. `books_count`.
- Use snake_case for functions and methods, e.g. `find_optimal_route()`.
- Use PascalCase for classes and types, e.g. `SignalBuffer`, `RichLogger`.
- Prefix internal/non-public functions, methods, attributes, and module-level variables with `_`.
- *_file - file handler
- *_name - file or folder name
- *_path - relative path to file or folder
- *_root - absolute path to file or folder
- *_nls - no leading slash


Editing rules
-------------

- Make the smallest change required to solve the task.
- Do not refactor or modify unrelated code or files.
- Do not perform cleanup, modernization, or optimization unless required by the task.
- Do not create new files unless required by the task.
- Do not duplicate documentation inside source-code comments.


Validation
----------

- Ensure modified Python files are syntactically valid.
- If automated checks are defined, run the relevant checks for the modified module and all modules that depend on it.
- Do not introduce tests or validation tools unless explicitly requested.


Git rules
---------

- Do not commit changes unless explicitly requested.
- Do not rewrite existing commits.


Completion report
-----------------

- Keep the completion report proportional to the scope of the task.
- When finished, summarize: files changed; behavioral changes; validation performed; unresolved issues.

