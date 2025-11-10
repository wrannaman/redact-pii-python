# PyPI Trusted Publisher Setup

## Why Use Trusted Publishers?

✅ **More Secure** - No long-lived API tokens to manage  
✅ **Automatic Token Rotation** - Short-lived tokens generated automatically  
✅ **Better Security Posture** - OIDC-based authentication  
✅ **No Secrets to Manage** - No need to store `PYPI_API_TOKEN` in GitHub secrets

## Setup Instructions

### 1. Register Pending Publisher on PyPI

Go to: https://pypi.org/manage/account/publishing/

Click **"Add a new pending publisher"** and fill in:

- **PyPI Project Name:** `redactpii`
- **Owner:** `wrannaman` (your GitHub username)
- **Repository name:** `redact-pii-python`
- **Workflow name:** `publish.yml` (the filename in `.github/workflows/`)
- **Environment name:** `pypi` (optional but recommended - see setup below)

### 2. Create GitHub Environment (Optional but Recommended)

For extra security, create a `pypi` environment in your GitHub repository:

1. Go to your repository on GitHub
2. Click **Settings** → **Environments**
3. Click **New environment**
4. Name it: `pypi`
5. (Optional) Add protection rules:
   - **Required reviewers**: Add yourself or team members who should approve releases
   - **Deployment branches**: Restrict to `main` branch only
   - **Wait timer**: Add a delay before deployment (optional)

This adds an extra layer of protection - releases will require approval if you set up reviewers.

### 3. Verify Workflow is Updated

The workflow (`.github/workflows/publish.yml`) has been updated to use OIDC:
- Uses `pypa/gh-action-pypi-publish@release/v1` action
- Includes `id-token: write` permission
- Uses `environment: pypi` (optional - remove this line if you don't create the environment)
- No longer requires `PYPI_API_TOKEN` secret

### 3. Create Your First Release

Once the pending publisher is registered:

1. Create a new release on GitHub:
   - Go to **Releases** → **Create a new release**
   - Tag: `v1.0.0`
   - Title: `v1.0.0 - Initial Release`
   - Description: (see GITHUB_SETUP.md for template)

2. The workflow will automatically:
   - Build the package
   - Publish to PyPI using OIDC authentication
   - No manual token management needed!

## Important Notes

⚠️ **Project Name Reservation**: Registering a "pending" publisher does NOT reserve the project name. You should create the project on PyPI first if you want to reserve the name, or publish quickly after setting up the publisher.

⚠️ **First Publish**: The first time you publish, PyPI will create the project automatically if it doesn't exist.

## Alternative: Manual Token Setup (Not Recommended)

If you prefer the old token-based approach (not recommended):

1. Create API token on PyPI: https://pypi.org/manage/account/token/
2. Add secret to GitHub: Settings → Secrets → Actions → `PYPI_API_TOKEN`
3. Revert the workflow to use `TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}`

But **trusted publishers are the recommended approach** for better security!

