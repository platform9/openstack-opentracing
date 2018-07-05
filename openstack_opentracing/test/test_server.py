
import requests, time
from server1 import start_server1
from server2 import start_server2
from multiprocessing import Process

def setup_test():
    p1 = Process(target=start_server1)
    p1.start()
    p2 = Process(target=start_server2)
    p2.start()
    # Wait for the services to come up and listen
    time.sleep(100)
    return (p1, p2)

def join(p1, p2):
    p1.join()
    p2.join()


def perform_tests():
    for count in range(0, 1):
        resp = requests.get('http://127.0.0.1:2326/v1/forward')
        if not resp.status_code == 200:
            print "Error %s " % str(resp.status_code)
        else:
            print "Passed Test: %s" % str(resp.text)


if __name__ == "__main__":
    p1, p2 = setup_test()
    perform_tests()
    join(p1, p2)

