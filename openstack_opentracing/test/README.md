# openstack-opentracing Testing
This package has the ingredients to test the jaeger_middleware using a flask wsgi app.

## How to

* run
```bash 
docker run --name jaeger  -p 5775:5775/udp -p 5778:5778 -p 14268:14268 -p 6831:6831/udp -p 6832:6832/udp -p 16686:16686 jaegertracing/all-in-one:latest
```

* configure 'test-paste*.ini' and fix the corresponding ports in the paste ini files.
* Run 'server1', 'server2', 'server3'
* Wait for a minute (the time for sampling)
* Run test-server
* connect to http://localhost:6831 and check the Jaeger dashboard


## TODO

Lots, but most important make this automated
