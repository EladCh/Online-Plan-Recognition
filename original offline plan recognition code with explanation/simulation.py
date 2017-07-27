import os, benchmark
import planners, translation, hypothesis

def generate_pddl_for_hyp_plan( out_name, atoms ) :
	instream = open( 'template.pddl' )
	outstream = open( out_name, 'w' )

	for line in instream :
		line = line.strip()
		if '<HYPOTHESIS>' not in line :
			print >> outstream, line
		else :
			for atom in atoms :
				print >> outstream, atom
	
	outstream.close()
	instream.close()

class Agent :

	def __init__( self, problem, index ) :
		self.domain = 'domain.pddl'
		self.problem = problem
		self.index = index
		self.plan = []

	def compute_plan( self ) :
		planner = planners.H2( self.domain, self.problem, self.index )
		planner.execute()
		if planner.signal != 0 :
			return False
		self.plan = planner.get_plan()
		return True

	def get_obs_at_time_step( self, i ) :
		assert i <= len(self.plan)
		return self.plan[0:i]

	def save_plan( self ) :
		outstream = open( 'agent-%d-plan.txt'%self.index, 'w' )
		for op in self.plan :
			print >> outstream, op
		outstream.close()

class Observer :

	def __init__( self, hyps ) :
		self.hyps = hyps
		self.obs = None

	def test( self, options ) :

		# write obs.dat
		outstream = open( 'obs.dat', 'w' )
		for o in self.obs :
			print >> outstream, o.upper()
		outstream.close()

		for i in range(0, len(self.hyps) ) :
			self.hyps[i].test_for_sim( i, options )
