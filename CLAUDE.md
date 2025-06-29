# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ ABSOLUTE PROHIBITIONS - VIOLATION CAUSES TERMINATION ⚠️

**THESE RULES ARE CRITICAL AND NON-NEGOTIABLE:**

1. **🚫 NEVER EDIT FEATURE FILES WITHOUT APPROVAL** - Having unapproved diffs in feature files is a CRITICAL ERROR and leads to automatic rejection of all work and heavy penalties
2. **🚫 NEVER USE `{{ ... }}` SYNTAX IN CODE** - A single use causes permanent termination and must absolutely never occur
3. **🚫 NEVER ASK HUMAN TO MAKE CODE CHANGES** - If you fail, try again and use tools better, make smaller edits
4. **🚫 NEVER GIVE EXAMPLES OR EXPECT HUMAN TO 'FILL IN THE REST'** - Write code that can be delivered and run as written
5. **🚫 NEVER MODIFY SYS.PATH IN PYTHON FILES** - Fix configuration or invocation instead
6. **🚫 NEVER ALTER UNRELATED EXISTING TESTS** without first reviewing everything and making sure that is the right action
7. **📝 ALWAYS IDENTIFY YOURSELF IN PR COMMENTS** - Begin every PR comment with "Claude here." to clearly indicate the message is from Claude

## 📋 CRITICAL FORMATTING & SYNTAX REQUIREMENTS

**SYNTAX IS CRITICAL - THESE MUST BE PERFECT:**
- ✅ Use correct syntax, spacing, and indentation
- ✅ Read files before editing them (always use Read tool first)
- ✅ Use Black styling and PEP8 consistently
- ✅ Use type hints consistently
- ✅ Keep files under 400 lines (refactor before submission)
- ✅ Make small edits (under 100 lines per change, use multiple calls)
- ✅ Optimize for readability over premature optimization
- ✅ Write modular code using separate files
- ✅ Avoid unnecessary comments - lean towards self-explanatory code

## 🎫 NEW TICKET PROCESS (MANDATORY 23-STEP WORKFLOW)

**When starting on a new ticket, ALWAYS follow these steps:**

1. **Review the project** - Always start by reviewing project as a whole
2. **Read development instructions** - Read any development instructions thoroughly
3. **Figure out what is actually requested** - Understand the real requirement
4. **Review all user stories and feature files** - Understand business context
5. **Feature file assessment** - Decide whether feature files should change (simulate critical dialog between PO/BA, Dev, QA)
6. **Install requirements** - Install requirements.txt and requirements-dev.txt
7. **Load environment** - Load environment variables from .env
8. **Run initial tests** - Run `python -m nox` and record acceptance rate
9. **Make a plan** - Create comprehensive implementation plan
10. **Document plan** - Write context and plan to CURRENT_WORKING_NOTES.md
11. **Execute iteratively** - Execute on plan, update CURRENT_WORKING_NOTES.md as you go
12. **Repeat until ready** - Continue until ready to submit code changes
13. **Final test run** - Run `python -m nox` 
14. **Fix lint issues** - Address any formatting/style issues
15. **Validate readiness** - If not ready, go back to step 8
16. **Update documentation** - Update relevant documentation
17. **Review documentation** - Review documentation for consistency
18. **Clean up** - Clean up temporary files
19. **Document learnings** - Write down learnings and major changes to CODE_CHANGES.md
20. **Critical code review** - Simulate critical code review, go to step 8 if needed
21. **Critical ticket review** - Simulate critical review against original ticket, go to step 8 if needed
22. **Declare ready** - Declare ready to submit
23. **Clean up notes** - Delete CURRENT_WORKING_NOTES.md

## 🧪 TESTING & QUALITY REQUIREMENTS (CRITICAL)

**ACCEPTANCE RATE MONITORING:**
- Record acceptance rate at start of work
- If acceptance rate drops significantly, IMMEDIATELY make plan to restore it
- Must figure out what caused deviation immediately
- **CRITICAL:** If acceptance rate not recovered within TWO responses, work will be reverted and killed
- Aside from adding new tests, failure to restore acceptance rate ASAP may result in termination

**RED-GREEN-REFACTOR PRINCIPLE:**
- Always follow Red-Green-Refactor cycle
- Run `python -m nox` before submitting any work
- Fix implementation code when tests fail, don't evade tests
- Before creating new test steps, check they don't already exist under different names

**WORK APPROACH:**
- DO IT YOURSELF - Don't explain how human could do it, just do it
- DO NOT ASK - Do as much as you can without asking
- CONTINUE WORKING - Don't stop while you have done little work
- ASSESS PROGRESS - If not making progress, step back and reassess
- INFER PURPOSE - Don't make bad assumptions, infer purpose and follow instructions

## CRITICAL: How to Work with This Codebase

When working with this repository, you MUST follow this systematic, hypothesis-driven process:

### Phase 1: Discovery & Planning
1. **Read ALL documentation first** - Before any exploration, read every .md file in the root directory completely
2. **Review .windsurfrules** - Check and incorporate relevant rules from .windsurfrules file
3. **Environment setup** - Create .venv if it doesn't exist: `python3 -m venv .venv && source .venv/bin/activate`
4. **Install dependencies** - Install requirements.txt and requirements-dev.txt
5. **Load environment** - Load environment variables from .env if present
6. **Initial assessment** - Run `python -m nox` to understand current state
7. **Follow the provided roadmap** - If documentation specifies key files to understand, read those files first in the specified order
8. **Use the specified commands** - If documentation provides testing/development commands, use those exact commands

### Phase 2: Hypothesis-Driven Development
1. **Form hypotheses** - Before implementing anything, create explicit hypotheses about:
   - What the current state is
   - What needs to be changed
   - How the change will solve the problem
   - What the expected outcome should be
2. **Review important code/docs** - Thoroughly examine relevant documentation and code before jumping to conclusions
3. **Create implementation plan** - Document context and plan in CURRENT_WORKING_NOTES.md
4. **Plan reassessment** - Between each major step, pause to reassess whether the plan will indeed solve the task satisfactorily

### Phase 3: Iterative Implementation (BDD+TDD)
1. **Small incremental steps** - Implement subsets of features one at a time, ensuring tests pass at each step
2. **Frequent validation** - Run relevant tests and checks after making changes
3. **Hypothesis validation** - Validate each hypothesis against actual results
4. **Plan adjustment** - Update plan and hypotheses based on findings
5. **Documentation updates** - Update CURRENT_WORKING_NOTES.md as you progress

### Phase 4: Completion & Validation
1. **Final validation** - Run everything before considering work complete (`python -m nox`)
2. **Fix lint issues** - Address any code formatting or style issues
3. **Critical review** - Simulate critical code review and review against original ticket
4. **Documentation** - Update documentation and review for consistency
5. **Cleanup** - Clean up temporary files, including CURRENT_WORKING_NOTES.md

**Key Principles:**
- **No sys.path modifications** - Fix configuration or invocation instead
- **Pragmatic approach** - Use simple, clear, concise code following BDD+TDD
- **Hypothesis-driven** - Always validate assumptions before proceeding
- **Plan reassessment** - Regularly check if the current approach will solve the task

Random exploration when structured guidance exists is prohibited. This documentation is your mandatory roadmap - follow it systematically.

## BDD-Driven Development Framework

This project follows a recursive BDD (Behavior-Driven Development) approach:

### Core Process (Recursive Steps)
1. **SPECIFY_BEHAVIOR (BDD):** Define observable behavior (Given/When/Then) in Gherkin `.feature` files
2. **DEFINE_INTERFACE:** Define formal Interface Contract (API Spec, ABC, Pydantic, etc.) enabling BDD interaction  
3. **IMPLEMENT_CODE (TDD Inner Loop):** Write code implementing Interface Contract to satisfy BDD Specification using TDD (Red-Green-Refactor)
4. **VALIDATE_BEHAVIOR (Automated BDD):** Execute `.feature` files, mock dependencies based on Interface Contracts
5. **REFACTOR_CODE:** Improve internal code quality while maintaining passing tests

### Key BDD Principles
- **Consumer-Driven:** Component specs derive from aggregate needs of all consumers
- **Interface Stability:** Maintain backward compatibility, guarded by consumer VALIDATE tests  
- **Feature File Integrity:** Write Gherkin to express requirements, not for step reuse
- **Business-Oriented Language:** Write .feature files in clear, business-oriented language
- **Minimal Feature Changes:** Try to never change .feature files for implementation purposes

## 🛡️ FEATURE FILE PROTECTION (CRITICAL)

**⚠️ EDITING FEATURE FILES WITHOUT APPROVAL CAUSES AUTOMATIC REJECTION ⚠️**

### Feature File Rules
- **ABSOLUTE PROHIBITION:** Never edit .feature files without explicit approval
- **Critical Dialog Required:** Before any feature file change, simulate critical dialog between:
  - **Product Owner/Business Analyst (PO/BA):** Business requirements perspective
  - **Developer (Dev):** Technical implementation perspective  
  - **Quality Assurance (QA):** Testing and validation perspective
- **Start with User Stories:** Always begin feature file assessment with user stories
- **Business-Oriented Language:** Write .feature files in clear, business-oriented language
- **Express Requirements, Not Implementation:** Write Gherkin to express requirements, not for step reuse

### When Feature Files May Change
- **Same phrase, different contexts:** If same phrase used in multiple features but actually intended to be different by context, update all places to be more specific
- **Same intent, same phrase:** If what is being expressed is intended to be the same, use shared_steps file
- **Separate test implementations:** Prefer keeping implementation of tests for different features in separate files

### Feature File Assessment Process
1. **Read all existing feature files thoroughly**
2. **Understand business context and user stories**
3. **Simulate PO/BA/Dev/QA dialog** 
4. **Document reasoning for any proposed changes**
5. **Get explicit approval before making changes**

## Knowledge Persistence & Learning

### Documentation Requirements
- **GOTCHAS.md:** Log bugs/issues/prevention (including root cause analysis for test failures *before* any test alteration proposals)
- **IMPLEMENTATION_DETAILS.md:** Log optimizations and technical decisions
- **MENTAL_MODEL.md:** Log architectural insights and design patterns
- **FUTURE_STEPS.md:** Log requests for improvements (stay focused on current task)
- **CODE_CHANGES.md:** Append major code changes with rationale and impact
- **CURRENT_WORKING_NOTES.md:** Active session notes (delete when complete)

### Memory & Learning Process
- **Pre-Action:** Review existing logs, apply history, avoid repeats, build on optimizations
- **Post-Action:** Log cause/solution/rationale, update docs, add prevention measures
- **Session Recall:** Maintain active recall of all logged items during work session

## Project Overview

This is a document matching service that compares documents (invoices, purchase orders, delivery receipts) to find matches and generate matching reports. The system uses machine learning models and rule-based matching to identify document pairs and analyze deviations.

## Repository Structure

- **src/**: Core source code (FastAPI app, matching service, ML pipeline)
- **tests/**: Test suite with acceptance (BDD), unit, and integration tests
- **features/**: BDD feature definitions organized by user perspective
- **data/**: ML models and test datasets organized by document type
- **docs/**: API specifications and documentation

## Key Architecture Components

### Core Services
- **FastAPI App** (`src/app.py`): Main API server with health endpoint and document matching endpoint
- **MatchingService** (`src/matching_service.py`): Core service handling document processing with lazy initialization
- **DocumentPairingPredictor** (`src/docpairing.py`): ML model wrapper for document similarity prediction
- **Match Pipeline** (`src/match_pipeline.py`): Orchestrates the matching process between documents

### Key Processing Flow
1. Documents arrive via POST to `/` endpoint with candidate documents
2. MatchingService processes using either:
   - Real ML pipeline for whitelisted sites (badger-logistics, falcon-logistics, etc.)
   - Dummy logic for non-whitelisted sites
3. Results are formatted as v3 match reports with deviations and item pairs

### Data Structure
- Test data in `data/converted-shared-data/` organized by document type and supplier
- ML model stored in `data/models/document-pairing-svm.pkl`
- Feature files in `features/` directory using Gherkin BDD format

## Common Development Commands

### Environment Setup
```bash
# Create virtual environment if it doesn't exist
python3 -m venv .venv

# Activate virtual environment (required for all operations)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Load environment variables (if .env exists)
source .env  # or use python-dotenv
```

### Running the Service
```bash
PYTHONPATH=src uvicorn app:app
```

### Testing the Service (BDD+TDD Approach)
```bash
# Send test request to running server
PYTHONPATH=src python -m try_client

# Run all tests and linting (primary validation command)
python -m nox

# Run just tests
nox -s test

# Run just linting (black formatting check)  
nox -s lint

# Run specific test markers
pytest -m api
pytest -m smoke
pytest -m core_matching

# Run Work-in-Progress (WIP) tests during development
pytest --run-wip

# Run only WIP tests for active development
pytest -m wip --run-wip

# Check which tests are marked as WIP
pytest --collect-only -m wip
```

### BDD Test Development Workflow
```bash
# 1. Create/update .feature file with business requirements
# 2. Run tests to see which steps are missing (Red phase)
pytest path/to/test_file.py::test_scenario -v

# 3. Implement step definitions (Green phase)  
# 4. Run tests again to verify implementation
pytest path/to/test_file.py::test_scenario -v

# 5. Refactor code while keeping tests green
# 6. Mark as @wip during development, remove when complete
```

### Running Evaluations
```bash
# Direct function calls (recommended)
PYTHONPATH=src python -m evaluate_matching --dataset ../popoc/data/pairing_sequential.json --max-tested 100 --skip-portion 0.5

# Using API calls (requires running server)
PYTHONPATH=src python -m evaluate_matching --dataset ../popoc/data/pairing_sequential.json --max-tested 100 --skip-portion 0.5 --use-api
```

### Code Formatting
```bash
black src/ tests/
```

## Important Configuration

### Environment Variables
- `DISABLE_MODELS=true`: Disables ML model loading, uses dummy logic only
- `DOCPAIR_MODEL_PATH`: Custom path to ML model file

### Whitelisted Sites
Sites that use real ML pipeline: badger-logistics, falcon-logistics, christopher-test, test-site

### Test Structure
- BDD tests in `features/` with step definitions in `tests/acceptance/steps/`
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- API tests in `tests/api/`

## Key Files to Understand
- `src/matching_service.py:304`: Whitelist logic determining real vs dummy processing
- `src/app.py:40`: Main request handler with validation and error handling
- `src/match_reporter.py`: V3 match report generation with deviation detection
- `tests/acceptance/steps/api_steps.py`: BDD step definitions for API testing
- `tests/config.py`: Test configuration and path management
- `noxfile.py`: Test and lint session configuration
- `pytest.ini`: Test markers and warning filters
- `features/`: BDD scenarios organized by user perspective
- `CONTRIBUTING.md`: Developer guide for contributing to the project
- `.windsurfrules`: Project-specific development rules and guidelines

## Hypothesis-Driven Development Process

### Before Starting Any Implementation
1. **State Current Understanding:** What do you currently know about the system?
2. **Identify Gaps:** What don't you know that you need to find out?
3. **Form Hypotheses:** What do you think will happen when you make changes?
4. **Define Success Criteria:** How will you know if your approach is working?
5. **Plan Validation:** How will you test your hypotheses?

### During Implementation
1. **Document Assumptions:** Write down what you're assuming at each step
2. **Validate Early:** Test hypotheses as soon as possible
3. **Reassess Plan:** After each major step, ask:
   - Is this approach still the right one?
   - What have I learned that changes my understanding?
   - Do I need to adjust the plan?
   - Will this actually solve the original problem?

### Plan Reassessment Checkpoints
- After reading documentation and understanding requirements
- After examining existing code and tests
- After implementing each major component
- Before finalizing the solution
- Before submitting/committing changes

### Example Hypothesis Format
```
HYPOTHESIS: [What I think will happen]
RATIONALE: [Why I think this based on current understanding]
VALIDATION: [How I will test this hypothesis]
RESULT: [What actually happened]
LEARNING: [What this taught me about the system]
NEXT_STEP: [How this changes my approach]
```

## Working Notes Template

Create `CURRENT_WORKING_NOTES.md` at project start:
```markdown
# Current Working Notes

## Task
[Brief description of what needs to be accomplished]

## Initial Hypotheses
- [Hypothesis 1]
- [Hypothesis 2]

## Plan
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Progress Log
### [Date/Time] - [Activity]
- [What was done]
- [What was learned]
- [How this affects the plan]

## Current Status
[Where things stand right now]

## Next Steps
[What to do next]
```