from collections import defaultdict
from datetime import datetime
from notifications.push.Push_notifications import *
#import notifications.push.push_notifications as tt

class aux:
    lastNotificationSendTime = datetime(2000,1,1,0,0,0,0)
    push_send_log = defaultdict(Class_push_send_log)
    #push_send_log: defaultdict(list)