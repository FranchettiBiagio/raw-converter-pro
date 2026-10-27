# Contributing to Franchetti Raw Converter Pro

Thank you for your interest in contributing! This document outlines the process and standards for contributing to this project.

---

## Code of Conduct

By participating, you agree to uphold our **Code of Conduct**:

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive criticism
- No harassment, discrimination, or offensive behavior
- Respect intellectual property rights

---

## Ways to Contribute

### 🐛 Bug Reports
- Search existing issues first
- Use the bug report template
- Include: OS version, steps to reproduce, expected vs actual behavior, logs/screenshots

### 💡 Feature Requests
- Check roadmap in CHANGELOG.md (Unreleased section)
- Describe use case and expected benefit
- Consider implementation complexity

### 🔧 Code Contributions
- Fork → Branch → Commit → PR
- Follow style guide below
- Add tests for new functionality
- Update documentation

### 📖 Documentation
- Fix typos, clarify explanations
- Add examples, screenshots
- Translate to other languages

### 🧪 Testing
- Test on different Windows versions
- Test with various RAW formats
- Report compatibility issues

---

## Development Setup

### Prerequisites
- Windows 10/11 (x64)
- Python 3.9+ (3.12 recommended)
- Git
- Code editor (VS Code recommended)

### Environment
```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/raw-converter-pro.git
cd raw-converter-pro

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # if exists

# Run from source
python main.py
```

### Development Dependencies
```bash
# Optional: for linting, formatting, testing
pip install black flake8 mypy pytest pytest-qt
```

---

## Code Style Guide

### Python (PEP 8 + Project Conventions)

```python
# Imports: stdlib → third-party → local
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import rawpy
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .converter import RawConverter  # local last

# Type hints required for public functions
def convert_single(
    self,
    raw_path: Path,
    output_dir: Path,
    max_dimension: int,
    jpg_quality: int,
    copyright_text: str,
    font_size: int,
    keep_original_name: bool,
    custom_prefix: str = ""
) -> Tuple[bool, str]:
    """Convert a single RAW file to JPEG with watermark.

    Args:
        raw_path: Path to source RAW file
        output_dir: Destination directory
        max_dimension: Long edge in pixels (0 = no resize)
        jpg_quality: JPEG quality 50-100
        copyright_text: Watermark text (empty = no watermark)
        font_size: Watermark font size in points
        keep_original_name: True to keep source filename
        custom_prefix: Prefix when not keeping original name

    Returns:
        Tuple of (success: bool, message: str)
    """
    pass
```

### Formatting
```bash
# Auto-format with Black (line length 100)
black --line-length 100 .

# Lint with flake8
flake8 --max-line-length=100 .

# Type check with mypy
mypy --strict .
```

### Naming Conventions
| Element | Style | Example |
|---------|-------|---------|
| Classes | PascalCase | `RawConverter`, `ConverterGUI` |
| Functions/Methods | snake_case | `convert_single`, `_add_watermark` |
| Variables | snake_case | `max_dimension`, `output_dir` |
| Constants | UPPER_SNAKE | `SUPPORTED_EXTENSIONS` |
| Private methods | _snake_case | `_worker_batch` |
| GUI widgets | descriptive | `btn_start`, `var_quality` |

### Documentation
- **Docstrings**: Google style for all public classes/methods
- **Comments**: Explain *why*, not *what*
- **Type hints**: Required for all function signatures

---

## Pull Request Process

### Before Submitting
1. **Run tests**: `python -m pytest` (when available)
2. **Lint**: `flake8 --max-line-length=100 .`
3. **Format**: `black --line-length 100 .`
4. **Type check**: `mypy --strict .`
4. **Manual test**: Run app, test your changes

### PR Requirements
- [ ] Clear title: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
- [ ] Description explains *what* and *why*
- [ ] References issue: `Closes #123` or `Relates to #123`
- [ ] Single logical change per PR
- [ ] No unrelated formatting changes
- [ ] Updated documentation if user-facing change
- [ ] Updated CHANGELOG.md (Unreleased section)

### Review Process
1. Automated checks pass (CI)
2. Maintainer review (1-2 business days)
3. Address feedback
4. Squash and merge (maintainer)

---

## Testing Guidelines

### Manual Testing Checklist
- [ ] App launches without errors
- [ ] File selection works (folder + files)
- [ ] Drag-and-drop area responds
- [ ] Output folder selection works
- [ ] All option controls function
- [ ] Conversion completes successfully
- [ ] Progress bar updates correctly
- [ ] Log shows color-coded entries
- [ ] Cancel button works mid-conversion
- [ ] Output JPEGs open correctly
- [ ] Watermark appears as expected
- [ ] No crashes on invalid files
- [ ] Memory stable during large batches

### Test Files
Maintain a test corpus in `tests/fixtures/`:
- Sample RAW files per format (small, <5 MB each)
- Edge cases: corrupted, zero-byte, unusual metadata
- Various resolutions and aspect ratios

### Automated Testing (Future)
```python
# tests/test_converter.py
import pytest
from pathlib import Path
from main import RawConverter

def test_convert_single_creates_jpg(tmp_path):
    converter = RawConverter()
    # ... test with fixture RAW
    assert output.exists()
```

---

## Release Process (Maintainers Only)

### Version Bump
```bash
# Update version in:
# - main.py (__version__)
# - build_exe.py (OUTPUT_EXE name)
# - version_info.txt (FileVersion, ProductVersion)
# - CHANGELOG.md (move Unreleased to versioned section)
```

### Build & Verify
```bash
python build_exe.py
# Test dist/FranchettiRawConverterPro.exe on clean VM
```

### Publish
1. Create Git tag: `git tag -a v2.55.0 -m "Release v2.55.0"`
2. Push tag: `git push origin v2.55.0`
3. GitHub Actions builds and creates Release
4. Verify Release artifacts
5. Update uptodown.dev listing
6. Announce

---

## Getting Help

- **GitHub Discussions**: General questions, ideas
- **GitHub Issues**: Bugs, feature requests
- **Email**: `dev@franchetti.dev` (maintainer contact)

---

## Recognition

Contributors are recognized in:
- GitHub Contributors graph
- Release notes
- About dialog (major contributions)

---

*Thank you for making Franchetti Raw Converter Pro better!*