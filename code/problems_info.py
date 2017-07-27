import linecache
import os
import re
from collections import OrderedDict

import planners
import translation
from action import Action, Predicates, Compressed_Action

ROOT_DIR = os.getcwd()

class Domain_info:
    def __init__(self, domain_name, hyps=[]):
        self.domain_name = domain_name
        self.has_duplicates = False

        self.actions = []
        self.predicates = []
        self.actions_dict = {}
        self.predicates_dict = {}

        # actions done in hyp path
        self.fulfilled_actions = []
        self.fulfilled_predicates = []
        self.seen_in_path_actions = []
        self.actions_in_cost = []
        self.cost = 0
        # actions done in obs path
        self.obs_fulfilled_actions = []
        self.obs_fulfilled_predicates = []
        self.obs_seen_actions = []
        self.obs_in_cost = []
        self.obs_in_process_actions = []
        self.obs_in_process_preconditions = []
        self.obs_cost = 0

        self.data_saved = {}
        self.temp_fullfilled = []
        self.in_process_actions = []
        self.in_process_preconditions = []

        # creating full pr-domain file
        trans_cmd = translation.Probabilistic_PR('domain.pddl', 'pr-domain.pddl', 'obs.dat')
        trans_cmd.execute()
        # parse the domain to our format
        if "intrusion" in domain_name or "block" in domain_name:
            self.intrusion()
        elif "easy" in domain_name or "bui" in domain_name or "logistics" in domain_name:
            self.easy()

    def intrusion(self):
        actions = []
        predicates = []
        f = ROOT_DIR
        with open(ROOT_DIR + "/pr-domain.pddl") as prDomainFile:
            lines = prDomainFile.readlines()

            for i in range(lines.__len__()):
                line = lines[i]
                if "(:predicates" in line:
                    while "(" in lines[i]:
                        i += 1
                        predicates.append(lines[i].replace("\t(", "").replace(")\n", "").replace("\t", ""))
                if ":action " in line:
                    temp_actions = []
                    while not lines[i].__eq__("\t)\n"):
                        temp_actions.append(
                            lines[i].replace("\t(", "").replace(")\n", "").replace(") \n", "").replace("\n",
                                                                                                       "").replace("\t",
                                                                                                                   ""))
                        i += 1
                    actions.append(temp_actions)
            predicates.pop()

            # creating predicate dictionary
            i = 0
            for p in predicates:
                ob = Predicates(p, i)
                self.predicates.append(ob)
                self.predicates_dict[ob.name] = ob
                i += 1

            # creating action dictionary
            i = 0
            for a in actions:
                ob = Action(a, self.predicates_dict, i)
                # check if there are action duplicates, if there are raise a flag
                if ob.name in self.actions_dict:
                    self.has_duplicates = True
                self.actions.append(ob)
                if self.actions_dict.get(ob.name) is None:
                    self.actions_dict[ob.name] = [ob]
                else:
                    self.actions_dict.get(ob.name).append(ob)
                i += 1

    def easy(self):
        actions = []
        predicates = []

        with open(os.getcwd() + "/pr-domain.pddl") as prDomainFile:
            lines = prDomainFile.readlines()

            for i in range(lines.__len__()):
                line = lines[i]
                if "(:predicates" in line:
                    while "(" in lines[i]:
                        i += 1
                        s = lines[i].replace("\t(", "").replace(")\n", "").replace("\t", "")
                        predicates.append(lines[i].replace("\t(", "").replace(")\n", "").replace("\t", ""))
                if ":action " in line:
                    temp_actions = []
                    while not lines[i].__eq__("\t)\n"):
                        temp = lines[i].replace("\t(", "").replace(")\n", "").replace(") \n", "").replace("\n",
                                                                                                          "").replace(
                            "\t", "").replace(" (", "").replace(")", "")
                        if "not" in temp:
                            temp = temp.replace("not", "(not ")
                        temp_actions.append(temp)
                        i += 1
                    actions.append(temp_actions)
            predicates.pop()

            # creating predicate dictionary
            i = 0
            for p in predicates:
                ob = Predicates(p, i)
                self.predicates.append(ob)
                self.predicates_dict[ob.name] = ob
                i += 1

            # creating action dictionary
            i = 0
            for a in actions:
                ob = Action(a, self.predicates_dict, i)
                # check if there are action duplicates, if there are raise a flag
                if ob.name in self.actions_dict:
                    self.has_duplicates = True
                self.actions.append(ob)
                if self.actions_dict.get(ob.name) is None:
                    self.actions_dict[ob.name] = [ob]
                else:
                    self.actions_dict.get(ob.name).append(ob)
                i += 1

    def get_init_preconds(self):
        # mark the init preconditions as valid
        with open(os.getcwd() + "/pr-problem.pddl") as instream:
            instream = instream.readlines()
            for line in range(instream.__len__()):
                if "init" in instream[line]:
                    line += 2
                    while not "goal" in instream[line + 2]:
                        pre = instream[line].replace("(", "").replace(")", "").replace("(not ", "").replace("\t","").replace("\n", "")
                        precondition_object = self.predicates_dict.get(pre)
                        if precondition_object is None:
                            continue
                        precondition_object.valid = True
                        precondition_object.times_visited += 1
                        line += 1

    def save_data(self, j, i):
        # saves the data of the iteration
        spec_data = [self.cost, self.fulfilled_actions, self.in_process_preconditions, self.actions_in_cost]
        if j == -1:
            value = "offline_" + str(i)
        else:
            value = str(j) + "," + str(i)
        self.data_saved[value] = spec_data

        # initialization of the members of the domain object
        self.fulfilled_actions = []
        self.fulfilled_predicates = []
        self.seen_in_path_actions = []
        self.actions_in_cost = []
        self.in_process_actions = []
        self.in_process_preconditions = []

        pass

    def save_obs_data(self, j):
        # saves the data of the iteration
        spec_data = [self.obs_cost, self.obs_fulfilled_actions, self.obs_in_process_preconditions, self.obs_in_cost]
        value = str(j) + "_obs"
        self.data_saved[value] = spec_data

        # initialization of the members of the domain object
        self.obs_fulfilled_actions = []
        self.obs_fulfilled_predicates = []
        self.obs_seen_actions = []
        self.obs_in_cost = []
        self.obs_cost = 0

    def restart(self):
        # restart the domain (all to false)
        self.cost = 0

        for action in self.actions:
            if "NOT" in action.name:
                action.valid = True
            else:
                action.valid = False
        for predicate in self.predicates:
            predicate.valid = False

    def restart_obs(self):
        # restart the obs members in the domain object
        self.obs_seen_actions = []
        self.obs_fulfilled_actions = []
        self.obs_fulfilled_predicates = []

    def get_obs_predicates(self, obs_num):
        # mark the observed action and its preconditions as true
        obs_action_list = []

        with open(os.getcwd() + "/obs.rsc") as instream:
            for i in range(0, obs_num + 1):
                line = instream.readline()
                obs_action_list.append(line)
        # read the observations, if it exists mark as happened
        for o in obs_action_list:
            name = o.replace(" ", "_")
            name = name.replace("\n", "").replace("(", "").replace(")", "")
            name = "EXPLAIN_OBS_" + name + "_1"
            acts = self.actions_dict.get(name)
            for act in acts:
                if act is None:
                    continue
                for p in act.precondition:
                    p_obj = self.predicates_dict.get(p)
                    self.create_lists_obs(p_obj)
                # act.valid = True
                self.obs_fulfilled_actions.append(act)
            self.iterate_lists_obs()
        return

    def run_hyp(self, hype, obs=[]):
        # run over the atoms of the hyp
        atom_list = []
        for a in hype.atoms:
            temp = a.replace("(", "").replace(")", "")
            atom_list.append(temp)
        # initialize the init state of the predicates
        self.get_init_preconds()
        temp_pred_obj_list = self.predicates

        # do for all atoms in hyp
        for a in atom_list:
            for p in temp_pred_obj_list:
                name = p.name.lower().strip()
                if "easy" in self.domain_name:
                    a = a.replace(" ", "_")
                else:
                    name = name.replace("_", " ")
                if a == name:
                    # create a list of optional actions to pass by
                    self.create_lists(p)
                    # check the validity of the actions and do the effect if needed
                    self.iterate_lists()
        # remove redundancies in action list
        self.fulfilled_actions = list(OrderedDict.fromkeys(self.fulfilled_actions))
        # set the cost of the hyp as the number of the fulfilled actions
        self.cost = self.fulfilled_actions.__len__()

    def check_actions(self, possible_actions):
        # check if the action occurred
        precons = possible_actions.precondition
        for p in precons:
            invert_flag = False
            if "not" in p:
                invert_flag = True

            predicate_str = p.replace("(not ", "")
            p_obj = self.predicates_dict[predicate_str]

            if invert_flag:
                if p_obj.valid:
                    return False
                else:
                    return True
            else:
                if not p_obj.valid:
                    return False
                else:
                    return True

    def create_lists(self, input):
        # run recursively over the domain according to the domain pddl file
        self.in_process_preconditions.append(input)
        precondition_obj_list = []
        # find the actions which has the given predicate as an effect and insert it to a list and inserts the actions to path list
        path_actions = input.possible_actions

        # update fields of used predicates
        for action_str in path_actions:
            # find the action list to get the objects and insert them to a list
            action_objs = self.actions_dict.get(action_str)
            # if there are more than one action with this name
            if action_objs.__len__() > 1:
                action_obj = Compressed_Action(action_objs)
            else:
                action_obj = action_objs[0]
            if action_obj is None:
                continue

            # if there are duplicates it is necessary to prevent redundant exploiting of the action
            if self.has_duplicates:
                if action_obj in self.in_process_actions:
                    self.in_process_actions.append(action_obj)
                    continue

            self.in_process_actions.append(action_obj)

            # takes the preconditions of an action as an object
            for precondition_str in action_obj.precondition:
                temp_str = precondition_str.replace("(not ", "")
                precondition_obj = self.predicates_dict.get(temp_str)
                if precondition_obj is None:
                    continue
                self.in_process_preconditions.append(precondition_obj)
                precondition_obj_list.append(precondition_obj)

            # run the recursion
            precondition_obj_list = list(reversed(precondition_obj_list))
            for precond_obj in precondition_obj_list:
                self.create_lists(precond_obj)

        # remove redundancies in preconditions list
        from collections import OrderedDict
        self.in_process_preconditions = list(OrderedDict.fromkeys(self.in_process_preconditions))

    def iterate_lists(self):
        # run over the possible actions list and finds out which action really happened
        temp_actions_list = self.in_process_actions
        seen_actions = []
        # if there are duplicates insert them all
        for seen in temp_actions_list:
            if seen.index < 0:
                for action in seen.actions_objs:
                    seen_actions.append(action)
            else:
                seen_actions.append(seen)
        # reverse the list in order to start checking from the init state
        seen_actions = list(reversed(seen_actions))

        seen_preconditions = self.in_process_preconditions

        for o in seen_actions:
            print "hyp-" + str(o.name) + ":" + str(o.index)

        # checking validity of all actions
        for action in seen_actions:
            valid = True
            precond_list = action.precondition
            for precondition in precond_list:
                preco_obj = self.predicates_dict.get(precondition)
                if precond_list is None:
                    continue
                if preco_obj.valid is False:
                    valid = False
            if valid:
                action.valid = True
                self.fulfilled_actions.append(action)

                # set action effects as valid
                for effect in action.effect:
                    inverse = False
                    if "(not " in effect:
                        inverse = True
                        effect = " " + effect.replace("(not", "").strip() + " "

                    effect_obj = self.predicates_dict.get(effect)
                    if effect_obj is None:
                        continue
                    if inverse:
                        effect_obj.valid = False
                    else:
                        effect_obj.valid = True
        print "________________________________________________________"

    def create_lists_obs(self, input):
        self.obs_in_process_preconditions.append(input)
        precondition_obj_list = []
        # find the actions which has the given predicate as an effect and insert it to a list and inserts the actions to path list
        path_actions = input.possible_actions

        # update fields of used predicates
        for action_str in path_actions:
            action_objs = self.actions_dict.get(action_str)
            if action_objs.__len__() > 1:
                action_obj = Compressed_Action(action_objs)
            else:
                action_obj = action_objs[0]
            if action_obj is None:
                continue

            # if action_obj in self.obs_in_process_actions:
            #     self.obs_in_process_actions.append(action_obj)
            #     continue
            self.obs_in_process_actions.append(action_obj)

            action_is_valid = True
            # takes the preconditions of an action as an object
            for precondition_str in action_obj.precondition:
                temp_str = precondition_str.replace("(not ", "")
                precondition_obj = self.predicates_dict.get(temp_str)
                # if precondition_obj is None:
                if precondition_obj is None or precondition_obj in self.obs_in_process_preconditions:
                    continue
                self.obs_in_process_preconditions.append(precondition_obj)
                precondition_obj_list.append(precondition_obj)

            # run the reccursion
            for precond_obj in precondition_obj_list:
                self.create_lists_obs(precond_obj)

        from collections import OrderedDict
        self.obs_in_process_preconditions = list(OrderedDict.fromkeys(self.obs_in_process_preconditions))

    def iterate_lists_obs(self):
        # temp_actions_list = self.obs_in_process_actions
        # seen_actions = list(reversed(temp_actions_list))
        # # seen_actions = list(OrderedDict.fromkeys(seen_actions))
        seen_preconditions = self.obs_in_process_preconditions
        temp_actions_list = self.obs_in_process_actions
        seen_actions = []
        for seen in temp_actions_list:
            if seen.index < 0:
                for action in seen.actions_objs:
                    seen_actions.append(action)
            else:
                seen_actions.append(seen)
        seen_actions = list(reversed(seen_actions))

        for o in seen_actions:
            print "obs-" + str(o.name) + ":" + str(o.index)

        for action in seen_actions:
            if action.valid:
                continue

            valid = True
            precond_list = action.precondition
            for precondition in precond_list:
                preco_obj = self.predicates_dict.get(precondition)
                if precond_list is None:
                    continue
                if preco_obj.valid is False:
                    valid = False
            if valid:
                # if action not in self.obs_fulfilled_actions:
                #     print action.name + " : " + str(action.index)

                if "EXPLAIN_OBS" not in action.name:
                    action.valid = True
                    self.obs_fulfilled_actions.append(action)
                    self.obs_cost += 1

                # for effect in action.effect:
                #     effect_obj = self.predicates_dict.get(effect)
                #     if effect_obj is None:
                #         continue
                #     effect_obj.valid = True
                for effect in action.effect:
                    inverse = False
                    if "(not " in effect:
                        inverse = True
                        effect = " " + effect.replace("(not", "").strip() + " "

                    effect_obj = self.predicates_dict.get(effect)
                    if effect_obj is None:
                        continue
                    if inverse:
                        effect_obj.valid = False
                    else:
                        effect_obj.valid = True
        self.obs_fulfilled_actions = list(OrderedDict.fromkeys(self.obs_fulfilled_actions))

    def reset_dictionaries(self):
        # restart the dictionaries
        for actions in self.actions_dict:
            for action in self.actions_dict.get(actions):
                action.valid = False
        for predicate in self.predicates_dict:
            self.predicates_dict.get(predicate).valid = False

    def generate_pddl_for_obs_plan(self, obs):
        obs_preconditions=[]
        # get obs preconditions
        for o in obs:
            o = "EXPLAIN_OBS_"+o.replace(" ","_").replace("(","").replace(")","")+"_1"
            o_obj = self.actions_dict.get(o)
            if o_obj is None:
                continue
            temp_list=[]
            for p_str in o_obj[0].precondition:
                p_str="("+p_str.replace("_"," ").lower().strip()+")"
                if not "explained" in p_str:
                    temp_list.append(p_str)
                # temp_list.append(p_str)

            obs_preconditions.append(temp_list)

        for i in range(obs.__len__()):
            out_name="obs_"+str(i)+"_problem.pddl"
            instream = open('template.pddl')
            outstream = open(out_name, 'w')

            for line in instream:
                line = line.strip()
                if '<HYPOTHESIS>' not in line:
                    print >> outstream, line
                else:
                    if i>0:
                        for j in range(1,i+1):
                            for atom in obs_preconditions[j]:
                                print >> outstream, atom
                    else:
                        for atom in obs_preconditions[i]:
                            print >> outstream, atom
            # able to insert number of goals here (atoms)
            outstream.close()
            instream.close()

    def walk(self, dir):
        entries = os.listdir(dir)
        for entry in entries:
            domain_path = os.path.join(entry, 'pr-domain.pddl')
            domain_path = os.path.join(dir, domain_path)
            instance_path = os.path.join(entry, 'pr-problem.pddl')
            instance_path = os.path.join(dir, instance_path)
            yield entry, domain_path, instance_path

    def run_planner_on_obs(self, obs_index):
        # os.chdir(ROOT_DIR)
        obs_plans=[]
        obs_actions=[]
        for i in range(obs_index):
            hyp_problem = 'obs_%d_problem.pddl' % i

            self.modify_obs_file(i)
            # creating the derived problem with G_Obs
            trans_cmd = translation.Probabilistic_PR('domain.pddl', hyp_problem, 'obs.dat')
            trans_cmd.execute()

            os.system('mv prob-PR obs_prob-%s-PR' % i)

            for id, domain, instance in self.walk('obs_prob-%s-PR' % i):
                if id == "O":
                    plan_for_G_Obs_cmd = planners.HSP(domain, instance, i)
                    plan_for_G_Obs_cmd.execute()
                    obs_actions= plan_for_G_Obs_cmd.get_plan()
                    obs_plans.append(obs_actions)
        return obs_plans

    # incrementally editing obs.dat according to current iteration
    def modify_obs_file(self, count):
        lines = []
        for i in range(count + 1):
            line = linecache.getline('obs.dat', i + 1)
            obs_line = line.replace('(', '( ')
            obs_line = obs_line.replace(')', ' )')
            lines.append(obs_line)

        with open(os.getcwd() + "/obs.dat", "w") as outstream:
            for line in lines:
                outstream.write(line)
        pass