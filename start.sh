#!/bin/bash
# Start backend
cd /home/user/marketing/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start frontend
cd /home/user/marketing/frontend
npm run dev &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID | Frontend PID: $FRONTEND_PID"
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"

wait
