# Deploying Grade Dashboard to Vercel

This guide provides instructions for deploying the Grade Dashboard application to Vercel.

## Prerequisites

- [Vercel account](https://vercel.com/signup)
- [Vercel CLI](https://vercel.com/docs/cli) (optional for command-line deployment)
- [Supabase account](https://supabase.com/) (for database)

## Deployment Steps

### 1. Prepare Your Project

The project is already set up for Vercel deployment with the following files:

- `vercel.json`: Configuration for Vercel
- `api/index.py`: Entry point for the Vercel serverless function
- `api/requirements.txt`: Python dependencies
- `.vercelignore`: Files to exclude from deployment

### 2. Set Up Environment Variables

You'll need to set the following environment variables in your Vercel project:

- `SUPABASE_URL`: Your Supabase URL
- `SUPABASE_KEY`: Your Supabase API key
- `SECRET_KEY`: A random string used by Flask for security (see below for how to generate one)
- `FLASK_ENV`: Set to `production` for production deployment

#### Generating a SECRET_KEY

You can generate a secure random string for your SECRET_KEY using Python:

```python
import secrets
print(secrets.token_hex(16))  # Outputs a 32-character random hex string
```

Run this command in your terminal and use the output as your SECRET_KEY.

If you don't set a SECRET_KEY, the application will use a default value ('dev'), but this is not recommended for production.

#### About FLASK_ENV

The FLASK_ENV variable determines which configuration to use. If not set, it defaults to 'development'. For production deployment, set it to 'production'.

### 3. Deploy to Vercel

#### Option 1: Using the Vercel Dashboard

1. Push your code to a Git repository (GitHub, GitLab, or Bitbucket)
2. Log in to your Vercel account
3. Click "New Project"
4. Import your repository
5. Configure the project:
   - Set the Framework Preset to "Other"
   - Set the Build Command to `pip install -r api/requirements.txt`
   - Set the Output Directory to `api`
6. Add the environment variables
7. Click "Deploy"

#### Option 2: Using the Vercel CLI

1. Install the Vercel CLI:
   ```
   npm install -g vercel
   ```

2. Log in to Vercel:
   ```
   vercel login
   ```

3. Deploy from the project directory:
   ```
   vercel
   ```

4. Follow the prompts to configure your project
5. Set up environment variables:
   ```
   vercel env add SUPABASE_URL
   vercel env add SUPABASE_KEY
   vercel env add SECRET_KEY
   vercel env add FLASK_ENV
   ```

6. Deploy to production:
   ```
   vercel --prod
   ```

### 4. Verify Deployment

1. Once deployed, Vercel will provide a URL for your application
2. Visit the URL to ensure the application is working correctly
3. Check the Vercel logs if you encounter any issues:
   ```
   vercel logs
   ```

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**: Ensure all required environment variables are set in your Vercel project settings.

2. **Import Errors**: If you see import errors, check that all dependencies are listed in `api/requirements.txt`.

3. **Database Connection Issues**: Verify your Supabase credentials and ensure your IP is allowed in Supabase settings.

4. **Timeout Errors**: Vercel serverless functions have a timeout limit. If your application takes too long to start, consider optimizing your code.

### Getting Help

- Check the [Vercel documentation](https://vercel.com/docs)
- Review the [Vercel Python runtime documentation](https://vercel.com/docs/functions/runtimes/python)
- Consult the [Supabase documentation](https://supabase.com/docs) for database issues

## Updating Your Deployment

To update your deployment after making changes:

1. Push your changes to your Git repository (if using Git integration)
2. Vercel will automatically redeploy your application

Or, using the CLI:

```
vercel --prod
``` 