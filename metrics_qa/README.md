command to bring to containers (metrics_qa/metrics_cache)
- docker-compose up --build -d metrics

command to shutdown metrics_qa/metrics_cache containers
- docker-compose down

command to summarize metics data
- docker exec -it metricsa_qa summarize.py -h
- docker exec -it metricsa_qa summarize.py --dut vm33 --since "2023-10-31T00:11:22Z"
