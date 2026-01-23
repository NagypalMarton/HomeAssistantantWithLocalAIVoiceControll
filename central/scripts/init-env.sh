#!/bin/bash
set -e

ENV_FILE="/app/.env"

echo "🔧 Initializing Central Backend environment..."

# Check if .env exists
if [ ! -f "$ENV_FILE" ]; then
    echo "📝 Creating .env file from template..."
    cp /app/.env.example "$ENV_FILE"
fi

# Generate JWT_SECRET if not set or default
JWT_SECRET=$(grep "^JWT_SECRET=" "$ENV_FILE" | cut -d '=' -f2)
if [ -z "$JWT_SECRET" ] || [ "$JWT_SECRET" = "your-256-bit-secret-change-this-in-production" ]; then
    echo "🔑 Generating JWT_SECRET..."
    NEW_JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    sed -i "s|^JWT_SECRET=.*|JWT_SECRET=$NEW_JWT_SECRET|" "$ENV_FILE"
    echo "✅ JWT_SECRET generated"
fi

# Generate ENCRYPTION_KEY if not set or default
ENCRYPTION_KEY=$(grep "^ENCRYPTION_KEY=" "$ENV_FILE" | cut -d '=' -f2)
if [ -z "$ENCRYPTION_KEY" ] || [ "$ENCRYPTION_KEY" = "your-encryption-key-change-in-production" ]; then
    echo "🔐 Generating ENCRYPTION_KEY..."
    NEW_ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    sed -i "s|^ENCRYPTION_KEY=.*|ENCRYPTION_KEY=$NEW_ENCRYPTION_KEY|" "$ENV_FILE"
    echo "✅ ENCRYPTION_KEY generated"
fi

echo "✅ Environment initialization complete!"
echo ""
echo "📋 Generated credentials saved to .env"
echo "⚠️  IMPORTANT: Backup your .env file for production use!"
echo ""
