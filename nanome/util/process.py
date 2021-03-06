class Process():
    _manager = None

    class _ProcessRequest():
        def __init__(self):
            self.executable_path = ""
            self.args = []
            self.encoding = None  # "utf-8" if stdout and err are text
            self.cwd_path = None
            self.id = 0

    def __init__(self):
        self.on_queued = lambda: None
        self.on_queue_position_change = lambda _: None
        self.on_start = lambda: None
        self.on_done = lambda _: None
        self.on_error = lambda _: None
        self.on_output = lambda _: None
        self.__request = Process._ProcessRequest()

    @property
    def executable_path(self):
        return self.__request.executable_path

    @executable_path.setter
    def executable_path(self, value):
        self.__request.executable_path = value

    @property
    def args(self):
        return self.__request.args

    @args.setter
    def args(self, value):
        self.__request.args = value

    @property
    def cwd_path(self):
        return self.__request.cwd_path

    @cwd_path.setter
    def cwd_path(self, value):
        self.__request.cwd_path = value

    @property
    def output_text(self):
        return self.__request.encoding == "utf-8"

    @output_text.setter
    def output_text(self, value):
        if value:
            self.__request.encoding = "utf-8"
        else:
            self.__request.encoding = None

    @property
    def _id(self):
        return self.__request.id

    def start(self):
        Process._manager.start_process(self, self.__request)
