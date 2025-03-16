from app import create_app
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create the application instance
app = create_app()

if __name__ == '__main__':
    # Get port from environment variable or use 5002 as default
    port = int(os.environ.get('PORT', 5002))
    
    # Run the app with debug mode enabled
    app.run(
        debug=True,
        port=port,
        host='0.0.0.0'
    ) 