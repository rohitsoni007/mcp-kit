# Contributing to MCP Gearbox

Thank you for your interest in contributing to MCP Gearbox! This document provides guidelines and information for contributors.

## Development Setup

### Prerequisites

- Python 3.11 +
- [uv](https://docs.astral.sh/uv/) package manager
- Git

### Setting Up Your Development Environment

1. **Fork and clone the repository:**
```bash
git clone https://github.com/rohitsoni007/mcp-kit.git
cd mcp-kit
```

2. **Create a virtual environment:**
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install development dependencies:**
```bash
uv pip install -e ".[dev]"
```

4. **Install pre-commit hooks:**
```bash
pre-commit install
```

## Development Workflow

### Running Tests

Run the full test suite:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=mcp_kit --cov-report=html
```

Run specific test files:
```bash
pytest tests/test_cli.py
```

Run tests with verbose output:
```bash
pytest -v
```

### Code Quality

**Format code with Black:**
```bash
black src tests
```

**Type checking with mypy:**
```bash
mypy src/mcp_kit
```

**Run pre-commit checks:**
```bash
pre-commit run --all-files
```

### Testing Your Changes

1. **Install your development version:**
```bash
uv pip install -e .
```

2. **Test the CLI commands:**
```bash
mcp --version

```

3. **Test cross-platform compatibility:**
   - Test on different operating systems if possible
   - Test with different terminal environments
   - Test with different Python versions (3.11, 3.12, 3.13)

## Code Style and Standards

### Python Code Style

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use [Black](https://black.readthedocs.io/) for code formatting (line length: 88)
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes

### Code Organization

- Keep functions focused and single-purpose
- Use descriptive variable and function names
- Group related functionality into appropriate modules
- Follow the existing project structure

### Error Handling

- Use specific exception types rather than generic `Exception`
- Provide helpful error messages with actionable suggestions
- Log errors appropriately using the logging system
- Handle edge cases gracefully

### Testing

- Write tests for all new functionality
- Maintain or improve test coverage
- Use descriptive test names that explain what is being tested
- Test both success and failure scenarios
- Mock external dependencies (API calls, file system operations)

## Submitting Changes

### Before Submitting

1. **Ensure all tests pass:**
```bash
pytest
```

2. **Check code formatting:**
```bash
black --check src tests
```

3. **Run type checking:**
```bash
mypy src/mcp_cli
```

4. **Update documentation if needed:**
   - Update README.md for user-facing changes
   - Update docstrings for API changes
   - Add or update examples

### Pull Request Process

1. **Create a feature branch:**
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes and commit:**
```bash
git add .
git commit -m "Add feature: description of your changes"
```

3. **Push to your fork:**
```bash
git push origin feature/your-feature-name
```

4. **Create a pull request:**
   - Use a clear, descriptive title
   - Provide a detailed description of your changes
   - Reference any related issues
   - Include screenshots for UI changes

### Pull Request Guidelines

- **Title:** Use a clear, descriptive title that summarizes the change
- **Description:** Explain what the change does and why it's needed
- **Testing:** Describe how you tested your changes
- **Breaking Changes:** Clearly mark any breaking changes
- **Documentation:** Update relevant documentation

## Types of Contributions

### Bug Reports

When reporting bugs, please include:
- Your operating system and Python version
- Steps to reproduce the issue
- Expected vs. actual behavior
- Error messages and stack traces
- Debug logs (use `--debug --log-file debug.log`)

### Feature Requests

When requesting features:
- Explain the use case and why it's valuable
- Provide examples of how it would be used
- Consider backward compatibility
- Be open to discussion about implementation approaches

### Code Contributions

We welcome contributions for:
- Bug fixes
- New features
- Performance improvements
- Documentation improvements
- Test coverage improvements
- Cross-platform compatibility fixes

### Documentation Contributions

Help improve documentation by:
- Fixing typos and grammar
- Adding examples and use cases
- Improving clarity and organization
- Adding troubleshooting information
- Translating documentation

## Development Guidelines

### API Design

- Keep the CLI interface simple and intuitive
- Follow Unix command-line conventions
- Provide helpful error messages
- Support common workflows efficiently

### Performance

- Minimize API calls and cache responses appropriately
- Handle large server lists efficiently
- Provide progress indicators for long operations
- Optimize file I/O operations

### Security

- Validate all user inputs
- Sanitize file paths to prevent directory traversal
- Handle sensitive information appropriately
- Follow security best practices for HTTP requests

### Accessibility

- Ensure the CLI works with screen readers
- Provide alternative text for visual elements
- Support keyboard-only navigation
- Test with different terminal configurations

## Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR:** Breaking changes
- **MINOR:** New features (backward compatible)
- **PATCH:** Bug fixes (backward compatible)

### Release Checklist

1. Update version in `src/mcp_kit/__init__.py`
2. Update `CHANGELOG.md` with release notes
3. Ensure all tests pass
4. Create a release tag
5. Update documentation if needed

## Getting Help

### Communication Channels

- **GitHub Issues:** For bug reports and feature requests
- **GitHub Discussions:** For questions and general discussion
- **Pull Request Comments:** For code review discussions

### Development Questions

If you have questions about:
- Code architecture or design decisions
- Testing strategies
- Implementation approaches
- Development environment setup

Feel free to:
- Open a GitHub Discussion
- Comment on relevant issues
- Ask in pull request comments

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different viewpoints and experiences

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Personal attacks
- Publishing private information without consent

### Enforcement

Project maintainers are responsible for clarifying standards and will take appropriate action in response to unacceptable behavior.

## Recognition

Contributors will be recognized in:
- The project's contributor list
- Release notes for significant contributions
- Special recognition for major features or improvements

Thank you for contributing to MCP Gearbox!
