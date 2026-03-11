Diagnose the accompy project setup and health.

Run the following checks:
1. `python -c "from accompy import verify_and_setup; verify_and_setup(interactive=False)"` — check dependencies
2. `python -m pytest tests/ -v --tb=short` — run tests
3. Check that all modules import cleanly: `python -c "import accompy; print(dir(accompy))"`

Report:
- Which system dependencies are present/missing (FluidSynth, SoundFont, MMA)
- Which tests pass/fail
- Any import errors or deprecation warnings
- Recommended next steps
