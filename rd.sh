docker stop sf2gs*
docker rm sf2gs*
docker rmi sf2gs_app-v0.0
docker compose -f docker-compose.yml -f docker-compose.caddy.yml up -d
docker compose logs -f
