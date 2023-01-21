# StockNotifier
thios python  script is using https://pushover.net/api in order to push to your phone
Notify if some item is in stock in some store

# examples scraping
f-productOffers-fnacContent js-fnacTabContent isActive

curl 'https://www.fnac.es/Consola-PlayStation-5-Videoconsola-Consola/a7724798' \
  -H 'authority: www.fnac.es' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36' \
  -H 'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9' \
 --compressed

https://www.fnac.es/LEGO-Super-Mario-71374-Nintendo-Entertainment-System-Juegos-de-construccion-Lego/a7956379#omnsearchpos=1
https://www.fnac.es/Nav/API/FnacOfferTab/7956379/1

https://www.fnac.es/Consola-PlayStation-5-Videoconsola-Consola/a7724798
https://www.fnac.es/Nav/API/FnacOfferTab/7724798/1

https://www.fnac.es/The-Last-of-Us-Parte-II-PS4-Juego-PS4/a7004048#int=S:Destacados|Gaming:%20Videojuegos%20y%20Consolas|79720|7004048|BL2|L1
https://www.fnac.es/Nav/API/FnacOfferTab/7004048/1


https://www.fnac.es/Portatil-HP-Laptop-15s-eq1044ns-15-6-Plata-Ordenador-portatil-PC-Portatil/a7622827#int=S:OFERTAS%20DESTACADAS%20%7CHome-Gene%7CNonApplicable%7CNonApplicable%7CBL3%7CNonApplicable
https://www.fnac.es/Nav/API/FnacOfferTab/7622827/1

diesponible
    class="f-buyBox-availabilityStatus-available"
    class="f-buyBox-availability f-buyBox-availabilityStatus-available"
no disponible
    class="f-buyBox-availabilityStatus-unavailable"
    class="f-buyBox-availability f-buyBox-availabilityStatus-unavailable"

price, mas de uno
    class="f-productOffer f-productOffer--options clearfix"