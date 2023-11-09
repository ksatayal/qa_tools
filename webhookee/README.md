to build docker image

- docker build -t atayalan/webhookee .

to run a webhookd service

- docker run -d --name webhookd -p 9090:9090 atayalan/webhookee:latest


to unit test the webhookd service
- curl -X POST -u 'user1:mypass1' http://10.22.101.28:9090/callback/sessionInfo -H 'Content-Type: application/json' -d '{"pi":3.14}'
  should get {"status": "ok"}
- curl -X GET http://10.22.101.28:9090/callback/sessionInfo
  should get {"pi": 3.14}
