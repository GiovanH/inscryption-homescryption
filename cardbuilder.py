#!/bin/python3

import csv
import json
import os
import shutil
import collections
# import glob


import jsonschema

csv_path = "./cards.csv"
mod_prefix = "HS"

RECREATE_CSV = False


with open('../MADH95Mods-JSONCardLoader/Schemas/Card_Schema.json', 'r') as fp:
    json_card_schema = json.load(fp)
with open('../MADH95Mods-JSONCardLoader/Schemas/Starter_Deck_Schema.json', 'r') as fp:
    json_deck_schema = json.load(fp)

def main():
    card_dicts = []

    if RECREATE_CSV or not os.path.isfile(csv_path):
        with open(csv_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
            # blank_card = {
            #     'rel_name': 'NAME'
            # }
            # keys = list(rowToCardDef(blank_card).keys())
            # keys.remove('modPrefix')
            # keys.remove('name')
            writer.writerow([
                'rel_name',
                'displayedName',
                'description',
                'baseAttack',
                'baseHealth',
                'bloodCost',
                'bonesCost',
                'rare',
                'hidden',
                'decks',
                'abilities',
                'exjson'
            ])
            writer.writerow([
                'john',
                'John',
                'As default as it gets.',
                '1',
                '1',
                '1',
                '',
                'False',
                'False',
                '',
                'Evolve',
                '{"defaultEvolutionName": "June", "evolveTurns": 1}'
            ])

    with open(csv_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            card_dicts.append(row)

    starter_decks = collections.defaultdict(list)

    for card_dict in card_dicts:
        card_def = rowToCardDef(card_dict)
        name = card_def['name']
        if name == f"{mod_prefix}_":
            continue

        for deck_name in card_def.pop('!CB_DECKS'):
            starter_decks[deck_name].append(name)

        art_path = os.path.join('Artwork', card_def['texture'])
        default_art_path = os.path.join('Artwork', 'default.png')
        if not os.path.isfile(art_path):
            print("Writing default", art_path, "for", name)
            shutil.copy2(default_art_path, art_path)

        out_path = f"Cards/card_{name}.jldr2"
        print("Writing", out_path)
        jsonschema.validate(card_def, schema=json_card_schema)
        with open(out_path, 'w') as fp:
            json.dump(card_def, fp, indent=2)

    decks_def = {
        "decks": []
    }
    for deck_name, card_list in starter_decks.items():
        decks_def['decks'].append({
            "name": deck_name,
            "cards": card_list,
            "iconTexture": "default.png"
        })

    out_path = f"hs_kcmstarters_deck.jldr2"
    print("Writing", out_path)
    jsonschema.validate(decks_def, schema=json_deck_schema)
    with open(out_path, 'w') as fp:
        json.dump(decks_def, fp, indent=2)

def rowToCardDef(card_dict):
    name = f"{mod_prefix}_{card_dict.pop('rel_name')}"

    exjson = json.loads(card_dict.pop('exjson', '{}') or '{}')
    is_rare = card_dict.pop('rare', False)
    if is_rare.lower() == "false":
        is_rare = False

    is_hidden = card_dict.pop('hidden', False)
    if is_hidden.lower() == "false":
        is_hidden = False

    card_def = {
        **card_dict,
        "modPrefix": mod_prefix,
        "name": name,
        # "displayedName": "John",
        # "description": "EGBERT DESCRIPTION",
        "texture": f"card_{name}.png",
        # "pixelTexture": f"card_{name}.png",
        # "baseAttack": 1,
        # "baseHealth": 1,
        # "bloodCost": 1,
        # "abilities": [ "Evolve" ],
        "metaCategories": [
            "GBCPlayable"
        ],
        "appearanceBehaviour": [
            # "bitty45.inscryption.sigils.UndeadAppearance"
        ],
        "cardComplexity": "Simple"
    }

    for int_key in ['baseAttack', 'baseHealth', 'bloodCost', 'bonesCost']:
        card_def[int_key] = int(card_def[int_key] or 0)

    for array_key in ['abilities', 'tribes', 'decks', 'traits']:
        card_def[array_key] = card_def[array_key].split(',')
        card_def[array_key] = list(filter(bool, card_def[array_key]))

    exjson['!CB_DECKS'] = card_def.pop('decks')

    if is_rare:
        card_def['appearanceBehaviour'] += ["RareCardBackground"]
        if not is_hidden:
            card_def['metaCategories'] += ["Rare"]
    else:
        if not is_hidden:
            card_def['metaCategories'] += ["ChoiceNode", "Part3Random", "TraderOffer", "GBCPack"]

    card_def = {
        **card_def,
        **exjson,
    }

    return card_def


if __name__ == "__main__":
    main()