#!/bin/bash

# Wait for RabbitMQ to be ready
until timeout 2 bash -c "echo > /dev/tcp/rabbitmq/5672" >/dev/null 2>&1; do
  echo "Waiting for RabbitMQ..."
  sleep 2
done

# Start services with host binding
cd /app
python services/api_gateway/apiv1.py &
python services/user_service/v1/appv1.py &
python services/user_service/v2/app_v2.py &
python services/order_service/Order_app.py &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?