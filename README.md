# UGC-tools

_Ce repository a pour but de fournir des outils pour faciliter l'accès aux information des cinémas ugc_

## Carte des cinémas

Les cinémas sont présentés à [cette adresse](https://www.ugc.fr/cinemas-acceptant-ui.html) par UGC. Il n'est pas facile de trouver le cinéma le plus proche de soi.

Une carte est disponible à [cette url](http://ugc.bruhie.re/)

### Fonctionnement

La liste des cinémas est récuperé en utilisant BeautifulSoup directement depuis l'html de la page. Ces adresses sont comparées avec la [base nationale de data.gouv](https://adresse.data.gouv.fr/donnees-nationales), pour les adresses francaises.
