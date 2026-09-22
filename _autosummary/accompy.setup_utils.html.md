# accompy.setup_utils

Setup and configuration utilities for accompy.

This module provides automatic setup, verification, and troubleshooting
tools to help users get accompy configured correctly.

### Functions

| [`diagnose_issues`](#accompy.setup_utils.diagnose_issues)()                         | Diagnose common setup issues and provide solutions.    |
|--------------------------------------------------------------------------------------------|--------------------------------------------------------|
| [`print_diagnostic_report`](#accompy.setup_utils.print_diagnostic_report)()                 | Print a comprehensive diagnostic report.               |
| [`setup_soundfont`](#accompy.setup_utils.setup_soundfont)([force])                  | Download and configure a SoundFont file.               |
| [`verify_and_setup`](#accompy.setup_utils.verify_and_setup)([interactive, auto_fix]) | Verify all dependencies and optionally auto-configure. |

### accompy.setup_utils.diagnose_issues()

Diagnose common setup issues and provide solutions.

* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`Tuple`](https://docs.python.org/3/library/typing.html#typing.Tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]]
* **Returns:**
  List of (issue, description, solution) tuples

Example:

```default
from accompy.setup_utils import diagnose_issues
for issue, desc, solution in diagnose_issues():
    print(f"{issue}: {desc}")
    print(f"Solution: {solution}")
```

### accompy.setup_utils.print_diagnostic_report()

Print a comprehensive diagnostic report.

### accompy.setup_utils.setup_soundfont(force=False)

Download and configure a SoundFont file.

* **Parameters:**
  **force** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True, download even if a SoundFont already exists
* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)
* **Returns:**
  True if successful, False otherwise

Example:

```default
from accompy.setup_utils import setup_soundfont
if setup_soundfont():
    print("SoundFont configured successfully!")
```

### accompy.setup_utils.verify_and_setup(interactive=True, auto_fix=False)

Verify all dependencies and optionally auto-configure.

* **Parameters:**
  * **interactive** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True, prompt user for permission before making changes
  * **auto_fix** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True and interactive=False, automatically fix issues without prompting
* **Return type:**
  [`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`bool`](https://docs.python.org/3/builtins/functions.html#bool)]
* **Returns:**
  Dict mapping dependency name to whether it’s available

### Example

```pycon
>>> from accompy.setup_utils import verify_and_setup
>>> status = verify_and_setup(interactive=False)
>>> if all(status.values()):
...     print("Ready to use!")
```
