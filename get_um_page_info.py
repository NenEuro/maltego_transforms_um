import maltego
import requests
import sys
import re
from bs4 import BeautifulSoup

info = dict()

def maltego_ent_type(key):
    if key=="E-mail":
        return "maltego.EmailAddress"
    elif key=="Location" or key=="Office" or key=="Postal address":
        return "maltego.Location"
    elif key=="Phone":
        return "maltego.PhoneNumber"
    else:
        return "maltego.Phrase"

def add_info(key, value):
    if key in info:
        info[key].add(value)
    else:
        info[key]={value}

def get_soup(url):
    r = requests.get(url)
    r.raise_for_status
    soup = BeautifulSoup(r.text, "html.parser")
    return soup


def get_info_from_home_page(url):
    soup = get_soup(url)
    content = soup.findAll("div", {"class": "content"})
    positions = [record.find('h4').text for record in content]
    locations = [record.find('p').text for record in content]
    for position in positions:
        add_info("Position", position)
    for location in locations:
        add_info("Location", location)
    content = soup.findAll("div", {"class": "description"})
    educations = [record.find('p', {"class": "what"}).text for record in content]
    locs = [record.find('p', {"class": "where"}).text for record in content]
    for education in educations:
        add_info("Education", education)
    for location in locs:
        add_info("Location", location)

def get_info_from_contac_page(url):
    url=f"{url}/contact"
    soup = get_soup(url)
    info_from_page = soup.find_all("h4")
    values = [inf.find_next_sibling().text.strip() for inf in info_from_page]
    keys = [key.text.strip() for key in info_from_page]
    i=0
    while i<len(keys):
        add_info(keys[i],values[i])
        i+=1

def parse_into_maltego(m):
    for key,values in info.items(): 
        for value in values:
            if key=="Phone":
                value = value.replace(" ","")
            m.addEntity(maltego_ent_type(key),value)

def main():
    try:
        m = maltego.MaltegoTransform()
        web_url_for_UM = sys.argv[1]
        if "webs.um.es" in web_url_for_UM:
            get_info_from_home_page(web_url_for_UM)
            get_info_from_contac_page(web_url_for_UM)
            info.pop("LDAP entry", None)
            parse_into_maltego(m)
            m.returnOutput()
    except Exception as e:
        m.addUIMessage(str(e))


if __name__ == "__main__":
    main()