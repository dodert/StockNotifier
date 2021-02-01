from datetime import datetime
class Class_push_send_log:
    push_key:str = None
    first_send:datetime = None
    latest_send:datetime = None
    unique_store_item: str = None
    def __init__(self, push_key:str = None, unique_store_item: str = None):
        self.push_key = push_key
        if self.first_send is None:
            self.first_send = datetime.utcnow()
        self.latest_send = None
        self.unique_store_item = unique_store_item

class Class_sendpush_to:
    device: str
    delayBetween_seconds: int
    def __init__ (self, device: str, delayBetween_seconds: int):
        self.device = device
        self.delayBetween_seconds = delayBetween_seconds

