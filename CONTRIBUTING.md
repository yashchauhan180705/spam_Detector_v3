# Contributing to Spam Detector v3

Thank you for your interest in contributing to the Spam Detection System! This guide will help you get started.

## Getting Started

### Prerequisites

- Python 3.11+
- Docker Desktop
- Git
- A GitHub account

### Setting Up Development Environment

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/spam_Detector_v3.git
   cd spam_Detector_v3
   ```

2. **Create a Virtual Environment** (Optional for local testing)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Start Services with Docker**
   ```bash
   docker-compose up --build
   ```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `bugfix/` - Bug fixes
- `hotfix/` - Critical fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring

### 2. Make Your Changes

- Write clean, readable code
- Follow Python PEP 8 style guidelines
- Add comments for complex logic
- Update documentation as needed

### 3. Test Your Changes

#### Run Linting
```bash
pip install flake8
flake8 .
```

#### Test Docker Builds
```bash
# Test individual service
docker build -t test-model-service ./model-service

# Test all services
docker-compose build
docker-compose up
```

#### Manual Testing
- Access http://localhost:5000 for UI
- Test API endpoints manually
- Verify all services are healthy

### 4. Commit Your Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "Add feature: brief description of changes"
```

Good commit message examples:
- ✅ "Add email batch processing endpoint"
- ✅ "Fix model loading error in prediction service"
- ✅ "Update README with installation instructions"
- ❌ "Update files"
- ❌ "Fix bug"

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then:
1. Go to GitHub repository
2. Click "New Pull Request"
3. Select your branch
4. Fill in PR template
5. Submit for review

## Pull Request Guidelines

### PR Title
Use clear, descriptive titles:
- "Add feature: email batch processing"
- "Fix: model service container health check"
- "Docs: update CI/CD documentation"

### PR Description
Include:
- **What**: What changes were made
- **Why**: Why these changes are needed
- **How**: How the changes work
- **Testing**: How you tested the changes
- **Screenshots**: For UI changes

### PR Checklist
- [ ] Code follows project style guidelines
- [ ] Tests pass locally
- [ ] Docker builds succeed
- [ ] Documentation updated (if needed)
- [ ] No merge conflicts
- [ ] CI/CD checks pass

## CI/CD Process

All pull requests trigger automated checks:

### 1. Lint Check
- Runs flake8 on all Python code
- Must pass with no errors

### 2. Docker Build Test
- Builds all three services
- Tests docker-compose orchestration
- Verifies health checks

### 3. Code Quality
- Security vulnerability scanning
- Dependency checks
- Code complexity analysis

### How to Fix CI Failures

1. **Check the Actions tab** on your PR
2. **Click the failed job** to see logs
3. **Fix the issues** locally
4. **Push the fixes** (CI will re-run automatically)

Common issues:
- **Flake8 errors**: Fix code style issues
- **Docker build fails**: Check Dockerfile and dependencies
- **Health check fails**: Verify service starts correctly

## Code Style

### Python Style Guide
- Follow PEP 8
- Maximum line length: 127 characters
- Use meaningful variable names
- Add docstrings to functions and classes

### Example:
```python
def process_email(email_text: str) -> dict:
    """
    Process and classify an email as spam or ham.
    
    Args:
        email_text: The email content to process
        
    Returns:
        Dictionary with classification results
    """
    # Implementation
    pass
```

## Service-Specific Guidelines

### Model Service
- Keep model training logic separate
- Document model parameters
- Handle errors gracefully

### Prediction Service
- Optimize for performance
- Cache models when possible
- Validate input data

### UI Gateway Service
- Keep business logic minimal
- Focus on orchestration
- Provide clear error messages

## Testing

### Manual Testing
1. Start all services: `docker-compose up`
2. Test each endpoint
3. Verify logs for errors
4. Check health endpoints

### Health Checks
```bash
curl http://localhost:5001/health  # Model Service
curl http://localhost:5002/health  # Prediction Service
curl http://localhost:5000/        # UI Gateway
```

## Documentation

When adding features, update:
- README.md - User-facing documentation
- CI_CD.md - CI/CD related changes
- Code comments - Complex logic
- API documentation - New endpoints

## Getting Help

- **Issues**: Check existing issues or create a new one
- **Discussions**: Start a discussion for questions
- **PR Comments**: Ask questions in pull request comments

## Code Review Process

1. **Automated checks** run first (CI/CD)
2. **Maintainer review** - usually within 2-3 days
3. **Address feedback** - make requested changes
4. **Approval** - maintainer approves PR
5. **Merge** - PR merged to main branch

## After Your PR is Merged

1. **Delete your branch** (optional)
   ```bash
   git branch -d feature/your-feature-name
   git push origin --delete feature/your-feature-name
   ```

2. **Update your fork**
   ```bash
   git checkout main
   git pull upstream main
   git push origin main
   ```

3. **Celebrate!** 🎉 You're a contributor!

## Best Practices

### Do's ✅
- Write small, focused PRs
- Test thoroughly before submitting
- Keep commits atomic and logical
- Respond to review comments promptly
- Be respectful and professional

### Don'ts ❌
- Don't mix unrelated changes
- Don't commit sensitive data
- Don't ignore CI failures
- Don't break existing functionality
- Don't submit without testing

## Security

### Reporting Vulnerabilities
- **DO NOT** open public issues for security vulnerabilities
- Email maintainers directly
- Provide detailed information
- Allow time for fixes before disclosure

### Secure Coding
- Never commit secrets or API keys
- Use environment variables for sensitive data
- Validate all user input
- Follow security best practices

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## Questions?

If you have questions not covered here:
1. Check existing documentation
2. Search closed issues and PRs
3. Open a new discussion
4. Ask in your pull request

Thank you for contributing! 🚀
