class store_config:
    name:str
    function = None
    timeoutRequest: int
    eppepe:str
    def __init__(self, name:str, function , timeoutRequest):
        self.name = name
        self.function = function
        self.timeoutRequest = timeoutRequest