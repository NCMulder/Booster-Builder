from dataclasses import dataclass
import requests
import json
import random
import sys
import time


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

    def replace(self, booster, position, element):
        self.remove(booster, position)
        self.add(booster, element, position)

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

    # b_m.mythicify(booster)
    # b_m.foilify(booster)
    b_m.add_basic(booster, set)
    print(booster)

    # foil_rarities = []
    # for _ in range(850):
    #     booster = booster_string()
    #     b_m.foilify(booster, foil_pack_odds=[1, 0])
    #     foil_rarities.append(booster.string[-2])
    # from collections import Counter
    # print(Counter(foil_rarities))

    viz.show(booster, set)
