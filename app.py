from flask import Flask, jsonify, abort, request
# from flask import jsonify
from diplomacy import Game
from diplomacy.utils.export import to_saved_game_format, from_saved_game_format
import json
import base64

app = Flask(__name__)

# TODO: Make an issue about the timestamp. It seems to be off time by one hour even though my timezone is configured correctly
# TODO: Minify JSON Output
# TODO: Minify SVG Output (at least Whitespace)

# A list of valid variants
valid_variants = ['standard']
version = 'v0.2'


@app.route('/'+ version + '/variants')
def variants():
    json_array = []
    for variant in valid_variants:
        game = Game(map_name=variant)
        json_array.append({
            "name": variant,
            "powers": list(game.get_map_power_names()),
            "end_of_game": game.win
            })

    return jsonify(json_array)

@app.route('/'+ version + '/adjudicate/<variant_name>')
def basic_instance(variant_name):
    if variant_name not in valid_variants:
        abort(404)
    game = Game(map_name=variant_name)
    # ! This could cause bugs, I'm not sure about the behaviour.
    game.rules = []
    savedGame = to_saved_game_format(game)
    return {
        "phase_type": game.phase_type,
        "phase_power_data": return_phase_data(game),
        "phase": game.map.phase_long(game.get_current_phase()),
        "svg_with_orders": "",
        "svg_adjudicated": game.render(incl_orders=False, incl_abbrev=True),
        "current_state_encoded": base64.b64encode(json.dumps(savedGame).encode()).decode(),
        "current_state": savedGame,
        "possible_orders": return_possible_orders(game),
    }


@app.route('/'+ version + '/adjudicate', methods=['POST'])
def adjudicator():
    if not request.is_json:
        abort(418, 'Please use Application Type JSON')
    jsonb = request.get_json()
    data = json.loads(base64.b64decode(jsonb["previous_state_encoded"]).decode())
    game = from_saved_game_format(data)
    game.clear_orders()
    game.rules = []
    for order in jsonb["orders"]:
        game.set_orders(order["power"], order["instructions"])
    previous_svg = game.render(incl_orders=True, incl_abbrev=True)
    game.process()
    adjudicated = game.render(incl_orders=True, incl_abbrev=True)
    savedGame = to_saved_game_format(game)
    return {
        "phase_type": game.phase_type,
        "phase_power_data": return_phase_data(game),
        "phase": game.map.phase_long(game.get_current_phase()),
        "svg_with_orders": previous_svg,
        "svg_adjudicated": adjudicated,
        "current_state_encoded": base64.b64encode(json.dumps(savedGame).encode()).decode(),
        "current_state": savedGame,
        "possible_orders": return_possible_orders(game)
    }


def return_possible_orders(game):
    # TODO: Better variable names, for now it does its job
    possible_orders = game.get_all_possible_orders()

    possibilities = []
    for power in game.get_map_power_names():
        loc = []
        dicto = {
            "name": power
        }
        units = []
        for loc in game.get_orderable_locations(power):
            cur = {
                "location": loc,
                "instructions": possible_orders[loc]
            }
            units.append(cur)
            # print(loc)
            # print(possible_orders[loc])
        dicto["units"] = units
        possibilities.append(dicto)
    return possibilities

def return_phase_data(game):
    # TODO: Better variable names, for now it does its job

    possibilities = []
    for power in game.powers:
        p = game.powers[power]
        dicto = {
            "name": p.name,
            "unit_count": len(p.units),
            "supply_centers_count": len(p.centers),
            "home_centers_count": len(p.homes)
        }
        possibilities.append(dicto)
    return possibilities


