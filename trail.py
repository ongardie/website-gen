class Queue(list):

    def enqueue(self, item):
        while item in self:
            self.remove(item)
        self.append(item)

    def dequeue(self):
        return self.pop(0)

class Page(object):

    def __init__(self, title, url):
        self.title = title
        self.url = url

    def __cmp__(self, other):
        if self.url == other.url:
            return cmp(self.title, other.title)
        else:
            return cmp(self.url, other.url)

    def __str__(self):
        return self.title

class Trail(Queue):

    def __init__(self, queue=None):
        if queue is None:
            queue = Queue()

        self.queue = queue

        # these will be filled in later
        self.session = None
        self.url = '/'

    def __iter__(self):
        return self.queue.__iter__()

    def __getitem__(self):
        return self.queue.__getitem__()

    def __len__(self):
        return self.queue.__len__()

    def add(self, title):
        self.queue.enqueue(Page(title, self.url))

        while len(self.queue) > 5:
            self.queue.dequeue()

        self.session['trail'] = self.queue
        self.session.save()

    def __str__(self):
        return '[%s]' % ', '.join([str(page) for page in self])

class TrailMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):

        url = environ['PATH_INFO']

        session = environ['beaker.session']

        if session.has_key('trail'):
            trail = Trail(session['trail'])
        else:
            trail = Trail()

        trail.url = url
        trail.session = session

        environ['trail'] = trail

        return self.app(environ, start_response)
