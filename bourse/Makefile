SUBDIRS = docker/dashboard/ docker/analyzer

all: make_subdirs docker_up

make_subdirs:
	@for dir in $(SUBDIRS); do \
        echo "Making in $$dir"; \
        $(MAKE) -C $$dir; \
    done

docker_up:
	docker-compose -f docker/docker-compose.yml up

docker_down:
	docker-compose -f docker/docker-compose.yml down

clean:
	@for dir in $(SUBDIRS); do \
        $(MAKE) -C $$dir clean; \
    done