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

## 🧠 MANDATORY PLANNING PROCESS FOR ALL NON-TRIVIAL TASKS

**BEFORE taking any action on complex requests, you MUST:**

1. **State your understanding**: "I understand you want me to [specific interpretation of request]"

2. **Draft explicit plan**: List specific actions you will take, in order

3. **Perform critical self-review**: Ask and answer these questions:
   - What assumptions am I making?
   - Does this plan do exactly what was requested, no more, no less?
   - What files/systems will be affected beyond what was mentioned?
   - What could go wrong or have unintended consequences?
   - Is there a simpler approach that achieves the same goal?

4. **Revise plan if needed**: Based on critical review, adjust approach

5. **Present final plan**: Show user the plan before executing

6. **Execute only after plan review**: Proceed step by step

**This process is MANDATORY for any task that:**
- Affects multiple files or systems
- Could have unintended side effects
- Involves git operations beyond simple status checks
- Requires interpretation of ambiguous instructions
- Could impact more than explicitly requested

**Skip this only for truly trivial tasks** (reading single files, simple status checks, basic calculations).

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

## Memory & Learning Process

### Critical Learning Guidelines
- **Continue until you are Done Done with a task.** A PR is not considered done until:
  - All task requirements are satisfied
  - All checks/builds are passing
  - All critical feedback has been addressed
- At the beginning of a new task given by a human, write down the task verbatim in a dedicated file
- Consider all feedback from humans critical
- Apply your own judgement on feedback from other LLMs - they may be wrong
- Make sure that you have a checklist for when you consider yourself to be DONE DONE and review it
- Do not stop unless asked to or DONE DONE
- If a PR is undergoing checks/builds, sleep until they are done; it may take up to several minutes so multiple cycles may be necessary