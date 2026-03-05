"""Root conftest."""

import os

# Disable setup check during CI/tests
os.environ["ACCOMPY_SKIP_SETUP_CHECK"] = "1"
