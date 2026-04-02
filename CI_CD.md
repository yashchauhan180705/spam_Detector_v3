# CI/CD Documentation

This document describes the CI/CD pipelines configured for the Spam Detector v3 project.

## Overview

The project uses GitHub Actions for continuous integration and continuous deployment. The workflows are designed to ensure code quality, build reliability, and secure deployments.

## Workflows

### 1. CI Pipeline (`ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Manual workflow dispatch

**Jobs:**

#### Lint
- Runs `flake8` to check Python code quality
- Checks for syntax errors and undefined names
- Provides code complexity and line length analysis

#### Docker Build Test
- Tests Docker builds for all three services:
  - `model-service`
  - `prediction-service`
  - `ui-gateway-service`
- Uses Docker BuildKit for efficient caching
- Runs in parallel for faster feedback

#### Docker Compose Integration Test
- Builds all services using docker-compose
- Starts all services
- Performs health checks on each service
- Ensures all services can communicate properly
- Shows logs on failure for debugging

**Status Badge:**
```markdown
![CI Pipeline](https://github.com/yashchauhan180705/spam_Detector_v3/actions/workflows/ci.yml/badge.svg)
```

### 2. Docker Image Build and Push (`docker-publish.yml`)

**Triggers:**
- Push to `main` branch
- Version tags (v*.*.*)
- Release publications
- Manual workflow dispatch

**Features:**
- Builds and pushes Docker images to GitHub Container Registry (ghcr.io)
- Creates multi-architecture images (amd64, arm64)
- Automatic tagging:
  - `latest` for main branch
  - Semantic versioning tags (v1.0.0, v1.0, v1)
  - Branch names
  - Git SHA
- Uses layer caching for faster builds

**Images Published:**
- `ghcr.io/<owner>/spam-detector-model-service`
- `ghcr.io/<owner>/spam-detector-prediction-service`
- `ghcr.io/<owner>/spam-detector-ui-gateway-service`

**Status Badge:**
```markdown
![Docker Publish](https://github.com/yashchauhan180705/spam_Detector_v3/actions/workflows/docker-publish.yml/badge.svg)
```

### 3. Deployment (`deploy.yml`)

**Triggers:**
- Manual workflow dispatch (choose environment)
- Release publications (auto-deploys to production)

**Environments:**
- Staging
- Production

**Current Status:**
This workflow is configured as a template and requires additional setup for actual deployments.

**To Enable Deployments:**

1. Configure GitHub Secrets:
   ```
   DEPLOY_HOST - Deployment server hostname
   DEPLOY_USER - SSH username
   DEPLOY_SSH_KEY - SSH private key
   ```

2. Configure GitHub Environments:
   - Go to Repository Settings → Environments
   - Create `staging` and `production` environments
   - Add protection rules (required reviewers, etc.)

3. Uncomment the `deploy-to-server` job in `deploy.yml`

4. Update the deployment script with your server paths

**Status Badge:**
```markdown
![Deploy](https://github.com/yashchauhan180705/spam_Detector_v3/actions/workflows/deploy.yml/badge.svg)
```

### 4. Code Quality (`code-quality.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Manual workflow dispatch

**Jobs:**

#### Security Scan
- Scans filesystem for vulnerabilities using Trivy
- Uploads results to GitHub Security tab
- Checks for critical and high severity issues

#### Dependency Check
- Scans Python dependencies using Safety
- Checks each service's requirements.txt
- Reports known vulnerabilities

#### Docker Security Scan
- Scans built Docker images for vulnerabilities
- Uses Trivy for comprehensive security analysis
- Checks all three services

#### Code Quality Analysis
- Runs pylint for code quality metrics
- Calculates cyclomatic complexity using radon
- Provides maintainability index

**Status Badge:**
```markdown
![Code Quality](https://github.com/yashchauhan180705/spam_Detector_v3/actions/workflows/code-quality.yml/badge.svg)
```

## Configuration Files

### `.flake8`
Configures flake8 linting rules:
- Max line length: 127 characters
- Max complexity: 10
- Excludes common directories (venv, __pycache__, etc.)

## Using the CI/CD System

### For Developers

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make Changes and Commit**
   ```bash
   git add .
   git commit -m "Add new feature"
   ```

3. **Push and Create PR**
   ```bash
   git push origin feature/my-feature
   ```
   - CI pipeline will run automatically
   - Check the Actions tab for results
   - Fix any issues before merging

4. **Merge to Main**
   - Once approved and CI passes, merge to main
   - Docker images will be built and pushed automatically

### Running Workflows Manually

1. Go to **Actions** tab in GitHub
2. Select the workflow you want to run
3. Click **Run workflow**
4. Choose branch and options
5. Click **Run workflow** button

### Monitoring Builds

1. Go to **Actions** tab
2. Click on a workflow run to see details
3. Click on individual jobs to see logs
4. Download artifacts if available

## Best Practices

### Code Quality
- Run `flake8` locally before pushing:
  ```bash
  pip install flake8
  flake8 .
  ```

### Docker Testing
- Test Docker builds locally:
  ```bash
  docker-compose build
  docker-compose up
  ```

### Security
- Keep dependencies up to date
- Review security scan results regularly
- Fix critical vulnerabilities promptly

### Releases
- Use semantic versioning (v1.0.0)
- Create releases through GitHub UI
- Add release notes describing changes

## Troubleshooting

### Build Failures

**Docker build fails:**
- Check Dockerfile syntax
- Verify all dependencies are in requirements.txt
- Check for network issues downloading packages

**Lint failures:**
- Run flake8 locally to see specific issues
- Fix code style problems
- Update .flake8 if rules need adjustment

**Health check failures:**
- Check service logs in the workflow
- Verify services start correctly locally
- Increase wait times if services need more startup time

### Deployment Issues

**Permission errors:**
- Verify GitHub Actions has correct permissions
- Check repository settings → Actions → General
- Ensure GITHUB_TOKEN has package write permission

**Image push failures:**
- Verify you're logged into ghcr.io
- Check package visibility settings
- Ensure repository name is correct

## Maintenance

### Updating Workflows

1. Edit workflow files in `.github/workflows/`
2. Test changes in a feature branch
3. Review workflow run results
4. Merge when verified working

### Updating Dependencies

1. Update requirements.txt files
2. Test locally with Docker
3. Push and verify CI passes
4. Monitor for security alerts

### Adding New Services

1. Create service directory with Dockerfile
2. Add to docker-compose.yml
3. Update CI workflows to include new service
4. Test entire pipeline

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/actions)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [GitHub Container Registry](https://docs.github.com/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Semantic Versioning](https://semver.org/)

## Support

For issues with CI/CD:
1. Check workflow logs in Actions tab
2. Review this documentation
3. Open an issue with relevant logs
4. Tag with `ci/cd` label
