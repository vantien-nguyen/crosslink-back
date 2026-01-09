shell:
	docker exec -it django python crosslink/manage.py shell

makemigrations:
	docker exec django python crosslink/manage.py makemigrations

migrate:
	docker exec django python crosslink/manage.py migrate

format:
	docker exec django /bin/bash -c 'black . && isort crosslink/ && autoflake --remove-all-unused-imports --ignore-init-module-imports -i -r .'

test:
	docker exec django python crosslink/manage.py test crosslink/

init_data:
	docker exec django python crosslink/manage.py initialize_data

generate_fake_catalog:
	docker exec django python crosslink/manage.py generate_fake_catalog --shops 50 --products-per-shop 2000 --max-variants 4

