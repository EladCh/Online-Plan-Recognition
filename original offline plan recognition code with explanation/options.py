import getopt, os, sys

def usage() :
	print >> sys.stderr, "Parameters:"
	print >> sys.stderr, "-e  --experiment <file>          Plan Recognition experiment files (tar'ed)"
	print >> sys.stderr, "-h  --help                       Get Help"
	print >> sys.stderr, "-t  --max-time <time>            Maximum allowed execution time (defaults to 1800 secs)"
	print >> sys.stderr, "-m  --max-memory <time>          Maximum allowed memory consumption (defaults to 1Gb)"
	print >> sys.stderr, "-O  --optimal                    Optimal Probabilistic PR"
	print >> sys.stderr, "-G  --greedy                     Greedy LAMA (takes first solution as best)"
	print >> sys.stderr, "-P  --hspr                       Use hspr for satisficing planning"
	print >> sys.stderr, "-F  --ff                         Use FF for satisficing planning"
	print >> sys.stderr, "-S  --simulation                 Simulation mode"
	print >> sys.stderr, "-b  --beta <value>               Parameter strictly positive which penalizes non--optimal behavior"
	print >> sys.stderr, "-D  --simulate-from-obs          Uses provided observations instead of generating them (Simulation mode)"

class Program_Options :

	def __init__( self, args ) :
		try:
			opts, args = getopt.getopt(	args,
							"e:ht:m:OGSb:PFD",
							["experiment=",
							"help",
							"max-time=",
							"max-memory=",
							"beta=",
							"hspr",
							"ff",
							"optimal",
							"greedy",
							"simulation",
							"simulate-from-obs"] )
		except getopt.GetoptError :
			print >> sys.stderr, "Missing or incorrect parameters specified!"
			usage()
			sys.exit(1)

		self.exp_file = None
		self.domain_name = None
		self.instance_names = []
		self.max_time = 1800
		self.max_memory = 1024
		self.optimal = False
		self.greedy = False
		self.simulation = False
		self.use_hspr = False
		self.use_FF = False
		self.beta = 1.0
		self.simulate_from_obs = False

		for opcode, oparg in opts :
			if opcode in ( '-h', '--help' ) :
				print >> sys.stderr, "Help invoked!"
				usage()
				sys.exit(0)
			if opcode in ('-e', '--experiment' ) :
				self.exp_file = oparg
				if not os.path.exists( self.exp_file ) :
					print >> sys.stderr, "File", self.exp_file, "does not exist"
					print >> sys.stderr, "Aborting"
					sys.exit(1)
			if opcode in ('-t', '--max-time' ) :
				try :
					self.max_time = int(oparg)
					if self.max_time <= 0 :
						print >> sys.stderr, "Maximum time must be greater than zero"
						sys.exit(1)
				except ValueError :
					print >> sys.stderr, "Time must be an integer"
					sys.exit(1)
			if opcode in ('-b', '--beta' ) :
				try :
					self.beta = float(oparg)
					if self.beta <= 0.0 :
						print >> sys.stderr, "Beta must be a positive real number"
						sys.exit(1)
				except ValueError :
					print >> sys.stderr, "Beta must be a (positive) real number, rather than", oparg
					sys.exit(1)
			if opcode in ('-m', '--max-memory' ) :
				try :
					self.max_memory = int(oparg)
					if self.max_memory <= 0 :
						print >> sys.stderr, "Maximum memory must be greater than zero"
						sys.exit(1)
				except ValueError :
					print >> sys.stderr, "Memory amount must be an integer"
					sys.exit(1)
			if opcode in ('-O', '--optimal' ) :
				self.optimal = True
			if opcode in ('-G', '--greedy' ) :
				self.greedy = True
			if opcode in ('-S', '--simulation' ) :	
				self.simulation = True
			if opcode in ('-P', '--hspr' ) :
				self.use_hspr = True
			if opcode in ('-F', '--ff' ) :
				self.use_FF = True
			if opcode in ('-D', '--simulate-from-obs' ) :
				self.simulate_from_obs = True

		if self.exp_file is None :
			print >> sys.stderr, "No experiment file was specified!!"
			usage()
			sys.exit(1)	
	
		os.system( 'tar jxvf %s'%self.exp_file )
		if not os.path.exists( 'domain.pddl' ) :
			print >> sys.stderr, "No 'domain.pddl' file found in experiment file!"
			usage()
			sys.exit(1)
		if not os.path.exists( 'template.pddl' ) :
			print >> sys.stderr, "No 'template.pddl' file found in experiment file!"
			usage()
			sys.exit(1)
		if not os.path.exists( 'hyps.dat' ) :
			print >> sys.stderr, "No 'hyps.dat' file found in experiment file!"
			usage()
			sys.exit(1)
		if not self.simulation :
			if not os.path.exists( 'obs.dat' ) :
				print >> sys.stderr, "No 'obs.dat' file found in experiment file!"
				usage()
				sys.exit(1)
			if not os.path.exists( 'real_hyp.dat' ) :
				print >> sys.stderr, "No 'real_hyp.dat' file found in experiment file!"
				usage()
				sys.exit(1)

	def print_options( self ) :
		def print_yes() : print >> sys.stdout, "Yes"
		def print_no() : print >> sys.stdout, "No"
		
		print >> sys.stdout, "Options set"
		print >> sys.stdout, "==========="
		print >> sys.stdout, "Experiment File:", self.exp_file
		print >> sys.stdout, "Max. Time Allowed", self.max_time
		print >> sys.stdout, "Max. Memory Allowed", self.max_memory
