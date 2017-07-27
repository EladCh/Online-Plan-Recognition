#!/usr/bin/python
import sys, os, csv
from options import Program_Options
import benchmark, planners, translation, hypothesis

def custom_partition( s, sep ) :
	i = 0
	while i < len(s) :
		if s[i] == sep : break
		i = i + 1
	if i == len(s) : return (None,None,None)
	if i == 0 : return ( None, s[i], s[i+1:] )
	return ( s[:i-1], s[i], s[i+1:] )



def load_hypotheses() :

	hyps = []
	
	instream = open( 'hyps.dat' )
	
	for line in instream :
		line = line.strip()
		H = hypothesis.Probabilistic()
		H.atoms = [  tok.strip() for tok in line.split(',') ]
		H.check_if_actual()
		hyps.append( H )

	instream.close()

	return hyps
	
def write_report( experiment, hyps ) :
	
	outstream = open( 'report.txt', 'w' )
	
	print >> outstream, "Experiment=%s"%experiment
	print >> outstream, "Num_Hyp=%d"%len(hyps)
	for hyp in hyps :
		print >> outstream, "Hyp_Atoms=%s"%",".join( hyp.atoms )
		if hyp.test_failed :
			print >> outstream, "Hyp_Test_Failed=True"
		else :
			print >> outstream, "Hyp_Test_Failed=False"

		print >> outstream, "Hyp_Cost_O=%f"%hyp.cost_O
		print >> outstream, "Hyp_Cost_Not_O=%f"%hyp.cost_Not_O
		print >> outstream, "Hyp_Prob_O=%f"%hyp.Probability_O
		print >> outstream, "Hyp_Prob_Not_O=%f"%hyp.Probability_Not_O
		print >> outstream, "Hyp_Plan_Time_O=%f"%hyp.Plan_Time_O
		print >> outstream, "Hyp_Plan_Time_Not_O=%f"%hyp.Plan_Time_Not_O
		print >> outstream, "Hyp_Trans_Time=%f"%hyp.trans_time
		print >> outstream, "Hyp_Plan_Time=%f"%hyp.plan_time
		print >> outstream, "Hyp_Test_Time=%f"%hyp.total_time
		print >> outstream, "Hyp_Is_True=%s"%hyp.is_true

	outstream.close()

def main() :
	print sys.argv
	options = Program_Options( sys.argv[1:] )

	if options.greedy :
		planners.LAMA.greedy = True

	hyps = load_hypotheses()

	hyp_time_bounds = [ options.max_time / len(hyps) for h in hyps ]

	for i in range( 0, len(hyps) ) :
		hyps[i].test(i, hyp_time_bounds[i], options.max_memory, options.optimal)
		if hyps[i].cost_O == 1e7 and hyps[i].cost_Not_O == 1e7 :
			hyps[i].test_failed = True
		remainder = hyp_time_bounds[i] - hyps[i].total_time
		if remainder > 0 :
			extra = remainder / (len(hyps)-i)
			for j in range(i+1,len(hyps)) :
				hyp_time_bounds[j] += extra

	write_report(options.exp_file, hyps)
	# pack logs, csvs and report.txt
	cmd = 'tar jcvf results.tar.bz2 *.pddl *.log report.txt obs.dat hyps.dat prob-*-PR'
	os.system( cmd )	
	cmd = 'rm -rf *.log report.txt *.res *.csv *.res.* *.pddl *.dat prob-*-PR'
	os.system( cmd )

if __name__ == '__main__' :
	main()
