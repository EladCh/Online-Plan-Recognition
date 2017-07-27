import sys, os, benchmark
import planners, translation

class Probabilistic :
	
	def __init__( self ) :
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

	#EXPLAIN: creates a list of the entry, domain_path, instance_path from a direcory
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
		#EXPLAIN: definition 2, (Ramirez & Geffner 2010)
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

		#EXPLAIN: creates a propriate planner according to the flags in option.py file
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
			#EXPLAIN: run the planner
			plan_for_G_Obs_cmd.execute()
			#EXPLAIN: return if failes
			if plan_for_G_Obs_cmd.signal != 0 and plan_for_G_Obs_cmd.signal != 256:
				self.test_failed = True
				return
			#EXPLAIN: not failed, update time
			G_Obs_time += plan_for_G_Obs_cmd.time
			#EXPLAIN: calculate plans with obs
			if id == 'O' : self.Plan_Time_O = plan_for_G_Obs_cmd.time
			#EXPLAIN: calculate complimentory plans (without obs)
			if id == 'neg-O' : self.Plan_Time_Not_O = plan_for_G_Obs_cmd.time
			#EXPLAIN: update minimal cost
			self.costs[id] = plan_for_G_Obs_cmd.cost / trans_cmd.factor
			if self.costs[id]  < min_cost : 
				min_cost = self.costs[id]
			
		print >> sys.stdout, "Min Cost:", min_cost
		print >> sys.stdout, "Costs:", self.costs
		self.plan_time = G_Obs_time
		self.total_time = trans_cmd.time + self.plan_time

		#EXPLAIN: definition 4 and 5, (Ramirez & Geffner 2010)
		# P(O|G) / P( \neg O | G) = exp { -beta Delta(G,O) }
		# Delta(G,O) = cost(G,O) - cost(G,\neg O)
		#EXPLAIN: delta(G|O)
		likelihood_ratio = math.exp( -options.beta*(self.costs['O']-self.costs['neg-O']) )
		# P(O|G) =  exp { -beta Delta(G,O) } / 1 + exp { -beta Delta(G,O) }
		#EXPLAIN: (O|G)
		self.Probability_O = likelihood_ratio / ( 1.0 + likelihood_ratio ) 
		#EXPLAIN: (NEG-O|G)
		self.Probability_Not_O = 1.0 - self.Probability_O		

		self.cost_O = self.costs['O']
		self.cost_Not_O = self.costs['neg-O']
	

	def test( self, index, max_time, max_mem, optimal = False, beta = 1.0  ) :
		import math, csv
		#EXPLAIN: definition 1, (Ramirez & Geffner 2010)
		# generate the problem with G=H
		hyp_problem = 'hyp_%d_problem.pddl'%index
		self.generate_pddl_for_hyp_plan( hyp_problem )
		#EXPLAIN: definition 2, (Ramirez & Geffner 2010)
		# derive problem with G_Obs
		trans_cmd = translation.Probabilistic_PR( 'domain.pddl', hyp_problem, 'obs.dat' )
		trans_cmd.execute()
		self.trans_time = trans_cmd.time
		os.system( 'mv prob-PR prob-%s-PR'%index )
		self.costs = dict()
		G_Obs_time = 0.0
		min_cost = 1e7
		time_bound = max_time
		#EXPLAIN: if optimal flag in options.py was risen
		if optimal :
			time_bound = max_time / 2
			for id, domain, instance in self.walk( 'prob-%s-PR'%index ) :	
				#EXPLAIN: creates an HSP planner
				plan_for_G_Obs_cmd = planners.HSP( domain, instance, index, time_bound, max_mem )
				#EXPLAIN: run the planner
				plan_for_G_Obs_cmd.execute()
				#EXPLAIN: calculate plans with obs
				if id == 'O' : self.Plan_Time_O = plan_for_G_Obs_cmd.time
				#EXPLAIN: calculate complimentory plans (without obs)
				if id == 'neg-O' : self.Plan_Time_Not_O = plan_for_G_Obs_cmd.time
				#EXPLAIN: update time
				G_Obs_time += plan_for_G_Obs_cmd.time
				self.costs[id] = plan_for_G_Obs_cmd.cost
				#EXPLAIN: update minimal cost
				if plan_for_G_Obs_cmd.cost < min_cost :
					min_cost = plan_for_G_Obs_cmd.cost
		#EXPLAIN: if optimal flag in options.py was not risen
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
			#EXPLAIN: creates an LAMA planner
			for id, domain, instance in self.walk( 'prob-%s-PR'%index ) :	
				plan_for_G_Obs_cmd = planners.LAMA( domain, instance, index, time_bound, max_mem )
				#EXPLAIN: run the planner
				plan_for_G_Obs_cmd.execute()
				#EXPLAIN: not failed, update time
				G_Obs_time += plan_for_G_Obs_cmd.time
				#EXPLAIN: calculate plans with obs
				if id == 'O' : self.Plan_Time_O = plan_for_G_Obs_cmd.time
				#EXPLAIN: calculate complimentory plans (without obs)
				if id == 'neg-O' : self.Plan_Time_Not_O = plan_for_G_Obs_cmd.time
				remainder = time_bound - plan_for_G_Obs_cmd.time
				if remainder > 0 :
					time_bound = time_bound + remainder
				#EXPLAIN: update minimal cost
				self.costs[id] = plan_for_G_Obs_cmd.cost
				if plan_for_G_Obs_cmd.cost < min_cost :
					min_cost = plan_for_G_Obs_cmd.cost

		self.plan_time = G_Obs_time
		self.total_time = trans_cmd.time + self.plan_time

		#EXPLAIN: definition 4 and 5, (Ramirez & Geffner 2010)
		# P(O|G) / P( \neg O | G) = exp { -beta Delta(G,O) }
		# Delta(G,O) = cost(G,O) - cost(G,\neg O)
		#EXPLAIN: delta(G|O)
		likelihood_ratio = math.exp( -beta*(self.costs['O']-self.costs['neg-O']) )
		# P(O|G) =  exp { -beta Delta(G,O) } / 1 + exp { -beta Delta(G,O) }
		#EXPLAIN: (O|G)
		self.Probability_O = likelihood_ratio / ( 1.0 + likelihood_ratio ) 
		#EXPLAIN: (NEG-O|G)
		self.Probability_Not_O = 1.0 - self.Probability_O		

		self.cost_O = self.costs['O']
		self.cost_Not_O = self.costs['neg-O']

	def load_plan( self, plan_name ) :
		instream = open( plan_name )
		self.plan = []
		for line in instream :
			line = line.strip()
			if line[0] == ';' : continue
			#_, _, stuff = line.partition(':')
			#op, _, _ = stuff.partition('[')
			_, _, stuff = custom_partition( line, ':' )
			op, _, _ = custom_partition( stuff, '[' )
			self.plan.append( op.strip().upper() )	
		instream.close()


	#EXPLAIN: writes line by line to out_name.file.
	#if '<HYPOTHESIS>' is in the line writes its atoms to the file. else, writes the line
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
		
		outstream.close()
		instream.close()

	#EXPLAIN: checks if there are atoms and update the is-true private of the probablistic obj
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

