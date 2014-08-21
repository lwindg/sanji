import os
import sys
import json
from random import randint
from Queue import Queue
from threading import Thread
from threading import Lock
from threading import Event

try:
    sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../../')
    from sanji.connection.connection import Connection
except ImportError as e:
    print e
    print "Please check the python PATH for import test module. (%s)" \
        % __file__
    exit(1)


class ConnectionMockup(Connection):

    def __init__(self):
        self.message_queue = Queue()
        self.publish_onfly = dict()
        self.tunnel = "mockup_tunnel"
        self.disconnect_event = Event()
        self._publish_lock = Lock()
        self.on_publish = None
        self.on_message = None

    def __onpublish(self):
        while self.disconnect_event.is_set() is False:
            arrival = []
            self._publish_lock.acquire()
            for mid in self.publish_onfly:
                arrival.append(mid)
            self.publish_onfly = dict()
            self._publish_lock.release()

            def pub(mid):
                self.on_publish(self, mid)

            map(pub, arrival)

    def __onmessage(self):
        while self.disconnect_event.is_set() is False:
            while self.message_queue.empty() is False:
                message = self.message_queue.get()
                self.on_message(self, message)

    def connect(self):
        self.__t_onpublish = Thread(target=self.__onpublish)
        self.__t_onpublish.daemon = True
        self.__t_onpublish.start()

        self.__t_onmessage = Thread(target=self.__onmessage)
        self.__t_onmessage.daemon = True
        self.__t_onmessage.start()

        self.__t_onpublish.join(timeout=1)
        self.__t_onmessage.join(timeout=1)

        return 0

    def disconnect(self):
        self.disconnect_event.set()
        return 0

    def set_tunnel(self, tunnel):
        self.tunnel = tunnel
        return tunnel

    def set_on_connect(self, func):
        self.on_connect = func

    def set_on_message(self, func):
        self.on_message = func

    def set_on_publish(self, func):
        self.on_publish = func

    def publish(self, **kwargs):
        self.message_queue.put(json.dumps(kwargs))
        mid = randint(0, 65535)
        self._publish_lock.acquire()
        self.publish_onfly[mid] = kwargs
        self._publish_lock.release()

        return mid