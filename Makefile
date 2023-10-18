.SILENT:

rebuild:
	docker-compose up --build
stop:
	docker-compose down
run-local:
	go run cmd/app/main.go
run-deploy:
	sudo docker-compose up
