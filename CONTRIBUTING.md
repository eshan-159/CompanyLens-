# Contributing to CompanyLens

First off, thank you for considering contributing to CompanyLens! 🎉

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)

## Code of Conduct

This project adheres to a simple code of conduct: Be kind, be respectful, be professional.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- **Clear title and description**
- **Steps to reproduce** the problem
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, Node.js version)
- **Error logs** if applicable

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear title and description**
- **Use case** - why is this enhancement useful?
- **Proposed solution** or implementation approach
- **Alternative solutions** you've considered

### Pull Requests

We love pull requests! Here's the process:

1. **Fork** the repo and create your branch from `main`
2. **Make your changes** following our style guidelines
3. **Test** your changes thoroughly
4. **Update documentation** if needed
5. **Submit** your pull request

## Development Setup

### Prerequisites

- Python 3.8+
- Node.js 18+
- Git

### Setup Steps

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/CompanyLens-.git
cd CompanyLens-

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Install Node.js dependencies
cd backend
npm install
cd ..

# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Run tests
python main.py -i companies_sample.csv -o test_output.xlsx
```

### Running the Development Server

```bash
# Terminal 1: Start backend server
cd backend
npm start

# Terminal 2: Run Python tests
python main.py --input test.csv --output test.xlsx --verbose
```

## Pull Request Process

1. **Update the README.md** with details of changes if applicable
2. **Update the requirements.txt** if you add Python dependencies
3. **Update package.json** if you add Node.js dependencies
4. **Follow the code style** guidelines below
5. **Ensure all tests pass** before submitting
6. **Write clear commit messages** (see below)

### Commit Message Guidelines

We follow conventional commits:

```
feat: add support for custom AI models
fix: resolve timeout issue in web crawler
docs: update installation instructions
style: format code with black
refactor: simplify search logic
test: add unit tests for summarizer
chore: update dependencies
```

## Style Guidelines

### Python Code Style

- **PEP 8** compliance (use `black` for formatting)
- **Type hints** where appropriate
- **Docstrings** for all public functions
- **Meaningful variable names**

```python
def find_company_website(company_name: str) -> Optional[str]:
    """Search for company website using DuckDuckGo.
    
    Args:
        company_name: Name of the company to search
        
    Returns:
        URL of the official website, or None if not found
    """
    pass
```

### JavaScript Code Style

- **ES6+** syntax
- **Consistent formatting** (use Prettier)
- **Clear variable names**
- **Comments** for complex logic

### Documentation

- **Clear and concise** writing
- **Code examples** where helpful
- **Up-to-date** with latest changes
- **Proper markdown formatting**

## Testing

Before submitting a PR, ensure:

1. Your code works with sample data
2. No new errors or warnings
3. Existing functionality still works
4. Edge cases are handled

## Questions?

Feel free to:
- Open an issue for questions
- Tag maintainers in discussions
- Reach out via GitHub

## Recognition

Contributors will be recognized in:
- GitHub contributors page
- Release notes (for significant contributions)
- README acknowledgments

---

**Thank you for making CompanyLens better!** 🚀
