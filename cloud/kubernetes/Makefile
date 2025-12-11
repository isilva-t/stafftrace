.PHONY: deploy status logs clean

deploy:
	kubectl apply -f backend-secret.yaml
	kubectl apply -f backend-deployment.yaml
	kubectl apply -f backend-service.yaml
	kubectl apply -f frontend-deployment.yaml
	kubectl apply -f frontend-service.yaml
	@echo "Waiting for services to get external IPs..."
	@kubectl get services --watch

status:
	@echo "=== Pods ==="
	@kubectl get pods
	@echo "\n=== Services ==="
	@kubectl get services
	@echo "\n=== Deployments ==="
	@kubectl get deployments

logs-backend:
	kubectl logs -f deployment/backend

logs-frontend:
	kubectl logs -f deployment/frontend

restart-backend:
	kubectl rollout restart deployment/backend

restart-frontend:
	kubectl rollout restart deployment/frontend

clean:
	kubectl delete -f frontend-service.yaml
	kubectl delete -f frontend-deployment.yaml
	kubectl delete -f backend-service.yaml
	kubectl delete -f backend-deployment.yaml
