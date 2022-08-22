from argparse import ArgumentError
from cgitb import html
from time import sleep
import unicodedata
import requests
from bs4 import BeautifulSoup, element
import re

import csv

import logging

# ADDRESS_SANITIZE_REGEX =
POSTAL_AND_CITY_REGEX = re.compile(
    r"(?P<postcode>\d{5}) (?P<city>.*)$")

# Also removes everything after the level, because of https://www.ugc.fr/cinema.html?id=58
LEVEL_REGEX = re.compile(r" - Niveau -?\d.*$")
ADDRESS_NUMBER_REGEX = re.compile(r"^(?P<number>[ /\d-]+(bis)?(ter)?)")

SECONDARY_ADDRESS_REGEX = re.compile(r" - .*$")
THEATRE_LIST_URL = "https://www.ugc.fr/cinemas-acceptant-ui.html"

BAN_URL = "https://api-adresse.data.gouv.fr/search/"


Logger = logging.Logger("ugc-logs")


class AddressNotFoundException(BaseException):
    pass


class Address(object):
    def __init__(self, raw_address: str):

        self.address_1 = {"number": None,
                          "street": None, "special_place": None}
        self.address_2 = None

        # Cleanup address a bit
        address = raw_address.strip()
        address = unicodedata.normalize("NFKD", address)
        address = address.replace("–", "-")  # Don't even ask

        # first extract city and postal code which are consistent with each other

        res = POSTAL_AND_CITY_REGEX.search(address)
        self.postcode = res.group("postcode")
        self.city = res.group("city")
        address = POSTAL_AND_CITY_REGEX.sub(
            '', address).strip()
        # I would've loved to use a single regex to handle all of theses strings but they are not consistent so here is some spaghetti for you
        level_match = LEVEL_REGEX.search(address)
        if level_match is not None:
            self.level = level_match.group().strip(" -")
            address = LEVEL_REGEX.sub('', address).strip()
        else:
            self.level = None
        address_number_match = ADDRESS_NUMBER_REGEX.search(address)
        if address_number_match is not None:
            self.address_1["number"] = address_number_match.group("number")
            address = ADDRESS_NUMBER_REGEX.sub('', address).strip(" ,")

        secondary_address_match = SECONDARY_ADDRESS_REGEX.search(
            address)
        if secondary_address_match is not None:
            self.address_2 = {"number": None,
                              "street": None, "special_place": None}
            secondary_address = secondary_address_match.group().strip(" -")
            secondary_address_number_match = ADDRESS_NUMBER_REGEX.search(
                secondary_address)
            if secondary_address_number_match is not None:
                self.address_2["number"] = secondary_address_number_match.group(
                    "number").strip()
                self.address_2["street"] = ADDRESS_NUMBER_REGEX.sub(
                    '', secondary_address).strip(" ,")
            else:
                self.address_2["special_place"] = secondary_address

            address = SECONDARY_ADDRESS_REGEX.sub('', address).strip(" -")

        if self.address_1["number"] is None:
            self.address_1["special_place"] = address
        else:
            self.address_1["street"] = address

    def find_geolocation(self):
        try:
            self.lon, self.lat = self._get_coordinates_from_ban_api_with_both_city_and_post_codes(
                self.address_1)
            Logger.info("Geolocation succesfully obtained")
            return
        except AddressNotFoundException:
            if self.address_2 is None:
                Logger.error(
                    f"Address not found : {self._build_address(self.address_1)}, no address 2 exists for this one, skipping...")
                return
        Logger.warning(
            f"Address not found {self._build_address(self.address_1)}, falling back to address 2")
        try:
            self.lon, self.lat = self._get_coordinates_from_ban_api_with_both_city_and_post_codes(
                self.address_2)
            Logger.info("Geolocation succesfully obtained (with address 2)")
        except AddressNotFoundException:
            Logger.error(
                f"Address 2 not found as well : {self._build_address(self.address_2)}")

    def _build_address(self, address_dict: dict):
        return (address_dict["special_place"] if address_dict["special_place"]
                else f"{address_dict['number']} {address_dict['street']}")

    def _get_coordinates_from_ban_api_with_both_city_and_post_codes(self, address_dict: dict):
        try:
            return self._get_coordinates_from_ban_api(address_dict, use_citycode=False, use_postcode=True)
        except AddressNotFoundException:
            Logger.warning(
                f"Address not found using postcode, trying city code")
        try:
            return self._get_coordinates_from_ban_api(address_dict, use_citycode=True, use_postcode=False)
        except AddressNotFoundException as e:
            Logger.warning(
                f"Address not found using city code, trying with no filter")
        try:
            a = self._get_coordinates_from_ban_api(
                address_dict, use_citycode=False, use_postcode=False)
            return a
        except AddressNotFoundException as e:
            Logger.warning(
                f"Address wasn't found at all in the whole country")
            raise e

    def _get_coordinates_from_ban_api(self, address_dict: dict, use_postcode=True, use_citycode=False, delay_seconds=0.1):
        if use_postcode and use_citycode:
            raise ArgumentError(
                "Both use_post_code and use_city_code cannot be true")
        address_query = self._build_address(address_dict)
        resp = requests.get(f"{BAN_URL}", params={
                            "q": address_query,
                            **({"postcode": self.postcode} if use_postcode else {}),
                            **({"citycode": self.postcode} if use_citycode else {}),
                            "autocomplete": 0,
                            "limit": 1
                            })
        Logger.info(resp.request.url)
        resp.raise_for_status()
        # built-in delay to meet quotas
        sleep(delay_seconds)
        if not len(resp.json()["features"]):
            raise AddressNotFoundException()

        coordinates = resp.json()["features"][0]["geometry"]["coordinates"]

        return coordinates


class Theatre(object):
    def __init__(self, html: element.Tag) -> None:
        self.html = html
        self.name = self.html.find("div", {"class": "text-uppercase"}).text
        self.address = Address(self.html.find(
            "div", {"class": "color--blue-grey"}).text)

        link = self.html.find("a")
        self.url = (link.attrs["href"] if link is not None else None)

        self.address.find_geolocation()

    def write_to_csv(self, csv_writer: csv.DictWriter):
        csv_writer.writerow({
            "name": self.name,
            "lat": self.address.lat,
            "lon": self.address.lon,
        })


class TheatreType(object):
    def __init__(self, html: element.Tag) -> None:
        self.html = html
        self.name = self.html.find("span", {"class": "text-uppercase"}).text
        theatre_parent = self.html.find(
            "div", {"class": "row collapse"})
        self.theatres = [Theatre(theatre_html)
                         for theatre_html in theatre_parent.children if theatre_html != ' ']

    def write_to_csv(self, csv_writer: csv.DictWriter):
        for theatre in self.theatres:
            theatre.write_to_csv(csv_writer)


class IsBelgiumException(BaseException):
    pass


class Region(object):
    def __init__(self, html: element.Tag):
        self.html = html
        self.name = self.html.find("h2").text.strip()
        if self.name == "Belgique":
            raise IsBelgiumException()
        self.theatre_types = [TheatreType(theatre_type_html) for theatre_type_html in self.html.find_all(
            "li", {"class": "accordion-item"})]

    def write_to_csv(self, csvDictWriter: csv.DictWriter):
        for theatre_type in self.theatre_types:
            theatre_type.write_to_csv(csvDictWriter)


if __name__ == "__main__":

    theatre_list_request = requests.get(THEATRE_LIST_URL)
    theatre_list_request.raise_for_status()

    html = BeautifulSoup(theatre_list_request.text, features="html.parser")
    with open("output.csv", "w") as file:
        field_names = ["name", "lat", "lon"]
        csv_dict_writer = csv.DictWriter(file, field_names)
        csv_dict_writer.writeheader()

        for region_html in html.find_all(
                "div", {"class": "row group-accordion"}):
            try:
                region = Region(region_html)
                region.write_to_csv(csv_dict_writer)

            except IsBelgiumException:  # Shit happens
                pass
