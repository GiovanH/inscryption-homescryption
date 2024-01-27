#!/bin/python3

import csv
import json
import os
import shutil
import collections
import re
import shutil
# import glob


import jsonschema
import subprocess

csv_path = "./cards.csv"
MOD_PREFIX = "HS"

RECREATE_CSV = False

WRITE_DEBUG_PACKS = True

TRIBE_TO_GEM = {
    "HS.Kid": "Green",
    "HS.Troll": "Green",
    "HS.Prospit": "Orange",
    "HS.Derse": "Blue"
}

try:
    with open('../MADH95Mods-JSONCardLoader/Schemas/Card_Schema.json', 'r') as fp:
        json_card_schema = json.load(fp)
    with open('../MADH95Mods-JSONCardLoader/Schemas/Starter_Deck_Schema.json', 'r') as fp:
        json_deck_schema = json.load(fp)
except FileNotFoundError:
    pass

def maybeWriteBlankImage(art_path, dimensions: str):
    if not os.path.isfile(art_path):
        print("Writing default", art_path)
        # shutil.copy2(default_art_path, art_path)
        subprocess.run([
            'magick', 'convert',
            '-size', dimensions,
            'canvas:transparent',
            '-alpha', 'transparent',
            f"PNG32:{art_path}"
        ])

def main():
    card_csv_rows = []

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
            card_csv_rows.append(row)

    starter_decks = collections.defaultdict(list)

    shutil.rmtree("./Cards/")

    for card_csv_row in card_csv_rows:
        card_def = rowToCardDef(card_csv_row.copy())
        name = card_def['name']

        if name == f"{MOD_PREFIX}_":
            continue

        art_path = os.path.join('Artwork', card_def['texture'])
        maybeWriteBlankImage(art_path, '114x94')

        art_path_gbc = os.path.join('Artwork', card_def['pixelTexture'])
        if not os.path.isfile(art_path_gbc):
            print("Resizing for", art_path_gbc)
            subprocess.run([
                'magick', art_path,
                '-interpolate', 'Integer', '-filter', 'point',
                # '-colors', '4',
                # '-separate', '-threshold', '50%', '-combine',
                # '+dither', '-colors', '4',
                '-resize', '41x28',
                art_path_gbc
            ])

        def _writeCard(card_def, postfix=''):
            for deck_name in card_def.pop('!CB_DECKS'):
                deck_tuple = (deck_name, card_def['temple'])
                starter_decks[deck_tuple].append(card_def['name'])

            if WRITE_DEBUG_PACKS:
                deck_tuple = ("HS_TEST", card_def['temple'])
                starter_decks[deck_tuple].append(card_def['name'])

            out_path = f"Cards/card_{card_def['name']}{postfix}.jldr2"
            os.makedirs(f"Cards/", exist_ok=True)
            # print("Writing", out_path)
            try:
                # jsonschema.validate(card_def, schema=json_card_schema)
                pass
            except NameError:
                pass
            with open(out_path, 'w') as fp:
                json.dump(card_def, fp, indent=2)

        _writeCard(card_def)

        # Tech Temple

        card_def_p03 = rowToCardDef(card_csv_row.copy(), temple="Tech", transform_energy=True)
        _writeCard(card_def_p03, postfix="_p03")

        # Other Temples

        for extemple in ['Undead', 'Wizard']:
            # Undead cards don't show up in the pool yet 'Undead',
            card_def_temple = rowToCardDef(card_csv_row.copy(), temple=extemple)
            _writeCard(card_def_temple, postfix=f"_{extemple}")

    decks_def = {
        "decks": []
    }
    for (deck_name, deck_temple), card_list in starter_decks.items():
        iconTexture = f"starter_{deck_name}.png"

        maybeWriteBlankImage(os.path.join('Artwork', iconTexture), '35x44')

        decks_def['decks'].append({
            "name": f"{deck_name}_{deck_temple}",
            "cards": card_list,
            "iconTexture": iconTexture
        })

    out_path = f"hs_kcmstarters_deck.jldr2"
    print("Writing", out_path)
    try:
        jsonschema.validate(decks_def, schema=json_deck_schema)
    except NameError:
        pass
    with open(out_path, 'w') as fp:
        json.dump(decks_def, fp, indent=2)

def rowToCardDef(card_csv_row, temple="Nature", transform_energy=False):
    rel_name = card_csv_row.pop('rel_name')
    mod_prefix = (f"{MOD_PREFIX}{temple}" if temple != "Nature" else MOD_PREFIX)

    if temple == "Undead":
        # Fix unextendable grimoramod
        mod_prefix = f"arackulele.inscryption.grimoramod_HS"

    name = f"{mod_prefix}_{rel_name}"

    try:
        json_txt = card_csv_row.pop('exjson', '{}')
        exjson = json.loads(json_txt or '{}')
    except json.decoder.JSONDecodeError:
        print(repr(json_txt))
        raise
    is_rare = card_csv_row.pop('rare', False)
    if is_rare.lower() == "false":
        is_rare = False

    is_hidden = card_csv_row.pop('hidden', False)
    if is_hidden.lower() == "false":
        is_hidden = False

    card_def = {
        **card_csv_row,
        "modPrefix": mod_prefix,
        "name": name,
        "defaultEvolutionName": f"God {card_csv_row['displayedName']}",
        # "displayedName": "John",
        # "description": "EGBERT DESCRIPTION",
        "texture": f"card_{MOD_PREFIX}_{rel_name}.png",
        "pixelTexture": f"card_{MOD_PREFIX}_{rel_name}_pixelTexture.png",
        "temple": temple,
        # "baseAttack": 1,
        # "baseHealth": 1,
        # "bloodCost": 1,
        # "abilities": [ "Evolve" ],
        "metaCategories": [],
        "appearanceBehaviour": [
            # "bitty45.inscryption.sigils.UndeadAppearance"
        ],
        "cardComplexity": "Simple"
    }

    emission_path = f"card_{MOD_PREFIX}_{rel_name}_emissionTexture.png"
    if os.path.isfile(f"./Artwork/{emission_path}"):
        card_def['emissionTexture'] = emission_path
    else:
        # print("No emissionTexture", emission_path)
        pass

    for int_key in ['baseAttack', 'baseHealth', 'bloodCost', 'bonesCost']:
        card_def[int_key] = int(card_def[int_key] or 0)

    # Name helpers
    for key in ['abilities', 'p03_abilities']:
        card_def[key] = card_def[key].replace('NN.', 'nevernamed.inscryption.sigils.')

    for array_key in ['abilities', 'tribes', 'decks', 'traits', 'p03_abilities']:
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

    if not is_hidden:
        card_def['metaCategories'] += ["GBCPlayable"]

    # Use advanced abilities
    advanced_abilities = card_def.pop('p03_abilities')
    if temple in ['Tech', 'Wizard']:
        card_def['abilities'] = advanced_abilities or card_def['abilities']
    else:
        advanced_abilities

    # Costs
    if temple == 'Tech':
        # Convert blood, bones to energy
        old_blood_cost = card_def.get('bloodCost', 0)
        card_def['bloodCost'] = 0

        old_bone_cost = card_def.get('bonesCost', 0)
        card_def['bonesCost'] = 0

        # if card_def['energyCost'] < 1:
        card_def['energyCost'] = 1
        card_def['energyCost'] += old_blood_cost + old_bone_cost
        # else just keep bones cost

    if temple == 'Undead':
        # Convert blood, bones to bones, energy
        old_blood_cost = card_def.get('bloodCost', 0)
        card_def['bloodCost'] = 0

        old_bone_cost = card_def.get('bonesCost', 0)
        card_def['bonesCost'] = 0

        if card_def['bonesCost'] < 1:
            card_def['bonesCost'] = 1
        card_def['bonesCost'] += old_blood_cost

        if old_bone_cost > 0:
            card_def['energyCost'] = 1 + old_bone_cost

    if temple == 'Wizard':
        old_blood_cost = card_def.get('bloodCost', 0)
        card_def['bloodCost'] = 0

        old_bone_cost = card_def.get('bonesCost', 0)
        card_def['bonesCost'] = 0

        total_old_cost = (old_bone_cost/1.5) + old_blood_cost

        card_def['gemsCost'] = []

        # Take a total "cost" in points, based on bones and blood.
        # First, pay it with tribes
        # Then, pull arbitrary gems if there's an outstanding balance.

        # Outstanding cost, in gems
        outstanding = round(total_old_cost * 0.6)

        # print(name, outstanding, card_def['tribes'], card_def['gemsCost'])
        while len(card_def['tribes']) > 0 and outstanding > 0:
            new_gem = TRIBE_TO_GEM.get(card_def['tribes'].pop())
            if new_gem is not None:
                card_def['gemsCost'].append(new_gem)
                outstanding -= 1
            # print(name, outstanding, card_def['tribes'], card_def['gemsCost'])

        if outstanding > 0:
            outstanding = int(outstanding)
            # print(outstanding, card_def['gemsCost'], outstanding)
            card_def['gemsCost'] += ['Green', 'Orange', 'Blue'][:outstanding]

        card_def['gemsCost'] = list(set(filter(bool, card_def['gemsCost'])))
        card_def['gemsCost'] = sorted(card_def['gemsCost'])
        # print(name, outstanding, card_def['tribes'], card_def['gemsCost'])

        card_def['bloodCost'] = 0
        card_def['bonesCost'] = 0

    # Workarounds
    if temple in ['Tech', 'Undead', 'Wizard']:
        # card_def['temple'] = 'Tech'
        # TODO: Evolve into and tail cards still have tribes since those fields aren't
        # namespace-replaced
        card_def['tribes'] = []  # Workaround https://github.com/Cosmiscient/P03KayceeMod-Main/issues/13

    card_def = {
        **card_def,
        **exjson,
    }

    return card_def


if __name__ == "__main__":
    main()