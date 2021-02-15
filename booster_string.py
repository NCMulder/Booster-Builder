from dataclasses import dataclass
import requests
import json
import random
import sys
import argparse
import time
import re
from pathlib import Path
from PIL import ImageDraw, ImageFont


@dataclass
class booster_string:
    string: str = '11c.3u.1r'


class booster_parser:
    def parse(booster_string):
        queries = []
        elements = booster_string.string.split('.')
        pattern = r'(\d+)([bcurm])\[?([^\*\]]*)\]?(\*)?'
        for element in elements:
            # Get the elements
            m = re.match(pattern, element)
            count = int(m.group(1))
            rarity = m.group(2)
            extra = m.group(3)
            foil = m.group(4)
            if rarity == 'b':
                query = '&unique=prints&q=t:basic ' + extra
            else:
                query = f'&q=r:{rarity} -t:basic ' + extra
            queries.append((count, query, foil))
        return queries


class booster_modifier:

    def n(self, booster, set=None, arg=None):
        return booster

    def add(self, booster, set=None, element='1c', position=0):
        split_booster = booster.string.split('.')
        if position == -1:
            split_booster += [element]
        else:
            split_booster.insert(position, element)
        booster.string = '.'.join(split_booster)

    def remove(self, booster, set=None, position=0, count=1):
        split_booster = booster.string.split('.')
        pattern = r'(\d+)([bcurm])\[?(.*)\]?'
        old = split_booster[position]
        match = re.match(pattern, old)
        count_old = int(match.group(1))
        if count_old < count:
            print('Warning: removing more elements than available')
        if count_old <= count:
            del split_booster[position:position + 1]
        else:
            new = f'{count_old - count}{match.group(2)}{match.group(3)}'
            split_booster[position] = new
        booster.string = '.'.join(split_booster)

    def replace(self, booster, set=None, oldpos=0, newpos=0, element='1c'):
        self.remove(booster, position=oldpos)
        self.add(booster, element=element, position=newpos)

    def mythicify(self, booster, set=None, odds=None):
        elements = booster.string.split('.')
        # Find the first rare placement
        for r_pos, element in enumerate(elements):
            m = re.match(r'(\d+)r.*', element)
            if m:
                break
        # If no rares are found, skip the process
        if not m:
            print('No rare to mythicify')
            return

        if not odds:
            # Get the mythic odds for the given set
            if set:
                ms = len(vizualizer().get_cards(f'&q=s:{set}, r=m'))
                rs = len(vizualizer().get_cards(f'&q=s:{set}, r=r'))
                odds = [ms, rs * 2]
            else:
            # Standard mythic distribution
                odds = [15, 106]

        # Roll the odds
        if random.choices([True, False], odds)[0]:
            self.remove(booster, position=r_pos)
            self.add(booster, element='1m', position=r_pos)

    def foilify(
        self,
        booster,
        set=None,
        foil_pack_odds=None,
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
            base = f'&q=s:{set}, '
            ms = len(vizualizer().get_cards(base + 'r=m'))
            rs = len(vizualizer().get_cards(base + 'r=r'))
            us = len(vizualizer().get_cards(base + 'r=u'))
            cs = len(vizualizer().get_cards(base + 'r=c -t=basic'))
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
        elements = booster.string.split('.')
        for x_pos, elem in enumerate(elements):
            if re.search(f'\\d+{to_replace}.*', elem):
                break
        self.remove(booster, position=x_pos)
        self.add(booster, element=f'1{foil_rarity}*', position=-1)

    def add_basic(self, booster, set=None):
        elements = booster.string.split('.')
        # For Alpha, replace 5 out of 121 rares
        # and 47/121 commons
        # For Beta and Unlimited, replace 4 out of 121 rares
        # For Alpha, Beta, Unlimited and Revised,
        # replace 26 out of 121 uncommons
        # For Beta, Unlimited and Revised, replace 46/121 commons
        if set in ['LEA', 'LEB', '2ED', '3ED', 'SUM', 'FBB']:
            place = 0
            for element in elements:
                m = re.match(r'(\d+)([bcurm]).*', element)

                count = int(m.group(1))
                rarity = m.group(2)

                # Uncommons
                if rarity == 'u':
                    odds = [26, 96]
                # Rares
                # TODO: Force Island
                elif rarity in ['r', 'm']:
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

                tot = sum(random.choices([True, False], odds, k=count))
                if tot > 0:
                    if rarity == 'r':
                        mod = f'{tot}b[t:island]'
                    else:
                        mod = f'{tot}b'
                    self.remove(booster, position=place, count=tot)
                    place = place + 1
                    self.add(booster, element=mod, position=place)
                place = place + 1
        else:
            # A basic replaces a common in standard sets
            elements = booster.string.split('.')
            for x_pos, elem in enumerate(elements):
                if re.search(f'\\d+c.*', elem):
                    break
            self.remove(booster, position=x_pos)
            self.add(booster, element='1b', position=-1)

    mod_dict = {
        'A': add,
        'R': remove,
        'M': mythicify,
        'F': foilify,
        'B': add_basic,
        'Z': replace
    }

    def modify(self, mod_string, booster, set=None):
        if not mod_string or mod_string == 'X':
            return
        mod_pattern = r'(.)\[?(.*?)\]?$'
        for mod in mod_string.split('.'):
            m = re.match(mod_pattern, mod)
            func = m.group(1)
            args = m.group(2).split(';') if m.group(2) else []
            args = [eval(arg) for arg in args]
            args = [set] + args
            print(func, args)
            (self.mod_dict.get(func) or self.n)(self, booster, *args)


class vizualizer:
    def get_cards(self, query):
        time.sleep(0.1)
        url = f'https://api.scryfall.com/cards/search?{query}+is:booster'
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
        for count, query, foil in queries:
            cards = self.get_cards(query + f'+s:{set}')
            card_sample = random.sample(cards, k=count)
            booster_cards.extend(card_sample)
        return booster_cards

    def get_card_image(self, cardname='', version='normal', uri=''):
        """Get a card image from Scryfall based on card name.
        See https://scryfall.com/docs/api/images
        """

        time.sleep(0.1)
        if uri:
            result = requests.get(uri)
        else:
            result = requests.get(
                'https://api.scryfall.com/cards/'
                f'named?exact={cardname}&format=image&version={version}'
            )

        if result.status_code == 200:
            result = result.content
        else:
            print(requests.exceptions.HTTPError)
            return None

        return result

    def print(self, booster, set):
        queries = booster_parser.parse(booster)
        booster_cards = []
        for count, query, foil in queries:
            cards = self.get_cards(query + f'+s:{set}')
            card_sample = random.sample(cards, k=count)
            booster_cards.extend([card['name'] for card in card_sample])
        print(booster_cards)

    def show(self, booster, set):
        # Image setup
        from PIL import Image
        from io import BytesIO

        card_size = [488, 680]
        queries = booster_parser.parse(booster)
        total = sum([count for count, _, _ in queries])

        image = Image.new(
            'RGB',
            [card_size[0] * 5,
             card_size[1] * -(-total // 5)]
        )

        index = 0
        for count, query, foil in queries:
            cards = self.get_cards(query + f'+s:{set}')
            card_sample = random.sample(cards, k=count)

            for card in card_sample:
                image_box = (
                    card_size[0] * (index % 5),
                    card_size[1] * (index // 5)
                )

                uri = (
                    card.get('image_uris')
                    or card['card_faces'][0]['image_uris']
                )['normal']

                card_image = self.get_card_image(uri=uri)
                card_image = Image.open(BytesIO(card_image))

                if foil:
                    fnt = ImageFont.truetype("Beleren-Bold.ttf", 40)
                    draw = ImageDraw.Draw(card_image)
                    draw.text((40, 70), "FOIL", font=fnt, fill=(255, 255, 255))

                image.paste(
                    card_image,
                    box=image_box
                )
                index = index + 1

        image.show()


class booster_builder():
    def get_random_boosters(
        n_players, n_packs, unique_packs=True, booster_sets=True
    ):
        set_dict = {}

        p = Path(__file__).with_name('sets.csv')
        with p.open('r', encoding='utf8') as set_list:
            for set_info in set_list.readlines():
                split_info = set_info.strip().split(',', 3)
                if (
                    not booster_sets
                    or (split_info[3] not in 'YZ'
                        and split_info[2] in ['core', 'expansion', 'masters']
                        )
                ):
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
        default='11c.3u.1r',
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
            split_info = set_info.strip().split(',', 3)
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
    elif dict_mod_string and dict_mod_string in 'XY':
        print(f'The set {b_set_info[0]} ({b_set}) isn\'t fully'
              ' implemented yet; expect discrepancies.')
    if mod_string and mod_string in 'XY':
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
