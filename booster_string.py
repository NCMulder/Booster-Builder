from dataclasses import dataclass
import requests
import json
import random
import sys
import argparse
import time
from pathlib import Path


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
                query = '++t:basic'
            else:
                query = f'r:{rarity} -t:basic'
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

    def replace(self, booster, position, element):
        self.remove(booster, position)
        self.add(booster, element, position)

    def mythicify(self, booster, set=None, odds=None):
        elements = booster.string.split('.')
        if 'r' not in elements:
            print('No rare to mythicify')
            return
        if set:
            ms = len(vizualizer().get_cards(f's:{set}, r=m'))
            rs = len(vizualizer().get_cards(f's:{set}, r=r'))
            odds = [ms, rs * 2]
        # Standard mythic distribution
        if not odds:
            odds = [15, 106]
        r_pos = elements.index('r')

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

    def add_basic(self, booster, set=None):
        elements = booster.string.split('.')
        # For Alpha, replace 5 out of 121 rares
        # and 47/121 commons
        # For Beta and Unlimited, replace 4 out of 121 rares
        # For Alpha, Beta, Unlimited and Revised,
        # replace 26 out of 121 uncommons
        # For Beta, Unlimited and Revised, replace 46/121 commons
        if set in ['LEA', 'LEB', '2ED', '3ED', 'SUM', 'FBB']:
            for i, element in enumerate(elements):
                # Uncommons
                if element == 'u':
                    odds = [26, 96]
                # Rares
                # TODO: Force Island
                elif element in ['r', 'm']:
                    if set == 'LEA':
                        odds = [5, 116]
                    elif set in ['LEB', '2ED']:
                        odds = [4, 117]
                    else:
                        odds = [0, 121]
                # Commons
                else:
                    if set == 'LEA':
                        odds = [47, 74]
                    else:
                        odds = [46, 75]

                if random.choices([True, False], odds)[0]:
                    self.replace(booster, i, 'b')
        else:
            # A basic replaces a common in standard sets
            x_pos = elements.index('c')
            self.remove(booster, x_pos)
            self.add(booster, 'b', -1)

    mod_dict = {
        'A': add,
        'R': remove,
        'M': mythicify,
        'F': foilify,
        'B': add_basic
    }

    def modify(self, mod_string, booster, set=None):
        if not mod_string or mod_string == 'X':
            return
        for mod in mod_string.split('.'):
            self.mod_dict[mod](self, booster, set=set)


class vizualizer:
    def get_cards(self, query):
        time.sleep(0.1)
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

    def get_booster_json(self, booster, set):
        queries = booster_parser.parse(booster)
        booster_cards = []
        for query in queries:
            cards = self.get_cards(query + f'+s:{set}')
            card = random.choice(cards)
            booster_cards.append(card)
        return booster_cards

    def get_card_image(self, cardname='', version='normal', uri=''):
        """Get a card image from Scryfall based on card name.
        See https://scryfall.com/docs/api/images
        """

        time.sleep(0.1)
        if uri:
            result = requests.get(uri).content
        else:
            result = requests.get(
                'https://api.scryfall.com/cards/'
                f'named?exact={cardname}&format=image&version={version}'
            ).content

        return result

    def print(self, booster, set):
        queries = booster_parser.parse(booster)
        booster_cards = []
        for query in queries:
            cards = self.get_cards(query + f'+s:{set}')
            card = random.choice(cards)
            booster_cards.append(card['name'])
        print(booster_cards)

    def show(self, booster, set):
        # Image setup
        from PIL import Image
        from io import BytesIO

        card_size = [488, 680]
        queries = booster_parser.parse(booster)

        image = Image.new(
            'RGB',
            [card_size[0] * 5,
             card_size[1] * -(-len(queries) // 5)]
        )

        for i, query in enumerate(queries):
            cards = self.get_cards(query + f'+s:{set}')
            card = random.choice(cards)

            image_box = (
                card_size[0] * (i % 5),
                card_size[1] * (i // 5)
            )

            front_uri = card['image_uris']['normal']

            card_image = self.get_card_image(uri=front_uri)
            image.paste(
                Image.open(BytesIO(card_image)),
                box=image_box
            )

        image.show()


class booster_builder():
    def get_random_boosters(n_players, n_packs, unique_packs=True, booster_sets=True):
        set_dict = {}

        p = Path(__file__).with_name('sets.csv')
        with p.open('r', encoding='utf8') as set_list:
            for set_info in set_list.readlines():
                split_info = set_info.strip().split(',')
                if not booster_sets or (split_info[3] not in 'YZ' and split_info[2] in ['core', 'expansion', 'masters']):
                    set_dict[split_info[0]] = split_info[1:]

        set_codes = list(set_dict.keys())
        total_packs = n_players * n_packs
        if unique_packs:
            random.shuffle(set_codes)
            set_codes = set_codes[:total_packs]
        else:
            set_codes = random.choices(set_codes, k=total_packs)

        b_m = booster_modifier()
        b_v = vizualizer()
        packs = {}
        for i, set_code in enumerate(set_codes):
            booster = booster_string()
            mod_string = set_dict[set_code][2]
            b_m.modify(mod_string, booster, set_code)
            json = b_v.get_booster_json(booster, set_code)
            packs[f'{i} - {set_code}'] = json

        return packs


def parse_arguments(code_list):
    parser = argparse.ArgumentParser(
        description='Create a pack for an M:TG booster.'
    )
    parser.add_argument(
        '-v', '--verbose',
        help='Display additional information',
        action='store_true'
    )

    parser.add_argument(
        '--set',
        choices=code_list,
        default=random.choice(code_list),
        help='The set to use when generating the final pack'
    )

    parser.add_argument(
        '--booster',
        default='c.c.c.c.c.c.c.c.c.c.c.u.u.u.r',
        help='The base booster to use'
    )

    parser.add_argument(
        '--mod',
        '-modifier',
        help='The modifier string to apply to the pack'
    )

    return parser.parse_args()


if __name__ == '__main__':
    # Parse the set information
    set_dict = {}
    with open('sets.csv', 'r', encoding='utf8') as set_list:
        for set_info in set_list.readlines():
            split_info = set_info.strip().split(',')
            set_dict[split_info[0]] = split_info[1:]

    code_list = []
    code_list = list(set_dict.keys())

    args = parse_arguments(code_list)

    b_set = args.set
    b_set_info = set_dict[b_set]
    dict_mod_string = b_set_info[2]
    mod_string = args.mod or dict_mod_string

    if dict_mod_string == 'Z':
        cont = input(
            f'The set {b_set_info[0]} ({b_set}) isn\'t normally used'
            ' for booster generation. Still continue? (Y/N)\n'
        ).upper()
        while cont not in 'YN':
            cont = input('Sorry, I didn\'t get that.  Still continue? (Y/N)\n')
        if cont != 'Y':
            exit()
    elif dict_mod_string in 'XY':
        print(f'The set {b_set_info[0]} ({b_set}) isn\'t fully'
              ' implemented yet; expect discrepancies.')
    if mod_string in 'XY':
        mod_string = 'B.M.F'

    b_string = args.booster
    booster = booster_string()
    booster.string = b_string

    print(booster)

    b_m = booster_modifier()
    b_m.modify(mod_string, booster, b_set)

    print(booster)

    viz = vizualizer()
    viz.show(booster, b_set)
