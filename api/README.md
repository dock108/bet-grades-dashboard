# Vercel Deployment for Grade Dashboard

This directory contains the necessary files for deploying the Grade Dashboard to Vercel.

## Files

- `index.py`: The entry point for the Vercel serverless function
- `requirements.txt`: Python dependencies required for the application

## Deployment

1. Install the Vercel CLI:
   ```
   npm install -g vercel
   ```

2. Login to Vercel:
   ```
   vercel login
   ```

3. Deploy to Vercel:
   ```
   vercel
   ```

4. For production deployment:
   ```
   vercel --prod
   ```

## Environment Variables

Make sure to set the following environment variables in your Vercel project settings:

- `SUPABASE_URL`: Your Supabase URL
- `SUPABASE_KEY`: Your Supabase API key
- `SECRET_KEY`: A random string used by Flask for security
- `FLASK_ENV`: Set to `production` for production deployment

### Generating a SECRET_KEY

You can generate a secure random string for your SECRET_KEY using Python:

```python
import secrets
print(secrets.token_hex(16))  # Outputs a 32-character random hex string
```

Run this command in your terminal and use the output as your SECRET_KEY.

If you don't set a SECRET_KEY, the application will use a default value ('dev'), but this is not recommended for production.

## Troubleshooting

If you encounter any issues with the deployment, check the Vercel logs:
```
vercel logs
```

For more information, refer to the [Vercel documentation](https://vercel.com/docs). 