from cgitb import html
import unicodedata
import requests
from bs4 import BeautifulSoup, element
import re

# ADDRESS_SANITIZE_REGEX =
POSTAL_AND_CITY_REGEX = re.compile(
    r"(?P<postal_code>\d{5}) (?P<city>.*)$")

# Also removes everything after the level, because of https://www.ugc.fr/cinema.html?id=58
LEVEL_REGEX = re.compile(r" - Niveau -?\d.*$")
NUMBER_REGEX = re.compile(r"^[\d, -]*")
THEATRE_LIST_URL = "https://www.ugc.fr/cinemas-acceptant-ui.html"


class Address(object):
    def __init__(self, raw_address: str):
        address = raw_address.strip()
        address = unicodedata.normalize("NFKD", address)

        # first extract city and postal code which are consistent with each other

        res = POSTAL_AND_CITY_REGEX.search(address)
        self.postal_code = res.group("postal_code")
        self.city = res.group("city")
        address = POSTAL_AND_CITY_REGEX.sub(
            '', address).strip()
        # I would've loved to use a single regex to handle all of theses strings but they are not consistent so here is some spaghetti for you
        level_match = LEVEL_REGEX.search(address)
        if level_match is not None:
            self.level = level_match.group()
            address = LEVEL_REGEX.sub('', address).strip()
        else:
            self.level = None


class Theatre(object):
    def __init__(self, html: element.Tag) -> None:
        self.html = html
        self.name = self.html.find("div", {"class": "text-uppercase"}).text
        self.address = Address(self.html.find(
            "div", {"class": "color--blue-grey"}).text)
        # print(self.name)


class TheatreType(object):
    def __init__(self, html: element.Tag) -> None:
        self.html = html
        self.name = self.html.find("span", {"class": "text-uppercase"}).text
        # print(self.name)
        self.theatres = [Theatre(theatre_html) for theatre_html in self.html.find_all(
            "div", {"class": "item--cinema"})]


class Region(object):
    def __init__(self, html: element.Tag):
        self.html = html
        self.name = self.html.find("h2").text.strip()
        if self.name == "Belgique":
            raise IsBelgiumException()
        # print(self.name)
        self.theatre_types = [TheatreType(theatre_type_html) for theatre_type_html in self.html.find_all(
            "li", {"class": "accordion-item"})]


class IsBelgiumException(BaseException):
    pass


if __name__ == "__main__":

    theatre_list_request = requests.get(THEATRE_LIST_URL)
    theatre_list_request.raise_for_status()

    html = BeautifulSoup(theatre_list_request.text, features="html.parser")
    print(type(html.find_all(
        "div", {"class": "row group-accordion"})[0]))
    try:
        regions = [Region(region_html) for region_html in html.find_all(
            "div", {"class": "row group-accordion"})]
    except IsBelgiumException:  # Shit happens
        pass

    print('main')
