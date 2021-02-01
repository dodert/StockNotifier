class item_game:
    url: str = ''
    isNew: bool = False
    buttonText: str = ''
    buyType: int = 0
    basketCode: str = ''
    sellPrice: float = 0
    name: str = ''
    isReserve: bool = False
    hasStock: bool = False
    __base_url: str = 'https://www.game.es/'
    def __init__(self, json_item ):
        if "Navigation" in json_item: self.url = f"{self.__base_url}{json_item['Navigation']}"
        if "IsNew" in json_item['Offers'][0]: self.isNew = json_item['Offers'][0]['IsNew']
        if "ButtonText" in json_item['Offers'][0]: self.buttonText = json_item['Offers'][0]['ButtonText']
        if "BasketCode" in json_item['Offers'][0]: self.basketCode = json_item['Offers'][0]['BasketCode']
        if "SellPrice" in json_item['Offers'][0]: self.sellPrice = json_item['Offers'][0]['SellPrice']
        if "IsReserve" in json_item['Offers'][0]: self.isReserve = json_item['Offers'][0]['IsReserve']
        if "Name" in json_item: self.name = json_item['Name']

        if self.buttonText == 'Comprar': self.hasStock = True