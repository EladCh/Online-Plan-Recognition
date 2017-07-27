import benchmark

class Probabilistic_PR :
	
	def __init__( self, domain, problem, obs, max_time = 1800, max_mem = 2048 ) :
		self.domain = domain
		self.problem = problem
		self.obs_stream = obs
		self.max_time = max_time
		self.max_mem = max_mem
		self.convert_to_integers = False
		self.factor = 1.0

	def execute( self ) :
		if not self.convert_to_integers :
			cmd_string = './pr2plan -d %s -i %s -o %s -P'%(self.domain, self.problem, self.obs_stream)
		else :
			cmd_string = './pr2plan -d %s -i %s -o %s -P -Z %s'%(self.domain, self.problem, self.obs_stream, self.factor)

		self.log = benchmark.Log( '%s_%s_%s_transcription.log'%(self.domain, self.problem, self.obs_stream) )
		self.signal, self.time = benchmark.run( cmd_string, self.max_time, self.max_mem, self.log )

