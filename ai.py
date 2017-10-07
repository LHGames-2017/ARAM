from __future__ import print_function
from flask import Flask, request
from structs import *
from copy import deepcopy
import json
import numpy as np
import astar


app = Flask(__name__)

def create_action(action_type, target):
    actionContent = ActionContent(action_type, target.__dict__)
    return json.dumps(actionContent.__dict__)

def create_move_action(target):
    return create_action("MoveAction", target)

def create_attack_action(target):
    return create_action("AttackAction", target)

def create_collect_action(target):
    return create_action("CollectAction", target)

def create_steal_action(target):
    return create_action("StealAction", target)

def create_heal_action():
    return create_action("HealAction", "")

def create_purchase_action(item):
    return create_action("PurchaseAction", item)

def deserialize_map(serialized_map):
    """
    Fonction utilitaire pour comprendre la map
    """
    serialized_map = serialized_map[1:]
    rows = serialized_map.split('[')
    column = rows[0].split('{')
    deserialized_map = [[Tile() for x in range(20)] for y in range(20)]
    for i in range(len(rows) - 1):
        column = rows[i + 1].split('{')

        for j in range(len(column) - 1):
            infos = column[j + 1].split(',')
            end_index = infos[2].find('}')
            content = int(infos[0])
            x = int(infos[1])
            y = int(infos[2][:end_index])
            deserialized_map[i][j] = Tile(content, x, y)

    return deserialized_map

def bot():
    """
    Main de votre bot.
    """
    print('debut du main')
    map_json = request.form["map"]

    # Player info
    encoded_map = map_json.encode()
    map_json = json.loads(encoded_map)
    p = map_json["Player"]
    pos = p["Position"]
    x = pos["X"]
    y = pos["Y"]
    house = p["HouseLocation"]
    player = Player(p["Health"], p["MaxHealth"], Point(x,y),
                    Point(house["X"], house["Y"]),
                    p["CarriedResources"], p["CarryingCapacity"])

    print('Player info')
    print('Position',pos)
    print('house pos',house)
    print()
    print('Player')
    print('Pos', 'x:', x, 'y:', y)
    print('health', p["Health"])
    print('maxhealth', p["MaxHealth"])
    print('ressources', p["CarriedResources"])
    print('capacity', p["CarryingCapacity"])

    # Map
    serialized_map = map_json["CustomSerializedMap"]
    deserialized_map = deserialize_map(serialized_map)

    print(serialized_map.replace('],','],\n'))

    #list of tiles
    wall_tiles = []
    house_tiles = []
    lava_tiles = []
    ressource_tiles = []
    shop_tiles = []

    astar_array = np.array([[0 for k in range(20)] for l in range(20)])

    for i, row in enumerate(deserialized_map[:20]):
        for j, item in enumerate(row[:20]):
            if item.Content in [1,3,5]:  
                astar_array[i][j] = 1

            if item.Content == 4:
                ressource_tiles.append((i,j))

            if item.Content == 2:
                house_tiles.append((i,j))

    print(*astar_array,sep='\n')


    pos_top_corner = (x - 10,y - 10)
    path = False
    r = 0

    if len(ressource_tiles) > 0 and p["CarriedResources"] < p["CarryingCapacity"]:
        while not path:
            pos_cible_rel = ressource_tiles[r]
            pos_cible_abs = (pos_cible_rel[0] + pos_top_corner[0], pos_cible_rel[1] + pos_top_corner[1])
            print("CIBLE : ", pos_cible_abs)

            path = astar.astar(astar_array,pos_cible_rel,(10,10))
            r += 1
            
        if path:
            if len(path) > 1:
                prochain_dep = Point(path[1][0] - 10, path[1][1] - 10)
                a = create_move_action(Point(x + prochain_dep.X, y + prochain_dep.Y))
            else:
                a = create_collect_action(Point(pos_cible_abs[0], pos_cible_abs[1]))
        else:
            print("pas de chemin vers les ressources")
            a = create_move_action(Point(x,y))
            
        
    else: #rentrer chez nous
        pos_cible_abs = p["HouseLocation"]
        pos_cible_rel = house_tiles[0]
        print("CIBLE : ", pos_cible_abs)

        path = astar.astar(astar_array,pos_cible_rel,(10,10))

        if path:
            if len(path) > 1:
                prochain_dep = Point(path[1][0] - 10, path[1][1] - 10)
                a = create_move_action(Point(x + prochain_dep.X, y + prochain_dep.Y))
        else:
            print("pas de chemin vers la maison")
            a = create_move_action(Point(x,y))
     

        
    
    print(path)


    #find other players Contient des bugs
    
    otherPlayers = []

    for player_dict in map_json["OtherPlayers"]:
        for player_name in player_dict.keys():
            player_info = player_dict[player_name]
            p_pos = player_info["Position"]
            player_info = PlayerInfo(player_info["Health"],
                                     player_info["MaxHealth"],
                                     Point(p_pos["X"], p_pos["Y"]))

            otherPlayers.append({player_name: player_info })
    

    print('Wall')
    print(wall_tiles)
    print('House')
    print(house_tiles)
    print('Lava')
    print(lava_tiles)
    print('Ressource')
    print(ressource_tiles)
    print('Shop')
    print(shop_tiles)

    # return decision
    print('Fin du Main\n')       
    print(a)
    return a

@app.route("/", methods=["POST"])
def reponse():
    """
    Point d'entree appelle par le GameServer
    """
    return bot()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
