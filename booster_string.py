from dataclasses import dataclass
import requests
import json
import random


@dataclass
class booster_string:
    string: str = 'c.c.c.c.c.c.c.c.c.c.c.u.u.u.r'


class booster_parser:
    def parse(booster_string):
        queries = []
        elements = booster_string.string.split('.')
        for element in elements:
            rarity = element[0]
            query = f'r:{rarity}'
            queries.append(query)
        return queries


class booster_modifier:
    def add(self, booster, element, position=0):
        split_booster = booster.string.split('.')
        if position == -1:
            split_booster += [element]
        else:
            split_booster[position:position] = element
        booster.string = '.'.join(split_booster)

    def remove(self, booster, position=0):
        split_booster = booster.string.split('.')
        del split_booster[position:]
        booster.string = '.'.join(split_booster)

    def mythicify(self, booster, set=None, odds=None):
        if set:
            ms = len(vizualizer().get_cards(f's:{set}, r=m'))
            rs = len(vizualizer().get_cards(f's:{set}, r=r'))
            odds = [ms, rs * 2 + ms]
        print(odds)
        r_pos = booster.string.split('.').index('r')

        if random.choices(['m', 'r'], odds)[0] == 'm':
            self.remove(booster, r_pos)
            self.add(booster, 'm', r_pos)


class vizualizer:
    def get_cards(self, query):
        url = f'https://api.scryfall.com/cards/search?q={query}+is:booster'
        response = requests.get(url).json()
        if response['object'] != 'list':
            print(query, response['details'])
            return []
        cards = []
        while True:
            cards += response['data']
            if response['has_more']:
                response = requests.get(response['next_page']).json()
            else:
                break
        return cards

    def show(self, booster, set):
        queries = booster_parser.parse(booster)
        booster_cards = []
        for query in queries:
            cards = self.get_cards(query + f'+s:{set}')
            card = random.choice(cards)
            booster_cards.append(card['name'])
        print(booster_cards)


b_m = booster_modifier()
viz = vizualizer()

booster = booster_string()
print(booster)

# b_m.mythicify(booster, odds=[1,1])
b_m.mythicify(booster, 'lea')

# b_m.remove(booster, -1)
# print(booster)

# b_m.add(booster, 'm', -1)
print(booster)

# viz.show(booster, 'kld')
