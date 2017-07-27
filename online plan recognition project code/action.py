from collections import OrderedDict


# Action representation for the Domain_Info class
# Main values are index, validity, a list of preconditions, and a list of effects
class Action:

    def __init__(self, data, predicat_dict, index):
        self.index=index
        self.valid = False
        self.precondition = []
        self.effect = []
        self.is_compressed = False
        for v in range(data.__len__()):
            if "action" in data[v]:
                self.name = data[v].split(" ")[1].replace("( ","").replace(" )","")
            elif "parameters" in data[v]:
                self.parameters = []
                while not "precondition" in data[v+1]:
                    self.parameters.append(data[v].replace("( ","").replace(" )",""))
                    v += 1
            elif "precondition" in data[v]:
                v += 2
                while not "effect" in data[v+1] and "" != data[v]:
                    self.precondition.append(data[v].replace("( ","").replace(" )",""))
                    v += 1
            elif "effect" in data[v]:
                v += 2
                while "" != data[v]:
                    name_str = data[v].replace("( ","").replace(" )","")
                    self.effect.append(name_str)
                    name_str = " " + name_str.replace("(not ", "").strip() + " "
                    predicat_obj = predicat_dict.get(name_str)
                    v += 1
                    if predicat_obj is None:
                        continue
                    predicat_obj.possible_actions.append(self.name)
            self.times_visited = 0


# Predicates representation for the Domain_Info class
class Predicates:

    def __init__(self, data, index):
        self.index = index
        self.possible_actions = []
        if "NOT" in data:
            self.valid = True
            self.name = data.replace("(not ","").replace("))",")")
        else:
            self.valid = False
            self.name = data
        self.times_visited = 0

    def invert_valid_state(self):
        # if self.valid:
            self.valid = False
        # else:
        #     self.valid = True


class Compressed_Action:

    def __init__(self, actions_list):
        self.actions_objs = actions_list
        self.index = actions_list[0].index * -1
        self.name = actions_list[0].name
        all_preconditions = []
        for action in actions_list:
            for precondition in action.precondition:
                all_preconditions.append(precondition)
        all_preconditions = list(OrderedDict.fromkeys(all_preconditions))
        self.precondition = all_preconditions
