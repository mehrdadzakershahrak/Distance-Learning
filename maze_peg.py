import numpy as np
import pprint
import re
import os
from itertools import chain, combinations
from feature_functions import laven_dist
from feature_functions import action_distance as plan_distance
import pickle
from os import path
import sys
import copy
from utils import *
from new_maxent_irl import maxent_irl

def store_traces(trace_files, scenario_wise=False):
    '''
    input: tuple containing full path of demonstration files(Explanations)
    This function parses the explanation files and stores in the global tuple traces in the order of scenarios
    '''
    global TRACE_ROOT_PATH
    if scenario_wise:
        traces = {}
    else:
        traces = []

    num_scenarios = len(trace_files)

    for i in range(num_scenarios):
        scenario_file = open(trace_files[i], 'r')
        lines = scenario_file.readlines()
        scenario_file.close()
        trace = []
        if scenario_wise:
            traces[i] = []
        for line in lines:
            if line[0] == '-':
                if scenario_wise:
                    traces[i].append(trace)
                else:
                    traces.append(trace)
                trace = []
            else:
                trace.append(line.rstrip())
    return traces

def render_problem_template(D):
    '''
    This function renders the domain (problem.tpl.pddl) file from substitutions corresponding to dictionary
    input: dictionary of substitutions
    '''
    global PROBLEM_ROOT_PATH, cost_dict,all_actions

    with open(PROBLEM_ROOT_PATH + 'problem.tpl.pddl', 'r') as f:
        og = f.readlines()


    #IPython.embed()
    for i in range(len(og)):
        if 'can_go' in og[i]:
            for e in all_actions.keys():
                if D[e] == 1:
                    if str(e) + ')' in og[i]:
                        og[i] = ';'+og[i]       #if an explanation is present, block the path from start to the goal.

    problem_template = open(PROBLEM_ROOT_PATH + 'p0.pddl', 'w')
    problem_template.write(''.join(og))
    problem_template.close()

def get_transition_matrix(all_actions, states_dict):
    '''

    :param all_actions: dict, all possible actions
    :param states_dict: states to number mapping
    :return:  transition probability matrix
    '''
    num_actions = len(all_actions)
    transition_matrix = np.zeros((2 ** num_actions, 2 ** num_actions, num_actions))
    for i in states_dict.keys():  # for each state,
        for a in list(set(all_actions.values()) - set(i)):  # for each explanation not yet done..
            try:
                new_state = list(i)
                new_state.append(a)
                transition_matrix[states_dict[i], states_dict[tuple(sorted(new_state))],a] = 1  # update transition matrix
            except (IndexError, KeyError) as e:
                print("incorrect new state!")
                print(new_state)
                print(a)
                # input()

    return transition_matrix

def powerset(iterable):
    #calculate powerset for a given iterable
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))

def get_state_map(actions):
    #calculate state map given the dictionary of all actions
    states = list(powerset(sorted(actions.values())))
    states_dict = {}
    reverse_states_dict = {}
    for i in range(len(states)):
        states_dict[states[i]] = i
        reverse_states_dict[i] = states[i]

    return states_dict, reverse_states_dict

def get_plan(state, all_actions, problem_file_used):
    '''
    input: state: tuple of all actions taken till reaching state, all_actions: dict of all actions assigned to a number
    output: plan obtained by running planner on input files
    '''
    global PLANNER_RELATIVE_PATH,plan_switch
    # generate dictionary corresponding to substitutions and render domain template to get plan
    subs_dict = {}
    for action_template in all_actions.keys():
        if all_actions[action_template] in state:
            #print(action_template)
            subs_dict[action_template] = 1
        else:
            subs_dict[action_template] = 0
    render_problem_template(subs_dict)

    #calculate plan and plan-cost using fast-downward planner
    cmd = '.' + PLANNER_RELATIVE_PATH + 'fast-downward.py --sas-file temp_' + str(0) + '.sas --plan-file plan_' + str(
        0) + ' ' + 'Archive/domain.pddl' + ' ' + 'Archive/' + 'p' + str(
        problem_file_used) + '.pddl' + ' --search "astar(lmcut())"'
    # print(cmd)
    plan = os.popen(cmd).read()
    proc_plan = plan.split('\n')
    cost = [i for i, s in enumerate(proc_plan) if 'Plan cost:' in s]
    if 'Solution found!' not in proc_plan:
        print("No Solution")
        return [], 0
    plan = proc_plan[proc_plan.index('Solution found!') + 2: cost[0] - 1]
    plan = plan_switch[plan[0]]
    plan_cost = float(proc_plan[cost[0]].split(' ')[-1])
    #   print(plan)
    return plan, plan_cost

def calculate_features(plan1, plan2, plan1_cost, plan2_cost, state1, state2):
    '''
    input: 2 plans and an explanation
    output: feature vectors corresponding to the inputs

    '''
    global all_actions,distances
    lav_dist = laven_dist(plan1, plan2)
    plan_dist = plan_distance(plan1, plan2)
    state1 = set(state1)
    state2 = set(state2)
    cost = 0
    just_explained = list(state2.difference(state1))
    distx = []
    disty = []
    for a in state1:
        distx.append(distances[a][0])
        disty.append(distances[a][1])
    if len(state1)==0:
        distx=[0]
        disty=[0]
    just_explained_dist = distances[tuple(just_explained)[0]]
    
    #domain-dependent features
    try:
        d1 = just_explained_dist[0]-min(distx)
        d2 = just_explained_dist[0]-max(distx)
        d3 = just_explained_dist[1]-min(disty)
        d4 = just_explained_dist[1]-max(disty)
    except ValueError:
        input()

    dist = distances[tuple(just_explained)[0]]
    laven = laven_dist(plan1,plan2)

    f = [laven, plan_dist, (abs(plan1_cost - plan2_cost))**2,d1,d2,d3,d4]
    #print('\n')
    #print(laven)
    #print(plan_dist)
    #print('------')
    print(f)
    return f

def get_feat_map_from_states(states_dict, feat_map, P_a, problem_file_used, all_actions):
    '''
    for updating feat_map from applicable actions
    This function calculates the features corresponding to the states containined in states_dict
    :param: states_dict: state dictionary
    :param: feat_map: initial feature map 
    :param: P_a: transition matrix
    :param: problem_file_used: the problem file used for calculating the plans for features
    :param: all_actions: dictionary for all actions

    :return: feat_map: Final calculate feature map 
    '''
    global state_pairs_found, num_features,inv_all_actions
    total_number = 1.0*len(applicable_states)**2
    count = 0.0
    c = 0

    for state in states_dict:
        for next_state in states_dict:
            c+=1
            s1 = set(sorted(state))
            s2 = set(sorted(next_state))
            if s1.issubset(s2) and (len(s2)-len(s1)==1): # for every possible state-pair
                if [s1, s2] not in state_pairs_found:
                    state_pairs_found.append([state, next_state])
                count+=1
                state_id = states_dict[state]
                next_state_id = states_dict[next_state]
                #IPython.embed()
                plan, plan_cost = get_plan(state, all_actions, problem_file_used) #plan for same-state pair
                feat_map[state_id, state_id] = np.zeros([1, num_features])
                if any(P_a[state_id,next_state_id,:]) == 1: #possible next state
                    new_plan, new_plan_cost = get_plan(next_state, all_actions, problem_file_used)
                    features = calculate_features(plan, new_plan, plan_cost, new_plan_cost, state, next_state)
                    feat_map[state_id, next_state_id] = features

            sys.stdout.write('\r' + "Progress:" + str(count) + "/" + str(total_number) + " ,applicable states:" + str(
                len(applicable_states)))
            sys.stdout.flush()

    return feat_map

def get_trajectories_from_traces(all_actions, trace_list, states_dict,scenarios):
    '''
    This function converts expert demos into state-next_state-trajectories of the shape: TXLx2 where T is the number of trajectories, L is the length of each trajectory
    and each item is a state-next_state (int) pair
    '''
    #global num_traces
    num_traces = len(trace_list[0]) * len(trace_list)
    trajectories = []
    count = 0
    for sc in range(len(trace_list)):  # for each scenario
        for i in range(len(trace_list[sc])):  # for each trace of each scenario
            trajectory = []
            state = []
            for j in range(len(trace_list[sc][i])):  # for each explanation of each trace
                action = all_actions[str.upper(trace_list[sc][i][j])]
                next_state  = state+[action]
                trajectory.append([states_dict[tuple(sorted(state))],states_dict[tuple(sorted(next_state))]])
                state = next_state

            trajectories.append(trajectory)
            count+=1

    return np.array(trajectories)

if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.realpath('__file__'))
    TRACE_ROOT_PATH = dir_path+'/'+'Train/'
    PROBLEM_ROOT_PATH = dir_path+'/'+'Archive/'
    PLANNER_RELATIVE_PATH = '/FD/'
    pp = pprint.PrettyPrinter(indent=4)
    problem_file_used = 0
    num_features = 7

    all_actions = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5}
    inv_all_actions = {0:'A',1:'B',2:'C',3:'D',4:'E',5:'F'} 
    distances = {0:[-1,0],1:[8,2],2:[5,1],3:[3,4],4:[1,1],5:[7,1]} #(x,y) coordinates of the danger zones
    scenarios = [[3],[1],[1,3],[3,5],[1,2]] 
    files_used = [1,2,3,4,5] #Files used for training

    #read the original problem file 
    with open(PROBLEM_ROOT_PATH + 'problem.tpl.pddl', 'r') as f:
        og_template = f.readlines()

    plan_switch = {}
    plan_switch['goes start a (1)'] = ['left','up','up','right','right','right','up']
    plan_switch['goes start e (2)'] = ['right','up','up','right','up']
    plan_switch['goes start c (6)'] = ['right','right','right','right','right','up','up','left','left','left','up']
    plan_switch['goes start f (8)'] = ['right','right','right','right','right','right','right','up','up','left','left','left','left','left','up']
    plan_switch['goes start b (12)'] =['right','right','right','right','right','right','right','right','right','up','up','left','left','left','left','left','left','left','up']
    plan_switch['goes start d (19)'] =['right','right','right','right','right','right','right','right','right','up','up','up','up','left','left','left','left','left','left','left','down']
    plan_switch['goes start h (21)'] =['right','right','right','right','right','right','right','right','right','up','up','up','up','up','up','left','left','left','left','left','left','left','down','down','down']
    # new_plan_switch = {}
    
    # for plan_prefix,plan in plan_switch.items():
    #     prev = [1,0]
    #     new_plan_switch[plan_prefix] = []
    #     for step in plan:
    #         now = copy.deepcopy(prev)
    #         if step == 'right':
    #             now[0]+=1
    #         elif step == 'left':
    #             now[0]-=1
    #         elif step == 'down':
    #             now[1]-=1
    #         elif step == 'up':
    #             now[1]+=1
    #         new_plan_switch[plan_prefix].append(str(prev)+str(now))
    #         prev = copy.deepcopy(now)
    #pp.pprint(new_plan_switch)
    # exit()
    
    states_dict, reverse_states_dict = get_state_map(all_actions)  # Generate state maps for all states
    N = len(states_dict)
    print("total number of states: " + str(N))
    feat_map = np.zeros([N, N, num_features])

    with open('states_dict.pickle', 'wb') as handle:    
        pickle.dump(states_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open('all_actions.pickle', 'wb') as handle:
        pickle.dump(all_actions, handle, protocol=pickle.HIGHEST_PROTOCOL)


    P_a = get_transition_matrix(all_actions, states_dict) #Generate transition matrix 

    state_pairs_found = []

    trace_files = [TRACE_ROOT_PATH + 'p' + str(i) + '.txt' for i in files_used]
    traces = store_traces(trace_files, scenario_wise=True)      #store traces in dictionary
    print("All Actions:")
    pp.pprint(all_actions)

    applicable_states = list(states_dict.keys())
    trajectories = get_trajectories_from_traces(all_actions, traces, states_dict,scenarios)

    print(trajectories) 

    print("Calculating feature map")

    #Calculate the feature map for all state pairs and store in a map
    feat_map = get_feat_map_from_states(states_dict, feat_map, P_a, problem_file_used, all_actions)

    #Normalize across each feature
    for i in range(np.shape(feat_map)[-1]):
        feat_map[:, :, i]= normalize(feat_map[:, :, i])

    np.save("feat_map_final.npy", feat_map)
    np.save("trajectories.npy", trajectories)
    np.save("P_a.npy", P_a)
    print("\n Done " + str(problem_file_used))
    print("---------------------------------")

    #check if any state-pair is left out
    count = 0
    for state in states_dict.keys():
        for next_state in states_dict.keys():
            s1 = set(sorted(state))
            s2 = set(sorted(next_state))
            if [state, next_state] not in state_pairs_found:
                if s1.issubset(s2) and (len(s2) - len(s1) == 1):  # possible state-pair
                    print(str([state, next_state]))
            if s1.issubset(s2) and (len(s2) - len(s1) == 1):
                count+=1
                if not any(P_a[states_dict[state],states_dict[next_state],:]):
                    print("False")
            else:
                if any(P_a[states_dict[state],states_dict[next_state],:]):
                    print("False")

    print(count)
 