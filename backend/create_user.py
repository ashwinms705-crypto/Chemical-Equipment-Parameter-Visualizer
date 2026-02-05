from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

# Create test user if not exists
if not User.objects.filter(username='admin').exists():
    user = User.objects.create_superuser('admin', 'admin@example.com', 'password123')
    Token.objects.create(user=user)
    print("Created superuser 'admin' with password 'password123'")
else:
    print("Superuser 'admin' already exists")
