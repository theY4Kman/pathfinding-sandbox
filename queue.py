import Queue


class PriorityQueueSet(object):
    def __init__(self):
        self.queue = Queue.PriorityQueue()
        self.items = {}

    def put(self, priority, item):
        self.items[item] = priority
        self.queue.put((priority, item))

    def get(self):
        priority, item = self.queue.get()
        del self.items[item]
        return priority, item

    def replace(self, priority, item):
        if item in self.items:
            self.queue.queue.remove((self.items[item], item))
        self.put(priority, item)

    def priority(self, item):
        return self.items.get(item)

    def __contains__(self, item):
        return item in self.items
