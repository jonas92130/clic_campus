from concurrent.futures import ThreadPoolExecutor

ids = []
with open("ids") as f:
    for line in f:
        ids.append(int(line.strip()))


done = 0


def send(city_id):
    global done
    import httpx

    url = f"https://www.casinosavenue.com/fr/ville/setTexte/{city_id}"

    payload = 'hotel_casino_trip_sitebundle_villesettexte%5BlisteTextesVilles%5D%5B0%5D%5Btexte%5D=&hotel_casino_trip_sitebundle_villesettexte%5BlisteTextesVilles%5D%5B1%5D%5Btexte%5D=&hotel_casino_trip_sitebundle_villesettexte%5BlisteTextesVilles%5D%5B2%5D%5Btexte%5D=&hotel_casino_trip_sitebundle_villesettexte%5BlisteTextesVilles%5D%5B3%5D%5Btexte%5D=&hotel_casino_trip_sitebundle_villesettexte%5BlisteTextesVilles%5D%5B4%5D%5Btexte%5D=&hotel_casino_trip_sitebundle_villesettexte%5BlisteTextesVilles%5D%5B5%5D%5Btexte%5D=&hotel_casino_trip_sitebundle_villesettexte%5B_token%5D=mR_BH_4mm1EIhzElEyUDBcHIcg_pVKgE8esmflxfaxc'
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7,it;q=0.6,zh-CN;q=0.5,zh;q=0.4',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': 'device_view=full; _ga=GA1.2.169864583.1716985756; ipClient=176.179.26.229; ipLat=48.8323; ipLong=2.4075; ipCountry=FR; ipSubdivision=IDF; _gid=GA1.2.400104185.1717314812; PHPSESSID=5dk4gf3k20b5beqh6jbnpadcm3; _ga_3FW5VDHPGP=GS1.2.1717314812.2.1.1717315046.60.0.0; ADRUM=s=1717315109998&r=https%3A%2F%2Fwww.casinosavenue.com%2Fen%2Fville%2FsetTexte%2F9852%3F0',
        'Origin': 'https://www.casinosavenue.com',
        'Referer': 'https://www.casinosavenue.com/en/ville/setTexte/9852',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"'
    }

    res = httpx.request("POST", url, headers=headers, data=payload)
    done += 1
    print(done, city_id, res.status_code)


ThreadPoolExecutor(max_workers=10).map(send, ids)