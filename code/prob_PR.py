#!/usr/bin/python
import copy
import sys, os, csv

import problems_info
from options import Program_Options
import benchmark, planners, translation, hypothesis

ideal_costs = []
ideal_actions = []
ideal_preconditions = []


def get_greedy_cost(path, planner_name):
	cost = -1
	if "LAMA" in planner_name:
		with open(path) as instream:
			for line in instream:
				if 'cost:' in line:
					cost = line.split('cost: ')[1]
					cost = cost.replace('.', "").replace('\n',"")
					break
		return int(cost)
	elif "H" in planner_name:
		with open(path) as instream:
			for line in instream:
				if 'MetricValue' in line:
					cost = line.split('MetricValue ')[1]
					cost = cost.replace('\n',"")
					break
		return int(cost)

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

def load_observations():
	instream = open('obs.dat')
	obs = [line.strip()for line in instream]
	instream.close()
	return obs

def write_report( experiment, hyps, obs, hyp_num, options, planner_name, obs_num, domain_data, observations_plans = []) :
	outstream = open( 'report.txt', 'w' )

	ex_name = str(experiment)
	ex_name = ex_name.split("/")
	name = ex_name[-1].split(".")[0]

	print >> outstream, "Experiment=%s" % name
	print >> outstream, "Num_Hyp=%d" % len(hyps)
	if obs != 0:
		print >> outstream, "Num_Obs=%d" % len(obs)

	hyps_data = []
	total_costs = 0
	i = 0
	for hyp in hyps:
		hyp_data = []
		# if obs_num != -1:  # online
		# 	current_domain = domain_data.data_saved[str(obs_num) + "," + str(i)]

		if obs_num == -1:  # offline
			current_domain = domain_data.data_saved["offline_" + str(i)]
			# ideal_costs.append(current_domain[0])
			sol_file_name = str(i) + "_neg-O_offline_pr-problem.soln"
			ideal_value = get_greedy_cost(os.getcwd() + "/results/solution_files/" + sol_file_name, planner_name)
			# if the planner failed, use the data we generated
			if ideal_value == -1:
				ideal_costs.append(current_domain[0])
			ideal_costs.append(int(ideal_value))

			ideal_actions.append(current_domain[1])

		hyp_data.append(ideal_costs[i])
		hyp_data.append(hyp.cost_O)
        #
		# hyp_temp_list = current_domain[1]  # actions from start to hyp
		# obs_temp_list = domain_data.obs_fulfilled_actions  # actions from start to obs
		# if obs_num != -1:  # in case of online
		# 	obs_temp_list = domain_data.data_saved[str(obs_num) + "_obs"][1]
		# 	# intersection of the hyp_path set and obs_path set reveals the common actions
		# 	common_actions = [x for x in hyp_temp_list if x in obs_temp_list]
		# 	extra_to_obs_cost = obs_temp_list.__len__() - common_actions.__len__()
		# else:
		# 	extra_to_obs_cost = 0
		i += 1

		# number of seen observations
		obs_plan = 0
		if obs_num != -1:
			obs_plan = observations_plans[obs_num].__len__()
		hyp_data.append(obs_plan)

		hyp.VK_rank = (float(hyp_data[0])/float(hyp_data[1]+obs_plan))
		total_costs += hyp.VK_rank

		hyps_data.append(hyp_data)




	i = 0
	for hyp in hyps :
		data = hyps_data[i]
		greedy_cost = data[0]
		hyp_cost = data[1]
		obs_plan = data[2]
		i+=1
		O_probability = hyp.VK_rank/total_costs
		not_O_probability = 1 - hyp.VK_rank/total_costs
		hyp.Probability_O = O_probability
		hyp.Probability_Not_O = not_O_probability

		# print "\nIdeal:	" + str(data[0])
		# # print "Hyp_cost:	" + str(hyp_cost)
		# print "Hyp_cost:	" + str(hyp.cost_O)
		# print "Obs:	" + str(extra_to_obs_cost) + "\n"

		print >> outstream, "Hyp_Atoms_(Goal)=%s" % ",".join( hyp.atoms )
		if hyp.test_failed :
			print >> outstream, "Hyp_Test_Failed=True"
		else:
			print >> outstream, "Hyp_Test_Failed=False"
		print >> outstream, "Hyp_Is_True=%s" % hyp.is_true
		print >> outstream, "Timeout=%d" % options.max_time
		print >> outstream, "Heap restriction=%d" % options.max_memory

		# number of seen observations
		if obs_num != -1:
			print >> outstream, "Obs_Cost=%f" % obs_plan
		else:
			print >> outstream, "Obs_Cost=%f" % 0.0
		# hyp cost without common action
		print >> outstream, "Hyp_Cost_O=%f"%(hyp_cost)
		# ideal cost
		print >> outstream, "Hyp_Ideal_Cost=%f"%greedy_cost

		print >> outstream, "Hyp_GR_rank=%f"%(hyp_cost-greedy_cost)
		if hyp_cost+obs_plan != 0 and obs_num!= -1:  # the ordinary online case
			print >> outstream, "Hyp_VK_rank=%f"%hyp.VK_rank
		else:  # in case of failure of both naive and neg-O preventing division in 0
			print >> outstream, "Hyp_VK_rank=%f" % (float(greedy_cost) / float(-1))
		print >> outstream, "Hyp_Cost_Not_O=%f"%hyp.cost_Not_O
		# print "*/**/*/*/*/*/*/*/*/*"
		# for a in hyps[i-1].plan:
		# 	print a
		# print "*********************************"
		# for a in current_domain[3]:
		# 	print a.name
		# print "*/**/*/*/*/*/*/*/*/*"
		print >> outstream, "Hyp_Prob_O=%f"%O_probability
		print >> outstream, "Hyp_Prob_Not_O=%f"%not_O_probability
		print >> outstream, "Hyp_Plan_Time_O=%f"%hyp.Plan_Time_O
		print >> outstream, "Hyp_Plan_Time_Not_O=%f"%hyp.Plan_Time_Not_O
		print >> outstream, "Hyp_Trans_Time=%f"%hyp.trans_time
		print >> outstream, "Hyp_Plan_Time=%f"%hyp.plan_time
		print >> outstream, "Hyp_Test_Time=%f"%hyp.total_time

	outstream.close()


# def main():
# 	print sys.argv
# 	options = Program_Options( sys.argv[1:] )
#
# 	command = "cp obs.dat obs.rsc"
# 	os.system(command)
#
# 	if options.greedy :
# 		planners.LAMA.greedy = True
# 	#make sure that results dir exists
# 	if not os.path.exists("results"):
# 		os.makedirs("results", mode=0777)
#
# 	planner_name=""
# 	# writing to file the planner we use, for later use
# 	path = os.getcwd()
# 	outstream = open(path + "/results/used_planner.txt", 'w')
# 	if options.greedy:
# 		outstream.write("Greedy_LAMA")
# 		planner_name="Greedy_LAMA"
# 	elif options.optimal:
# 		outstream.write("H2")
# 		planner_name ="H2"
# 	elif options.use_FF:
# 		outstream.write("Metric_FF")
# 		planner_name ="Metric_FF"
# 	elif options.use_hspr:
# 		outstream.write("Hsp_r")
# 		planner_name ="Hsp_r"
# 	else:
# 		outstream.write("LAMA")
# 		planner_name ="LAMA"
# 	outstream.close()
#
# 	hyps = load_hypotheses()
# 	hyp_time_bounds = [ options.max_time / len(hyps) for h in hyps ]
#
# 	hyps[0].make_pr_domain_file()
# 	domain_name = options.exp_file.split("_")[0]
# 	domain = problems_info.Domain_info(domain_name, hyps)
# 	for hyp in hyps:
# 		hyp.domain=domain
#
# 	remove_command = 'rm -rf *9999_problem.pddl*'
# 	os.system(remove_command)
#
# 	# run the code according to the selected mode
# 	# online mode, works by the definitions of Vered&Kaminka (to be published) (algorithm 2)
# 	if options.online:
# 		obs = load_observations()
# 		domain.generate_pddl_for_obs_plan(obs)
# 		remainder = hyp_time_bounds[0]
# 		# iterating the observations
# 		for j in range(0, len(obs)):
# 			# domain.get_obs_predicates(j)
# 			# domain.run_planner_on_obs(j)
# 			# domain.save_obs_data(j)
# 			global obs_ind
# 			# for each observation, iterate all hyps
# 			for i in range(0, len(hyps)):
# 				domain.run_hyp(hyps[i],j)
# 				s=domain.actions
# 				hyps[i].test_online(i, j, hyp_time_bounds[i], options.max_memory, s, options.optimal)
# 				if hyps[i].cost_O == 1e7 and hyps[i].cost_Not_O == 1e7:
# 					hyps[i].test_failed = True
# 				remainder = remainder - hyps[i].total_time
# 				if remainder > 0:
# 					extra = remainder / (len(hyps) - i)
# 					for k in range(i + 1, len(hyps)):
# 						hyp_time_bounds[k] += extra
# 				domain.save_data(j, i)
# 				domain.restart()
# 			domain.restart_obs()
#
# 			# write temporary report file for the observation
# 			write_report(options.exp_file, hyps, obs, i, options, planner_name, j, domain)
# 			# pack logs, csvs and report.txt
# 			cmd = "tar jcvf results_" + str(j) + ".tar.bz2 *.pddl *.log report.txt obs.dat hyps.dat prob-*-PR pr-problem.soln"
# 			os.system(cmd)
# 			# remove irrelevant files
# 			cmd = 'rm -rf prob-*-PR pr-problem.soln'
# 			os.system(cmd)
#
# 	# offline mode, the original code of Geffner&Rammirez 2010
# 	else:
# 		for i in range(0, len(hyps)):
# 			hyps[i].test_offline(i, hyp_time_bounds[i], options.max_memory, options.optimal)
# 			domain.run_hyp(hyps[i])
#
# 			if hyps[i].cost_O == 1e7 and hyps[i].cost_Not_O == 1e7:
# 				hyps[i].test_failed = True
# 			remainder = hyp_time_bounds[i] - hyps[i].total_time
# 			if remainder > 0:
# 				extra = remainder / (len(hyps) - i)
# 				for j in range(i + 1, len(hyps)):
# 					hyp_time_bounds[j] += extra
# 			domain.save_data(-1 , i)
# 			domain.restart()
#
# 		write_report(options.exp_file, hyps, 0, len(hyps), options, planner_name, -1, domain)
# 		# pack logs, csvs and report.txt
# 		cmd = 'tar jcvf results.tar.bz2 *.pddl *.log report.txt obs.dat hyps.dat prob-*-PR'
# 		os.system( cmd )
# 		# remove irrelevant files
# 		cmd = 'rm -rf *.log report.txt *.res *.csv *.res.* *.pddl *.dat prob-*-PR'
# 		os.system( cmd )


def recompute(plan_of_highest_ranked_goal, obs):
	pass


def prune(plan, obs, hyp):
	pass


def run(run_options):
	# print sys.argv
	options = Program_Options( run_options[1:] )

	command = "cp obs.dat obs.rsc"
	os.system(command)

	if options.greedy :
		planners.LAMA.greedy = True
	#make sure that results dir exists
	if not os.path.exists("results"):
		os.makedirs("results", mode=0777)

	planner_name=""
	# writing to file the planner we use, for later use
	path = os.getcwd()
	outstream = open(path + "/results/used_planner.txt", 'w')
	if options.greedy:
		outstream.write("Greedy_LAMA")
		planner_name="Greedy_LAMA"
	elif options.optimal:
		outstream.write("H2")
		planner_name ="H2"
	elif options.use_FF:
		outstream.write("Metric_FF")
		planner_name ="Metric_FF"
	elif options.use_hspr:
		outstream.write("Hsp_r")
		planner_name ="Hsp_r"
	else:
		outstream.write("LAMA")
		planner_name ="LAMA"
	outstream.close()

	hyps = load_hypotheses()
	hyp_time_bounds = [ options.max_time / len(hyps) for h in hyps ]

	hyps[0].make_pr_domain_file()
	domain_name = options.exp_file.split("_")[0]
	domain = problems_info.Domain_info(domain_name, hyps)

	for hyp in hyps:
		hyp.domain=domain

	remove_command = 'rm -rf *9999_problem.pddl*'
	os.system(remove_command)

	# run the code according to the selected mode
	# online mode, works by the definitions of Vered&Kaminka (to be published) (algorithm 2)
	if options.online:
		# run heuristic online algorithm
		if options.heuristic:
			# find only observations plans
			obs = load_observations()
			domain.generate_pddl_for_obs_plan(obs)
			observations_plans = domain.run_planner_on_obs(obs.__len__())

			remainder = hyp_time_bounds[0]
			hyps_list = copy.deepcopy(hyps)
			top_ranked_goal = None
			# iterating the observations
			last_obs_hyps = []
			for j in range(0, len(obs)):
				# check if there is a need to recompute
				if top_ranked_goal is None or recompute(top_ranked_goal.path, obs[j]):
					global obs_ind
					# for each observation, iterate all hyps
					last_obs_hyps = copy.deepcopy(hyps)
					for i in range(0, len(hyps_list)):
						# check if the goal can be pruned
						if prune(hyps_list[i].plan, obs[j], hyps_list[i]):
							hyps_list.remove(hyps_list[i])
						# run online algorithm on the hyp
						else:
							hyps_list[i].test_online(i, j, hyp_time_bounds[i], options.max_memory, options.optimal)
							if hyps_list[i].cost_O == 1e7 and hyps_list[i].cost_Not_O == 1e7:
								hyps_list[i].test_failed = True
							remainder = remainder - hyps_list[i].total_time
							if remainder > 0:
								extra = remainder / (len(hyps_list) - i)
								for k in range(i + 1, len(hyps_list)):
									hyp_time_bounds[k] += extra

					# write temporary report file for the observation
					write_report(options.exp_file, hyps_list, obs, i, options, planner_name, j, domain, observations_plans)
					# pack logs, csvs and report.txt
					cmd = "tar jcvf results_" + str(
						j) + ".tar.bz2 *.pddl *.log report.txt obs.dat hyps.dat prob-*-PR pr-problem.soln"
					os.system(cmd)
					# remove irrelevant files
					cmd = 'rm -rf prob-*-PR pr-problem.soln'
					os.system(cmd)

					# find the top ranked goal
					max_prob_hyp = None
					max_prob_value = 0
					for hyp in hyps:
						if hyp.Probability_O > max_prob_value:
							max_prob_hyp = copy.deepcopy(hyp)
					top_ranked_goal = max_prob_hyp

		# run online algorithm
		else:
			obs = load_observations()
			domain.generate_pddl_for_obs_plan(obs)
			observations_plans=domain.run_planner_on_obs(obs.__len__())
			remainder = hyp_time_bounds[0]
			# iterating the observations
			for j in range(0, len(obs)):
				# domain.get_obs_predicates(j)
				# domain.save_obs_data(j)


				global obs_ind
				# for each observation, iterate all hyps
				for i in range(0, len(hyps)):
					# domain.run_hyp(hyps[i],j)
					hyps[i].test_online(i, j, hyp_time_bounds[i], options.max_memory, options.optimal)
					if hyps[i].cost_O == 1e7 and hyps[i].cost_Not_O == 1e7:
						hyps[i].test_failed = True
					remainder = remainder - hyps[i].total_time
					if remainder > 0:
						extra = remainder / (len(hyps) - i)
						for k in range(i + 1, len(hyps)):
							hyp_time_bounds[k] += extra
					# domain.save_data(j, i)
					# domain.restart()
					# domain.reset_dictionaries()
				# domain.restart_obs()

				# write temporary report file for the observation
				write_report(options.exp_file, hyps, obs, i, options, planner_name, j, domain, observations_plans)
				# pack logs, csvs and report.txt
				cmd = "tar jcvf results_" + str(j) + ".tar.bz2 *.pddl *.log report.txt obs.dat hyps.dat prob-*-PR pr-problem.soln"
				os.system(cmd)
				# remove irrelevant files
				cmd = 'rm -rf prob-*-PR pr-problem.soln'
				os.system(cmd)

	# offline mode, the original code of Geffner&Rammirez 2010
	else:
		for i in range(0, len(hyps)):
			hyps[i].test_offline(i, hyp_time_bounds[i], options.max_memory, options.optimal)
			domain.run_hyp(hyps[i])

			if hyps[i].cost_O == 1e7 and hyps[i].cost_Not_O == 1e7:
				hyps[i].test_failed = True
			remainder = hyp_time_bounds[i] - hyps[i].total_time
			if remainder > 0:
				extra = remainder / (len(hyps) - i)
				for j in range(i + 1, len(hyps)):
					hyp_time_bounds[j] += extra
			domain.save_data(-1 , i)
			domain.restart()
			domain.reset_dictionaries()

		write_report(options.exp_file, hyps, 0, len(hyps), options, planner_name, -1, domain)
		# pack logs, csvs and report.txt
		cmd = 'tar jcvf results.tar.bz2 *.pddl *.log report.txt obs.dat hyps.dat prob-*-PR'
		os.system( cmd )
		# remove irrelevant files
		cmd = 'rm -rf *.log report.txt *.res *.csv *.res.* *.pddl *.dat prob-*-PR'
		os.system( cmd )


# if __name__ == '__main__' :
# 	main()
