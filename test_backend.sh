#!/bin/bash
# Test script to check if backend is responding

echo "Testing backend connectivity..."
echo ""

# Test root endpoint
echo "1. Testing root endpoint:"
curl -s http://localhost:8000/api | jq .
echo ""

# Test CORS preflight
echo "2. Testing CORS preflight:"
curl -i -X OPTIONS \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: POST" \
  http://localhost:8000/api/auth/login
echo ""

# Test registration endpoint
echo "3. Testing registration endpoint:"
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"testpass123"}'
echo ""

# Test login endpoint
echo "4. Testing login endpoint:"
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123"
echo ""

echo ""
echo "Tests complete!"
