from dataclasses import dataclass
import requests
import json
import random
import sys


@dataclass
class booster_string:
    string: str = 'c.c.c.c.c.c.c.c.c.c.c.u.u.u.r'


class booster_parser:
    def parse(booster_string):
        queries = []
        elements = booster_string.string.split('.')
        for element in elements:
            rarity = element[0]
            if rarity == 'b':
                query = 't:basic'
            else:
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
        del split_booster[position:position + 1]
        booster.string = '.'.join(split_booster)

    def mythicify(self, booster, set=None, odds=None):
        if set:
            ms = len(vizualizer().get_cards(f's:{set}, r=m'))
            rs = len(vizualizer().get_cards(f's:{set}, r=r'))
            odds = [ms, rs * 2]
        # Standard mythic distribution
        if not odds:
            odds = [15, 106]
        r_pos = booster.string.split('.').index('r')

        if random.choices([True, False], odds)[0]:
            self.remove(booster, r_pos)
            self.add(booster, 'm', r_pos)

    def foilify(
        self,
        booster,
        foil_pack_odds=None,
        set=None,
        foil_odds=None,
        to_replace='c'
    ):
        # First, run the odds that this booster contains a foil
        if random.choices([False, True], foil_pack_odds or [1, 2])[0]:
            return

        # Then, calculate/get the foil rarity distribution
        if foil_odds:
            odds = foil_odds
        # Assumes 1:3:4 rare/mythic:uncommon:common foil sheets
        elif set:
            base = f's:{set}, '
            ms = len(vizualizer().get_cards(base + 'r=m'))
            rs = len(vizualizer().get_cards(base + 'r=r'))
            us = len(vizualizer().get_cards(base + 'r=u'))
            cs = len(vizualizer().get_cards(base + 'r=c'))
            bs = len(vizualizer().get_cards(base + 't=basic'))
            odds = [ms, rs * 2, us * 3, cs * 4, bs * 16]
            # Remove basic option if no basics are in the set
            odds = [odd for odd in odds if odd]
        # Standard foil distribution
        else:
            odds = [15, 106, 240, 404, 80]

        choices = ['m', 'r', 'u', 'c', 'b'][:len(odds)]
        foil_rarity = random.choices(choices, odds)[0]

        # A foil replaces the common in standard sets
        x_pos = booster.string.split('.').index(to_replace)
        self.remove(booster, x_pos)
        self.add(booster, foil_rarity + '*', -1)


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


if __name__ == '__main__':
    b_m = booster_modifier()
    viz = vizualizer()
    booster = booster_string()

    print(booster)

    set = sys.argv[1]

    # b_m.mythicify(booster, odds=[1,1])
    # b_m.mythicify(booster, 'lea')

    # b_m.remove(booster, -1)
    # print(booster)

    # b_m.add(booster, 'm', -1)
    # print(booster)

    b_m.mythicify(booster)
    b_m.foilify(booster)
    print(booster)

    # foil_rarities = []
    # for _ in range(850):
    #     booster = booster_string()
    #     b_m.foilify(booster, foil_pack_odds=[1, 0])
    #     foil_rarities.append(booster.string[-2])
    # from collections import Counter
    # print(Counter(foil_rarities))


    # viz.show(booster, set)
