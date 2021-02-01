import maltego
import sys
import requests
import re
import base64
from bs4 import BeautifulSoup

info = dict()


def maltego_ent_type(key):
    if key=="E-Mail" or key=="Alternative address":
        return "maltego.EmailAddress"
    elif key=="Name":
        return "maltego.Person"
    elif key=="Phone Number":
        return "maltego.PhoneNumber"
    elif key=="Area of Knowledge" or key=="Organizational Units" or key=="Center" or key=="Postal Address" or key=="Despacho" or key=="Filiación" or key=="Center":
        return "maltego.Location"
    elif key=="Position" or key=="Cargo":
        return "maltego.Phrase"
    elif key=="Web personal institucional":
        return "maltego.Website"
    else:
        return "maltego.Phrase"

def add_info(key, value):
    if key=="E-Mail" or key=="Alternative address":
        value = parse_email(value)
    if key in info:
        info[key].add(value)
    else:
        info[key]={value}

def parse_email(soup_element) -> str:
    domain = base64.b64decode(re.findall("\'(.*?)\'",str(soup_element))[0]).decode("UTF-8")
    local_part = base64.b64decode(re.findall("\'(.*?)\'",str(soup_element))[1]).decode("UTF-8")
    return f"{local_part}@{domain}"

def get_english_page(r: requests.Response) -> requests.Response:
    if r.url.find("lang=0") != -1:
        r = requests.get(r.url.replace("lang=0", "lang=1"))
    return r

def parse_table(table):
    prev_key=None
    for row in table.findAll('tr'):
        cols = row.findAll('td')
        cols = [ele.text.strip() for ele in cols]
        if len(cols)==2:
            key = cols[0][:-1]
            value = cols[1]
            add_info(key, value)
            prev_key=key
        elif len(cols)==1:
            value = cols[0]
            if value=="Business Card (vCard)":
                break
            add_info(prev_key, value)
        else:
            raise RuntimeError("Table error!")

def parse_into_maltego(m):
    for key,values in info.items(): 
        for value in values:
            if key=="Phone Number":
                value = value.replace(" ","")
            m.addEntity(maltego_ent_type(key),value)
            
def parse_personal_page(r, email):
    r = get_english_page(r)
    soup = BeautifulSoup(r.text, 'html.parser')
    email_match = False
    email_list = soup.findAll("script",text=re.compile('correo'))

    if email_list!=None:
        for email_from_page in email_list:
            if parse_email(email_from_page)==email:
                email_match=True
    else:
        raise RuntimeError("No emails found on page!") 
            
    if email_match:
        info_table = soup.findAll("table",{"class": "infoElem"})
        if len(info_table)!=1:
            raise RuntimeError("Unexpected error with table extraction!")
        parse_table(info_table[0])
#    else:
#        raise RuntimeError("Wrong person!")

def get_all_personal_pages(r):
    soup = BeautifulSoup(r.text, 'html.parser')
    return ["https://www.um.es/atica/directorio/"+a['href'] for a in soup.findAll('a', href=True) if "usuario=" in a['href']]

def main():
    try:
        m = maltego.MaltegoTransform()
        email = sys.argv[1]
        r = requests.get("https://www.um.es/atica/directorio/?search="+email)
        r.raise_for_status()
        if "usuario=" in r.url:
            parse_personal_page(r, email)
        else:
            urls = get_all_personal_pages(r)
            for url in urls:
                r=requests.get(url)
                parse_personal_page(r, email)
        parse_into_maltego(m)
        m.returnOutput()
    except Exception as e:
        m.addUIMessage(str(e))


if __name__ == "__main__":
    main()
