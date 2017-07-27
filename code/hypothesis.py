import sys, os

import math
from collections import OrderedDict

import planners, translation
import linecache
import problems_info


count = -1


def save_sol_file(id, index, type, obs_index = -1):
	entries = os.listdir(os.getcwd())

	from_path = os.getcwd()+"/"
	to_path = os.getcwd()+"/results/solution_files/"
	if obs_index == -1:
		name = str(index) + "_" + str(id) + "_" + type + "_pr-problem.soln"
	else:
		name = "obs_" + str(obs_index) + "_hyp_" + str(index) + "_" + str(id) + "_" + type + "_pr-problem.soln"

	folder_name = from_path + "/results/solution_files"
	if not os.path.exists(folder_name):
		os.makedirs(folder_name, mode=0777)

	# entries = os.listdir(to_path)
	# if name in entries:
	# 	name = "1_" + name


	command = "cp " + from_path + "pr-problem.soln " + to_path + name
	os.system(command)


# incrementally editing obs.dat according to current iteration
def modify_obs_file(count):
	lines = []
	for i in range(count+1):
		line = linecache.getline('obs.dat', i + 1)
		obs_line = line.replace('(', '( ')
		obs_line = obs_line.replace(')', ' )')
		lines.append(obs_line)

	with open(os.getcwd() + "/obs.dat", "w") as outstream:
		for line in lines:
			outstream.write(line)
	pass


class Probabilistic :
	
	def __init__( self ) :
		# global planner_name
		self.atoms = []
		self.cost_O = 0.0
		self.cost_Not_O = 0.0
		self.Delta_O = 0.0
		self.Delta_Not_O = 0.0
		self.Probability_O = 0.0
		self.Probability_Not_O = 0.0
		self.Plan_Time_O = 0.0
		self.Plan_Time_Not_O = 0.0
		self.solvable = True
		self.plan = []
		self.test_failed = False
		self.trans_time = 0.0
		self.plan_time = 0.0
		self.total_time = 0.0
		self.is_true = True
		self.reason = ""
		self.curr_obs_num = 0
		self.path = []
		self.offline_ideal_cost = 0
		self.domain = None
		self.VK_rank = 0.0

		path = os.getcwd()
		instream = open(path + "/results/used_planner.txt", 'r')
		planner_name = instream.readline()

		if planner_name == "LAMA" or planner_name == "Greedy_LAMA":
			self.greedy = True
		else:
			self.greedy = False
		self.name= planner_name
		self.f=0

	# EXPLAIN: creates a list of the entry, domain_path, instance_path from a directory
	def walk( self, dir ) :
		entries = os.listdir( dir )
		for entry in entries :
			domain_path = os.path.join( entry, 'pr-domain.pddl' )
			domain_path = os.path.join( dir, domain_path )
			instance_path = os.path.join( entry, 'pr-problem.pddl' )
			instance_path = os.path.join( dir, instance_path )
			yield entry, domain_path, instance_path

	def test_for_sim( self, index, options  ) :
		import math, csv
		#EXPLAIN: definition 1, (Ramirez & Geffner 2010)
		# generate the problem with G=H
		hyp_problem = 'hyp_%d_problem.pddl'%index
		self.generate_pddl_for_hyp_plan( hyp_problem )
		# EXPLAIN: definition 2, (Ramirez & Geffner 2010)
		# derive problem with G_Obs
		trans_cmd = translation.Probabilistic_PR( 'domain.pddl', hyp_problem, 'obs.dat' )
		#trans_cmd.convert_to_integers = True
		trans_cmd.factor = 1000.0
		trans_cmd.execute()
		self.trans_time = trans_cmd.time
		os.system( 'mv prob-PR prob-%s-PR'%index )
		self.costs = dict()
		G_Obs_time = 0.0
		min_cost = 1e7

		# EXPLAIN: creates a propriate planner according to the flags in option.py file
		for id, domain, instance in self.walk( 'prob-%s-PR'%index ) :	
			if options.optimal :	
				plan_for_G_Obs_cmd = planners.H2( domain, instance, index, options.max_time, options.max_memory )
			else :
				if options.use_hspr :
					plan_for_G_Obs_cmd = planners.HSPr( domain, instance, index, options.max_time, options.max_memory )
				elif options.use_FF :
					plan_for_G_Obs_cmd = planners.Metric_FF( domain, instance, index, options.max_time, options.max_memory )	
				else :
					plan_for_G_Obs_cmd = planners.LAMA( domain, instance, index, options.max_time, options.max_memory )
					self.greedy = True
			# EXPLAIN: run the planner
			plan_for_G_Obs_cmd.execute()
			# EXPLAIN: return if failes
			if plan_for_G_Obs_cmd.signal != 0 and plan_for_G_Obs_cmd.signal != 256:
				self.test_failed = True
				return
			# EXPLAIN: not failed, update time
			G_Obs_time += plan_for_G_Obs_cmd.time
			# EXPLAIN: calculate plans with obs
			if id == 'O' :
				self.Plan_Time_O = plan_for_G_Obs_cmd.time
				if self.greedy:
					if not os.path.exists("temp_results/ideal_temp_files/soln_files"):
						os.makedirs("temp_results/ideal_temp_files/soln_files", mode=0777)
					command = "cp pr-problem.soln temp_results/ideal_temp_files/soln_files/pr-problem_" + str(
						index) + ".soln"
					os.system(command)
			# EXPLAIN: calculate complimentory plans (without obs)
			if id == 'neg-O' : self.Plan_Time_Not_O = plan_for_G_Obs_cmd.time
			# EXPLAIN: update minimal cost
			self.costs[id] = plan_for_G_Obs_cmd.cost / trans_cmd.factor
			if self.costs[id]  < min_cost : 
				min_cost = self.costs[id]
			
		print >> sys.stdout, "Min Cost:", min_cost
		print >> sys.stdout, "Costs:", self.costs
		self.plan_time = G_Obs_time
		self.total_time = trans_cmd.time + self.plan_time

		# EXPLAIN: definition 4 and 5, (Ramirez & Geffner 2010)
		# P(O|G) / P( \neg O | G) = exp { -beta Delta(G,O) }
		# Delta(G,O) = cost(G,O) - cost(G,\neg O)
		# EXPLAIN: delta(G|O)
		try:
			likelihood_ratio = math.exp(-options.beta * (self.costs['O'] - self.costs['neg-O']))
		except Exception:
			likelihood_ratio = 0
		# likelihood_ratio = math.exp( -options.beta*(self.costs['O']-self.costs['neg-O']) )
		# P(O|G) =  exp { -beta Delta(G,O) } / 1 + exp { -beta Delta(G,O) }
		# EXPLAIN: (O|G)
		self.Probability_O = likelihood_ratio / ( 1.0 + likelihood_ratio )
		# EXPLAIN: (NEG-O|G)
		self.Probability_Not_O = 1.0 - self.Probability_O		

		self.cost_O = self.costs['O']
		self.cost_Not_O = self.costs['neg-O']

	# original test function modified to suit online running
	def test_online( self, index, obs_index, max_time, max_mem, optimal = False, beta = 1.0) :
		# generate the problem with G=H
		hyp_problem = 'hyp_%d_problem.pddl'%index
		self.generate_pddl_for_hyp_plan( hyp_problem )
		global count
		if obs_index > count:
			count += 1
			self.curr_obs_num = count+1
			modify_obs_file(count)
		# creating the derived problem with G_Obs
		trans_cmd = translation.Probabilistic_PR('domain.pddl', hyp_problem, 'obs.dat')
		trans_cmd.execute()

		self.trans_time = trans_cmd.time
		os.system( 'mv prob-PR prob-%s-PR'%index )
		self.costs = dict()
		G_Obs_time = 0.0
		min_cost = 1e7
		time_bound = max_time

		# modifying init in pr_domain
		for id, domain, instance in self.walk('prob-%s-PR' % index):
			if id == 'O':
				self.modify_init_pr_problem_file(self.domain, instance)

		if optimal :
			time_bound = max_time / 2

			for id, domain, instance in self.walk( 'prob-%s-PR'%index ) :
				plan_for_G_Obs_cmd = planners.HSP( domain, instance, index, time_bound, max_mem )
				plan_for_G_Obs_cmd.execute()
				if id == 'O' :
					self.Plan_Time_O = plan_for_G_Obs_cmd.time
					if self.greedy:
						if not os.path.exists("temp_results/ideal_temp_files/soln_files"):
							os.makedirs("temp_results/ideal_temp_files/soln_files", mode=0777)
						command = "cp pr-problem.soln temp_results/ideal_temp_files/soln_files/pr-problem_" + str(index) + ".soln"
						os.system(command)
				if id == 'neg-O' : self.Plan_Time_Not_O = plan_for_G_Obs_cmd.time

				G_Obs_time += plan_for_G_Obs_cmd.time
				self.costs[id] = plan_for_G_Obs_cmd.cost
				if plan_for_G_Obs_cmd.cost < min_cost :
					min_cost = plan_for_G_Obs_cmd.cost
				# Save solution files
				if id == 'O' or id == 'neg-O':
					save_sol_file(id, index, "online", obs_index)
			self.path = plan_for_G_Obs_cmd.get_plan()
		if not optimal :
			#time_bound = max_time / 3
			#plan_for_G_cmd = planners.LAMA( 'domain.pddl', hyp_problem, index, time_bound, max_mem )
			#plan_for_G_cmd.execute()
			#if plan_for_G_cmd.cost < min_cost :
			#	min_cost = plan_for_G_cmd.cost
			#remainder = time_bound - plan_for_G_cmd.time
			#print >> sys.stdout, "Time remaining:", time_bound

			#if remainder > 0 :
			#	time_bound = (max_time / 3 ) + (remainder / 2 ) 
			time_bound = max_time / 2
			for id, domain, instance in self.walk( 'prob-%s-PR'%index ) :
				plan_for_G_Obs_cmd = planners.LAMA( domain, instance, index, time_bound, max_mem )
				plan_for_G_Obs_cmd.execute()
				G_Obs_time += plan_for_G_Obs_cmd.time
				if id == 'O' :
					self.Plan_Time_O = plan_for_G_Obs_cmd.time
					if self.greedy:
						if not os.path.exists("temp_results/ideal_temp_files/soln_files"):
							os.makedirs("temp_results/ideal_temp_files/soln_files", mode=0777)
						command = "cp pr-problem.soln temp_results/ideal_temp_files/soln_files/pr-problem_" + str(
							index) + ".soln"
						os.system(command)
				if id == 'neg-O' : self.Plan_Time_Not_O = plan_for_G_Obs_cmd.time
				remainder = time_bound - plan_for_G_Obs_cmd.time
				if remainder > 0 :
					time_bound = time_bound + remainder
				self.costs[id] = plan_for_G_Obs_cmd.cost
				if plan_for_G_Obs_cmd.cost < min_cost :
					min_cost = plan_for_G_Obs_cmd.cost

				# Save solution files
				if id == 'O' or id == 'neg-O':
					save_sol_file(id, index, "online", obs_index)

		self.plan_time = G_Obs_time
		self.total_time = trans_cmd.time + self.plan_time

		# P(O|G) / P( \neg O | G) = exp { -beta Delta(G,O) }
		# Delta(G,O) = cost(G,O) - cost(G,\neg O)
		try:
			likelihood_ratio = math.exp(-beta * (self.costs['O'] - self.costs['neg-O']))
		except Exception:
			likelihood_ratio = 0



		# likelihood_ratio = math.exp( -beta*(self.costs['O']-self.costs['neg-O']) )
		# P(O|G) =  exp { -beta Delta(G,O) } / 1 + exp { -beta Delta(G,O) }
		self.Probability_O = likelihood_ratio / ( 1.0 + likelihood_ratio )
		self.Probability_Not_O = 1.0 - self.Probability_O		

		self.cost_O = self.costs['O']
		self.cost_Not_O = self.costs['neg-O']

		if "H" in self.name:
			path = os.getcwd() + "/" + 'pr-problem.soln'
			self.offline_ideal_cost = self.get_greedy_cost(path, self.name)


	def test_offline( self, index, max_time, max_mem, optimal = False, beta = 1.0) :
		# EXPLAIN: definition 1, (Ramirez & Geffner 2010)
		# generate the problem with G=H
		hyp_problem = 'hyp_%d_problem.pddl'%index
		self.generate_pddl_for_hyp_plan( hyp_problem )
		# EXPLAIN: definition 2, (Ramirez & Geffner 2010)
		# derive problem with G_Obs
		trans_cmd = translation.Probabilistic_PR( 'domain.pddl', hyp_problem, 'obs.dat' )
		trans_cmd.execute()

		# if "H" in self.name:
		# 	path = os.getcwd() + "/" + 'pr-problem.soln'
		# 	self.offline_ideal_cost = self.get_greedy_cost(path, self.name)



		# plan_decifer = decipher.run()
		self.trans_time = trans_cmd.time
		os.system( 'mv prob-PR prob-%s-PR'%index )
		self.costs = dict()
		G_Obs_time = 0.0
		min_cost = 1e7
		# soln_flag=False
		time_bound = max_time
		# EXPLAIN: if optimal flag in options.py was risen
		if optimal :
			time_bound = max_time / 2
			for id, domain, instance in self.walk( 'prob-%s-PR'%index ) :
				# EXPLAIN: creates an HSP planner
				plan_for_G_Obs_cmd = planners.HSP( domain, instance, index, time_bound, max_mem )
				# EXPLAIN: run the planner
				plan_for_G_Obs_cmd.execute()
				# EXPLAIN: calculate plans with obs
				if id == 'O' :
					self.Plan_Time_O = plan_for_G_Obs_cmd.time
				# EXPLAIN: calculate complimentory plans (without obs)
				if id == 'neg-O' :
					self.Plan_Time_Not_O = plan_for_G_Obs_cmd.time
					soln_flag=True
				# EXPLAIN: update time
				G_Obs_time += plan_for_G_Obs_cmd.time
				self.costs[id] = plan_for_G_Obs_cmd.cost
				# EXPLAIN: update minimal cost
				if plan_for_G_Obs_cmd.cost < min_cost :
					min_cost = plan_for_G_Obs_cmd.cost
				# Save solution files
				if id == 'O' or id == 'neg-O':
					save_sol_file(id, index, "offline")
		# if soln_flag:
		# 	self.load_plan("pr-problem.soln")
		# 	soln_flag=False
		# EXPLAIN: if optimal flag in options.py was not risen
		if not optimal :
			# time_bound = max_time / 3
			# plan_for_G_cmd = planners.LAMA( 'domain.pddl', hyp_problem, index, time_bound, max_mem )
			# plan_for_G_cmd.execute()
			# if plan_for_G_cmd.cost < min_cost :
			#	min_cost = plan_for_G_cmd.cost
			# remainder = time_bound - plan_for_G_cmd.time
			# print >> sys.stdout, "Time remaining:", time_bound

			# if remainder > 0 :
			#	time_bound = (max_time / 3 ) + (remainder / 2 )
			time_bound = max_time / 2
			# EXPLAIN: creates an LAMA planner
			for id, domain, instance in self.walk( 'prob-%s-PR'%index ) :
				plan_for_G_Obs_cmd = planners.LAMA( domain, instance, index, time_bound, max_mem )
				# EXPLAIN: run the planner
				plan_for_G_Obs_cmd.execute()
				# EXPLAIN: not failed, update time
				G_Obs_time += plan_for_G_Obs_cmd.time
				# EXPLAIN: calculate plans with obs
				if id == 'O' :
					self.Plan_Time_O = plan_for_G_Obs_cmd.time
				# EXPLAIN: calculate complimentory plans (without obs)
				if id == 'neg-O' : self.Plan_Time_Not_O = plan_for_G_Obs_cmd.time
				remainder = time_bound - plan_for_G_Obs_cmd.time
				if remainder > 0 :
					time_bound = time_bound + remainder
				# EXPLAIN: update minimal cost
				self.costs[id] = plan_for_G_Obs_cmd.cost
				if plan_for_G_Obs_cmd.cost < min_cost :
					min_cost = plan_for_G_Obs_cmd.cost

				# Save solution files
				if id == 'O' or id == 'neg-O':
					save_sol_file(id, index, "offline")

		self.plan_time = G_Obs_time
		self.total_time = trans_cmd.time + self.plan_time



		# EXPLAIN: definition 4 and 5, (Ramirez & Geffner 2010)
		# P(O|G) / P( \neg O | G) = exp { -beta Delta(G,O) }
		# Delta(G,O) = cost(G,O) - cost(G,\neg O)
		# EXPLAIN: delta(G|O)
		try:
			likelihood_ratio = math.exp(-beta * (self.costs['O'] - self.costs['neg-O']))
		except Exception:
			likelihood_ratio = 0
		# likelihood_ratio = math.exp( -beta*(self.costs['O']-self.costs['neg-O']) )
		# P(O|G) =  exp { -beta Delta(G,O) } / 1 + exp { -beta Delta(G,O) }
		# EXPLAIN: (O|G)
		self.Probability_O = likelihood_ratio / ( 1.0 + likelihood_ratio )
		# EXPLAIN: (NEG-O|G)
		self.Probability_Not_O = 1.0 - self.Probability_O

		self.cost_O = self.costs['O']
		self.cost_Not_O = self.costs['neg-O']

		if "H" in self.name:
			path = os.getcwd() + "/" + 'pr-problem.soln'
			self.offline_ideal_cost = self.get_greedy_cost(path, self.name)

	def load_plan( self, plan_name ) :
		instream = open( plan_name )
		self.plan = []
		for line in instream :
			line = line.strip()
			if line[0] == ';' : continue
			_, _, stuff = line.partition(':')
			op, _, _ = stuff.partition('[')
			# _, _, stuff = custom_partition( line, ':' )
			# op, _, _ = custom_partition( stuff, '[' )
			self.plan.append( op.strip().upper() )	
		instream.close()

	# EXPLAIN: writes line by line to out_name.file.
	# if '<HYPOTHESIS>' is in the line writes its atoms to the file. else, writes the line
	def generate_pddl_for_hyp_plan( self, out_name ) :
		instream = open( 'template.pddl' )
		outstream = open( out_name, 'w' )

		for line in instream :
			line = line.strip()
			if '<HYPOTHESIS>' not in line :
				print >> outstream, line
			else :
				for atom in self.atoms :
					print >> outstream, atom
		# able to insert number of goals here (atoms)
		outstream.close()
		instream.close()

	# EXPLAIN: checks if there are atoms and update the is-true private of the probablistic obj
	def check_if_actual( self ) :
		real_hyp_atoms = []
		instream = open( 'real_hyp.dat' )
		for line in instream :
			real_hyp_atoms = [ tok.strip() for tok in line.split(',') ]
		instream.close()

		for atom in real_hyp_atoms :
			if not atom in self.atoms :
				self.is_true = False
				break
	def make_pr_domain_file(self):
		hyp_problem = 'hyp_%d_problem.pddl' % 9999
		self.generate_pddl_for_hyp_plan(hyp_problem)
		# EXPLAIN: definition 2, (Ramirez & Geffner 2010)
		# derive problem with G_Obs
		trans_cmd = translation.Probabilistic_PR('domain.pddl', hyp_problem, 'obs.dat')
		trans_cmd.execute()

		path= os.getcwd()+"/prob-PR/O/pr-domain.pddl  " +os.getcwd()
		os.system("mv " + path)
		path = os.getcwd() + "/prob-PR/O/pr-problem.pddl  " + os.getcwd()
		os.system("mv " + path)
		# erase folder after done unpacking
		os.system("rm " + "prob-PR")

	def get_greedy_cost(self, path, planner_name):
		cost = -1
		if "LAMA" in planner_name:
			with open(path) as instream:
				for line in instream:
					if 'cost:' in line:
						cost = line.split('cost: ')[1]
						cost = cost.replace('.', "").replace('\n', "")
						break
			return int(cost)
		elif "H" in planner_name:
			with open(path) as instream:
				for line in instream:
					if 'MetricValue' in line:
						cost = line.split('MetricValue ')[1]
						cost = cost.replace('\n', "")
						break
			return int(cost)

	def modify_init_pr_problem_file(self, domain, path_to_problem_file):
		# open the problem file for modifications
		with open (path_to_problem_file) as prDomainFile:
			lines = prDomainFile.readlines()
			init = []
			new_init = []
			obs=[]
			effects=[]
			predicates_to_remove=[]
			new_file=""
			# get the init satates in order to modify them
			for i in range(lines.__len__()):
				line = lines[i]
				if "(:init" in line:
					while "(" in lines[i]:
						i += 1
						init.append(lines[i].replace("\t(", "").replace(")\n", "").replace("\t", ""))
					init.pop()
			# get the obs actions in order to get the relevant preconditions for init
			for i in range(count + 1):
				line = linecache.getline('obs.dat', i + 1)
				obs_line = line.replace('(', '( ')
				obs_line = obs_line.replace(')', ' )')
				obs.append(obs_line)
			# get the effects of the obs
			for o in obs:
				o = o.replace('( ','').replace(" )\n", "")
				o = "EXPLAIN_OBS_" + o.replace(" ","_") + "_1"
				action = domain.actions_dict.get(o)
				if action is None:
					print 'damn'
				else:
					for a in action[0].effect:
						effects.append(a)
			effects = list(OrderedDict.fromkeys(effects))
			effects.remove('increase (total-cost) 1')
			# the contradicting preconditions
			for o in obs:
				o = o.replace('( ', '').replace(" )\n", "")
				o = "NOT_EXPLAINED_" + o.replace(" ", "_") + "_1"
				predicates_to_remove.append(o)
			# remove the contradicting predicates
			for line in init:
				for p in predicates_to_remove:
					if not line.strip() == p:
						if line == ' NOT_EXPLAINED_FULL_OBS_SEQUENCE ':
							new_init.append('EXPLAINED_FULL_OBS_SEQUENCE')
						else:
							new_init.append(line)
			# add the effect of the obs to init
			new_init = new_init[:1] + effects + new_init[1:]

			init = []

			# formating the new init
			for l in new_init:
				if "not" in l:
					l = "\t\t" + l.replace("(not","(not (") + " ))\n"
					# init.append(l)
				else:
					l= "\t\t( " + l + " )\n"
					init.append(l)
			init.append("\t)\n")

			# create the new file
			for i, val in enumerate(lines):
				# write the lines till init
				while lines[i] != '	(:init\n':
					new_file += lines[i]
					i+=1
				# write the line of init
				new_file+=lines[i]
				# write the new init state
				for l in init:
					new_file += l
				# precede the index to the goal line
				while lines[i] != '	(:goal\n':
					i+=1
				# write the line of goal to the end
				for i in range (i,lines.__len__()):
					new_file += lines[i]
				break
			# print "\n\n"+new_file

		# write the new file
		with open(path_to_problem_file, "w") as outstream:
			outstream.writelines(new_file)


		print 's';


