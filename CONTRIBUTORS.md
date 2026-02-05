# Contributors

Special thanks to everyone who has contributed to this project!

## Core Development
- **[@NexusBT2026](https://github.com/NexusBT2026)** - Project creator and maintainer

## Community Contributors

### [@arosstale](https://github.com/arosstale) (Artale)
- **Future Project Ideas**: Contributed innovative concepts for indicator extensions
- **Production Verification**: Tested v0.0.7 with V8 Strategy achieving exceptional results:
  - Sharpe Ratio: 4.5+ (improved from 4.13)
  - Win Rate: 80%+ (improved from 73%)  
  - Returns: 500%+ annual (improved from 400%)
- **Code Quality Review**: Comprehensive PyLint review improving score from 9.79 to 9.98
  - Exception handling improvements (6 fixes)
  - Unused variable cleanup (3 fixes)
  - Code documentation enhancements
- Independent validation proving production-grade reliability

---

## How to Contribute

We welcome contributions! Here's how to get started:

### 1. Fork and Clone
```bash
git clone https://github.com/YOUR_USERNAME/liquidator_indicator.git
cd liquidator_indicator
```

### 2. Set Up Development Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
pip install pytest pytest-timeout pylint
```

### 3. Make Your Changes
```bash
# Create a feature branch
git checkout -b feature/amazing-feature

# Make your changes
# ...

# Run tests
pytest tests/ -v -m "not live"

# Run linter
pylint src/liquidator_indicator --disable=C,R
```

### 4. Submit Pull Request
```bash
# Commit your changes
git add .
git commit -m "Add amazing feature"

# Push to your fork
git push origin feature/amazing-feature

# Open a Pull Request on GitHub
```

### Contribution Guidelines

**Code Quality**
- Maintain PyLint score above 9.5
- Use specific exception types (not broad `except Exception`)
- Add type hints where appropriate
- Include docstrings for public methods

**Testing**
- All tests must pass (61/61)
- Add tests for new features
- Maintain backward compatibility
- Test with and without numba

**Documentation**
- Update README.md if adding features
- Add examples for new functionality
- Update CHANGELOG.md with your changes
- Include inline comments for complex logic

**Code Style**
- Follow PEP 8
- Use meaningful variable names
- Keep functions under 50 lines when possible
- Prefer clarity over cleverness

### Types of Contributions

**Bug Fixes**
- Fix failing tests
- Resolve edge cases
- Improve error handling

**New Features**
- Additional exchange support
- New zone detection patterns
- Performance optimizations

**Documentation**
- Improve guides
- Add usage examples
- Fix typos or clarify instructions

**Testing**
- Increase test coverage
- Add edge case tests
- Performance benchmarks

**Code Quality**
- Refactoring for clarity
- Performance improvements
- Security enhancements

### Review Process

1. **Automated Checks**: GitHub Actions runs tests and linting
2. **Code Review**: Maintainer reviews code quality and design
3. **Testing**: Verify all tests pass (including backward compatibility)
4. **Merge**: PR merged if approved

### Recognition

Contributors are recognized in:
- CONTRIBUTORS.md (this file)
- CHANGELOG.md release notes
- GitHub release descriptions
- Package metadata

### Questions?

- **General**: Open a GitHub issue
- **Security**: See SECURITY.md for private reporting
- **Ideas**: Start a GitHub discussion

---

## Code of Conduct

Be respectful, constructive, and professional. We're building tools that handle real trading capital - quality and reliability matter.

**Repository**: https://github.com/NexusBT2026/liquidator_indicator  
**License**: MIT
