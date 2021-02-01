from collections import defaultdict

class settings:
    enviroment: str
    enableLogInfo: bool
    url_push: str
    token_push: str
    readConfigEachSeconds:int = 0
    stopProcess: bool = False
    delayIfException: int = 0
    delayPerItem: int = 0
    filetoLog = "log.txt"    
    disablePushForAll: bool = False
    onlySendPushWhenMatchPrice: bool = False
    showConfigInfo: bool = False
    users_pushKeys = ''
    itemsToLookFor = []
    group_by_store = defaultdict(list)
    storeConfig = defaultdict(list)