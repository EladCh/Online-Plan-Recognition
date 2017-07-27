#!/usr/bin/python
import sys, os, csv
from options import Program_Options
import benchmark, planners, translation, hypothesis, simulation

def load_hypotheses() :

	hyps = []
	
	instream = open( 'hyps.dat' )
	
	for line in instream :
		line = line.strip()
		H = hypothesis.Probabilistic()
		H.atoms = [  tok.strip() for tok in line.split(',') ]
		hyps.append( H )

	instream.close()

	return hyps

def load_obs() :
	obs = []
	instream = open( 'obs.dat' )
	for line in instream :
		line = line.strip()
		obs.append( line )
	instream.close()
	return obs

def generate_obs_and_test( hyps, options ) :
	agents = []
	for i in range(0, len(hyps)) :
		pddl_problem_file = 'hyp_%d_problem.pddl'%i
		simulation.generate_pddl_for_hyp_plan( pddl_problem_file, hyps[i].atoms )
		agent = simulation.Agent( pddl_problem_file, i )
		could_compute = agent.compute_plan()
		if not could_compute :
			outstream = open( 'error.txt', 'w' )
			print >> outstream, "Could not compute optimal plan within given time bounds!"
			outstream.close()
			sys.exit(0)
		agents.append( agent )
 
	observer = simulation.Observer( hyps )
	header = [ 'Time step' ]
	header += [ 'Hypothesis #%d'%k for k in range(0,len(hyps)) ]
	for i in range(0, len(agents) ) :
		likelihoods = []
		probs = []
		costs = []
		deltas = []
		for j in range(1, len(agents[i].plan)+1 ) :
			obs = agents[i].get_obs_at_time_step( j )
			observer.obs = obs
			observer.test( options )
			os.system( 'rm -rf prob-*-PR' )
			#P(O|G)
			posterior_probs = [ h.Probability_O for h in hyps ]
			likelihoods.append( posterior_probs )
			sum = 0.0
			for p in posterior_probs : sum += p
			# P(G|O)
			try :
				probs.append( [ h.Probability_O/sum for h in hyps ] )
			except ZeroDivisionError :
				print >> sys.stdout, "All P(O|G) = 0!!!"
				print >> sys.stdout, "P(O|G) = ", posterior_probs
				print >> sys.stdout, "Costs: ", ','.join(['/'.join([ str(h.costs['O']), str(h.costs['neg-O'])]) for h in hyps])
				sys.exit(1)
			costs.append( [ '/'.join([ str(h.G_cost), str(h.costs['O']), str(h.costs['neg-O'])]) for h in hyps ] )

		low_level_stream =  open( 'hyp-%d-probs_over_time.csv'%i, 'w' )
		outstream = csv.writer( low_level_stream )
		outstream.writerow( header )
		print >> sys.stdout, header
		for j in range(0, len(probs)) :
			outstream.writerow( [str(j+1)] + probs[j] )
			print >> sys.stdout, ','.join( [str(elem) for elem in [str(j)] + probs[j] ] )
		low_level_stream.close()
		low_level_stream = open( 'hyp-%d-costs_over_time.csv'%i, 'w' )
		outstream = csv.writer( low_level_stream )
		outstream.writerow( header )
		print >> sys.stdout, header
		for j in range(0, len(costs)) :
			outstream.writerow( [str(j+1)] + costs[j] )
			print >> sys.stdout, ','.join( [str(elem) for elem in [str(j)] + costs[j] ] )		
		low_level_stream.close()
	
	for i in range(0, len(agents)) :
		agents[i].save_plan()

	# pack logs, csvs and report.txt
	cmd = 'tar jcvf results.tar.bz2 %s agent-*-plan.txt hyp-*-costs_over_time.csv hyp-*-deltas_over_time.csv hyp-*-probs_over_time.csv'%options.exp_file
	os.system( cmd )	
	cmd = 'rm -rf *.log report.txt agent-*-plan.txt hyp-*-probs_over_time.csv *.res *.soln *.csv *.res.* *.pddl *.dat prob-*-PR'
	os.system( cmd )

def load_obs_and_test( hyps, options ) :

	observer = simulation.Observer( hyps )
	header = [ 'Time step' ]
	header += [ 'Hypothesis #%d'%k for k in range(0,len(hyps)) ]
	header += [ 'Time' ]
	obs = load_obs()
	probs = []
	costs = []
	deltas = []
	likelihoods = []
	for j in range(0, len(obs) ) :
		observer.obs = obs[0:j+1]
		observer.test( options )
		os.system( 'rm -rf prob-*-PR' )
		#P(O|G)
		posterior_probs = [ h.Probability_O for h in hyps ]
		likelihoods.append( [ '%s/%s'%(h.Probability_O,h.Probability_Not_O) for h in hyps ] )
		sum = 0.0
		for p in posterior_probs : sum += p
		# P(G|O)
		total_time = 0
		for h in hyps :
			total_time += h.total_time
		try :
			probs.append( [ h.Probability_O/sum for h in hyps ] + [str(total_time)] )
		except ZeroDivisionError :
			print >> sys.stdout, "All P(O|G) = 0!!!"
			print >> sys.stdout, "P(O|G) = ", posterior_probs
			print >> sys.stdout, "Costs: ", ','.join(['/'.join([ str(h.costs['O']), str(h.costs['neg-O'])]) for h in hyps])
			probs.append( [ 0.0 for h in hyps ] + [str(total_time)] )
		print probs
		costs.append( [ '/'.join([ str(h.costs['O']), str(h.costs['neg-O'])]) for h in hyps ] )

	low_level_stream =  open( 'hyp-likelihoods_over_time.csv', 'w' )
	outstream = csv.writer( low_level_stream )
	outstream.writerow( header )
	print >> sys.stdout, header
	for j in range(0, len(likelihoods)) :
		outstream.writerow( [str(j+1)] + likelihoods[j] )
		print >> sys.stdout, ','.join( [str(elem) for elem in [str(j)] + likelihoods[j] ] )
	low_level_stream.close()
	low_level_stream =  open( 'hyp-probs_over_time.csv', 'w' )
	outstream = csv.writer( low_level_stream )
	outstream.writerow( header )
	print >> sys.stdout, header
	for j in range(0, len(probs)) :
		outstream.writerow( [str(j+1)] + probs[j] )
		print >> sys.stdout, ','.join( [str(elem) for elem in [str(j)] + probs[j] ] )
	low_level_stream.close()
	low_level_stream = open( 'hyp-costs_over_time.csv', 'w' )
	outstream = csv.writer( low_level_stream )
	outstream.writerow( header )
	print >> sys.stdout, header
	for j in range(0, len(costs)) :
		outstream.writerow( [str(j+1)] + costs[j] )
		print >> sys.stdout, ','.join( [str(elem) for elem in [str(j)] + costs[j] ] )		
	low_level_stream.close()
	low_level_stream = open( 'hyp-deltas_over_time.csv', 'w' )
	outstream = csv.writer( low_level_stream )
	outstream.writerow( header )
	print >> sys.stdout, header
	for j in range(0, len(deltas)) :
		outstream.writerow( [str(j+1)] + deltas[j] )
		print >> sys.stdout, ','.join( [str(elem) for elem in [str(j)] + deltas[j] ] )		
	low_level_stream.close()

	# pack logs, csvs and report.txt
	cmd = 'tar jcvf results-beta-%f.tar.bz2 %s hyp-costs_over_time.csv hyp-deltas_over_time.csv hyp-probs_over_time.csv hyp-likelihoods_over_time.csv'%(options.beta, options.exp_file)
	os.system( cmd )	
	cmd = 'rm -rf *.log report.txt hyp-*_over_time.csv *.res *.soln *.csv *.res.* *.pddl *.dat prob-*-PR'
	os.system( cmd )

	
	

def main() :
	print sys.argv
	options = Program_Options( sys.argv[1:] )

	if options.greedy :
		planners.LAMA.greedy = True

	hyps = load_hypotheses()
	if options.simulate_from_obs :
		load_obs_and_test( hyps, options )
	else :
		generate_obs_and_test( hyps, options ) 
	

if __name__ == '__main__' :
	main()
