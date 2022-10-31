import re
from itertools import product
import numpy as np
from collections import defaultdict
from kgtk import call_semantic_similarity
import os
import requests
import json
from re import match
import pandas as pd

from collections import defaultdict
from itertools import product

from kgtk_score import get_similarity
from lexical_overlapping import get_score
from utils import gold_label, get_template_info


def load_json_files(system_json, reference_json):
    '''
    load the system and reference json file

    :param system_json:
    :param reference_json:
    :return:  system and reference json file
    '''
    with open(system_json) as f:
        system = json.load(f)
    with open(reference_json) as f:
        reference = json.load(f)
    # kairos_ce=openwb('/content/drive/MyDrive/AIDA KAIROS-file code/kairos_ep_alignment_output.tab_sijia_0520.xlsx')
    # template_info= defaultdict(list)
    # for row in list(kairos_ce)[1:]:
    #   template_info[row[3].value]=row[4].value
    return system, reference


def get_embedding_score(get_arg_match, get_ref_match, q1, q2, model):
    '''

    compute the embedding score using the sentence-transformers
    :param get_arg_match:
    :param get_ref_match:
    :param q1:
    :param q2:
    :param model:
    :return:
    '''
    score = 0
    argmatch = get_arg_match(q1)  # get the argument set (arg_Num, argument value) list
    argmatch2 = get_ref_match(q2)
    # print(argmatch,argmatch2)
    arg_visited = defaultdict(float)
    for c in argmatch:
        for g in argmatch2:

            if c[0] == g[0]:  # ensure these two are the same  argument
                if not re.match('arg\d', c[1]) and not re.match('arg\d', g[1]):

                    # get the embedding representation with the sentence transformer, embedding lenth =768
                    sys_arg = model.encode(c[1])
                    ref_arg = model.encode(g[1])
                    result = np.dot(sys_arg, ref_arg)  #using the dot prodct to get the similarity
                    # if result >= arg_visited[c[0]]:
                    #   arg_visited[c[0]]=result
                    # else:
                    #   result=arg_visited[c[0]]
                    if result >= 0.5:    # greater than 0.5, output the similarity score
                        score0 = result
                    else:   # otherwise, output 0, this is for purpose that can output 0 in the end for no-match system event
                        score0 = 0
                    # print(result)

                    score += score0

    # print(len([t for t in argmatch2 if not re.match('arg\d',t[1])]))
    # return score/len([t for t in argmatch2 if not re.match('arg\d',t[1])]),sorted(argmatch),sorted(argmatch2)
    return score


def compute_terminal_score(system, reference, system_arg_newmatch, ref_arg_newmatch, dwd2template):
    '''
    compute the terminal score , combine lexical overlapping, emebedding and the kgtk similarity


    :param system:
    :param reference:
    :param system_arg_newmatch:
    :param ref_arg_newmatch:
    :param dwd2template:
    :return:
    '''
    score_record = defaultdict(dict)
    for k in system.keys():  # iterate the system json file
        system_ep = system[k]  #current system event
        if k in EVAL_ep:  #if the current event is annotated by the human assessment
            arguments_dict = defaultdict(dict)
            for arg in system_ep['arguments']:  #iterate the arguments of the current system events
                arguments_dict[arg['dwd_argname']] = arg  # create a dict, {A0_PPT(arg_name)： Khayat(arg_value)}
            for v in reference.keys():# for each reference event
                score = 0
                score1 = get_score(k, v, system, dwd2template, reference)  #overlapping score
                # score0 = get_embedding_score(k, v)   # if use embedding score, cancel the comment
                reference_ep = reference[v]  #current reference event
                if reference_ep['arguments'] != []:    #if reference event has argument infomation
                    if system_ep['system_type'].split('.')[0].lower() == reference_ep['type']: #if this pair belongs to the same type for the first level
                        ref_argument_dict = defaultdict(dict)
                        for arg in reference_ep['arguments']:
                            ref_argument_dict[arg['dwd_argname']] = arg  #get the same dict for the reference event arguments
                        for args in arguments_dict.keys():
                            # print(ref_argument_dict[args])
                            # print(arguments_dict)
                            if ref_argument_dict[args] != {}:
                                # print(ref_argument_dict[args])
                                # print(arguments_dict[args])
                                # if ref_argument_dict[args]['dwd_key']==arguments_dict[args]['dwd_key']  and ref_argument_dict[args]['type']==arguments_dict[args]['entity_type'].lower():
                                score = get_similarity(k, v, sys_arg_newmatch, ref_arg_newmatch)  #get the kgtk similarity score
                                # print(ref_argument_dict[args],arguments_dict[args])
                                # if ref_argument_dict[args]['description']==arguments_dict[args]['description']:
                                #   score+=1
                        # print(k, v, score, score1, score0)
                        score_record[k][v] = score + score1    #terminal score, if add emebdding score, add score0
                        #{reference_id : the overall score of this reference event and system event}

    '''
    evaluation part
    '''
    hits = 0  #number of correct prediction
    count = 0   #number of matched event in the human assessment
    for k, v in score_record.items():  # iterate the dict
        max_score = [x for x, y in v.items() if y == max(v.values())]  # get the reference event that has the highest score of all the reference event
        print('system_event: ' + k, 'match to ' + system[k]['match'])    #print the gold label
        print(max_score, v)
        if system[k]['match'] != 'n/a':    #count the number of matched event
            count += 1
            if len(max_score) == 1:  # we must ensure that only one reference event get the highest score, and that event
                # exactly is the matched event  of the current system event, we would count as predict correctly
                if max_score[0].strip() == system[k]['match'].strip():  # if the
                    hits += 1
        # print(max_score[0],system[k]['match'],max_score[0]==system[k]['match'])
        if (system[k]['match']=='n/a' and max(v.values())==0):  # if highestscore= 0, means we think this system event
            # does not match to any reference event, so if system match is 'n/a', we predict correctly
            hits+=1

    print('total system events is {} and we predict correct is {}, the total matched system events is {} '.format(
        len(score_record), hits, count))


def extract_filler(system):  # s
    '''

    get a template info without any actual filler and just only include the default filler, like arg1, arg2, etc.
    then once we get a new event, even if we don't know the arg_num for each filler as that is absent in the arguments file,

    we can infer the arg_num based on the slot they filled in .

    :param system:
    :return:
    '''
    # input system json files
    # this is for those don't have corresponding arguments info in the arguments files, we extract the argument value from the existing template.
    dwd2template = defaultdict()
    for k, v in system.items():
        arg2num = dict()  # store the arguments corresponding arg_num
        if system[k]['arguments'] != []:  # if exists arguments in system

            for arg in system[k]['arguments']:  # iterate arguments
                if arg['description'] not in arg2num:  # avoid the duplicate
                    arg2num[arg['description']] = arg['arg_num']  # {sydney airport:A3_gol_destination_destination}
            # print(arg2num)
            # print(system[k]['template_info'])
            info = system[k]['template_info']  # get the complete template info here
            pattern = re.compile('<(.*?)>')
            valid = filter(lambda x: re.match('((?!arg\d).)', x),
                           pattern.findall(info))  # get all fillers in the template
            matched = pattern.findall(info)  # all slots   including arg1(means there is no filler to fill in the arg1 slot)
            c = info
            visited = []
            for g in range(len(matched)):
                if re.match('((?!arg\d).)', matched[g]):

                    if '&' in matched[g]:  # 'amer kyhat&Kyhat'

                        arg_list = matched[g].split('&')
                        for candidate in arg_list:
                            if candidate.strip() not in visited:
                                first_one = '' + candidate.strip()
                    else:
                        first_one = '' + matched[g].strip()

                    # print(matched[g],first_one)
                    c = re.sub(matched[g], arg2num[first_one], c, 1)   #substtute the original template with the arg,

                    visited.append(first_one)  # record the filler we have known
            # print(c,k)
            # else:
            #   print(pattern.findall(info)[g])
            result = pattern.findall(c)

            dwd2template[system[k]['dwd_key']] = c
    return dwd2template


def get_ref_qnode(reference_arguments_file):  #
    '''
    get the terminal qnode for each argument
    :param reference_arguments_file:
    :return:  qnode list
    '''
    ref_arg_newmatch = defaultdict(dict)  # initilize a new nested dict
    ref_arg_file = pd.read_excel(reference_arguments_file)  # load the arguments file
    for j, i in enumerate(ref_arg_file['eventprimitive_id']):
        if i != 'EMPTY_NA':  # rules: 1) if we get the mapped qnode based on the arguments value and filtered, we use that;
            # 2)otherwise, we the same as 1) but no filter
            # 3) otherwise, we use the original qnode based on the entity type
            # but there might be one slot has multiple arguments like  Khayat and Amer Khayat both consitutes ARG1, so it's a list
            if ref_arg_file.iloc[j, -1].strip() != '':
                # print(eval(ref_arg_file.iloc[j,-1]))
                map_value = list(eval(ref_arg_file.iloc[j, -1]))

            elif ref_arg_file.iloc[j, -2].strip() != '[]':
                # mapping_value=ref
                map_value = list(eval(ref_arg_file['value_mapping'][j]))
            else:
                map_value = [ref_arg_file['dwd_key'][j].strip('DWD_')]
            ref_arg_newmatch[i][ref_arg_file.iloc[j, -5]] = ref_arg_newmatch[i].get(ref_arg_file.iloc[j, -5],
                                                                                    []) + map_value
    return ref_arg_newmatch


# get the final qnode for the system
def get_sys_qnode(system_argumments_file):  # system_argument file

    '''
    similar to get_ref_qnode, just get the terminal qnode for the argument
    :param system_argumments_file:
    :return:
    '''
    sys_arg_newmatch = defaultdict(dict)
    sys_arg_file = pd.read_excel(system_argumments_file)
    for j, i in enumerate(sys_arg_file['system_ep_id']):
        if i != 'EMPTY_NA':
            if sys_arg_file.iloc[j, -1].strip() != '':

                map_value = list(eval(sys_arg_file.iloc[j, -1]))
            elif sys_arg_file.iloc[j, -2].strip() != "[]":
                # mapping_value=ref
                # print(sys_arg_file.iloc[j,-2].strip())
                map_value = list(eval(sys_arg_file['mapping_value'][j]))
            else:

                map_value = [sys_arg_file.iloc[j, -3].strip('DWD_')]
            # if sys_arg_file.iloc[j,-4] in  sys_arg_newmatch[i]:
            sys_arg_newmatch[i][sys_arg_file.iloc[j, -4]] = sys_arg_newmatch[i].get(sys_arg_file.iloc[j, -4],
                                                                                    []) + map_value
    return sys_arg_newmatch


if __name__ == '__main__':
    system_json = 'kairos_with_template_ep.json'  # json files for system event
    reference_json = 'gold_ep.json'  # json files for reference events
    system_source_file = 'kairos_ep_alignment_output.tab_sijia_0520.xlsx'  # source excel files for system events
    events_assessment_file = 'KAIROS_EVAL_ep_alignment.tab.xlsx'  # human assessment files for events matching
    system_arguments_file = 'kairos_ke_analysis_output_sijia_0520.tab.xlsx'  # excel for system argumentss
    reference_arguments_file = 'ce1005_arguments_sijia_0520.tab.xlsx'  # excel files for reference arguments
    system, reference = load_json_files(system_json, reference_json)  # load the json file
    template_info = get_template_info(system_source_file)  #load the template
    EVAL_ep, EVAL_reference_ep = gold_label(events_assessment_file)  # load the gold label
    dwd2template = extract_filler(system)  #get the template info for those argument info not in the argument files
    sys_arg_newmatch = get_sys_qnode(system_arguments_file)  # terminal qnode for system event argument after re-mapping
    ref_arg_newmatch = get_ref_qnode(reference_arguments_file)  #terminal qnode for reference event after  re-mapping
    compute_terminal_score(system, reference, sys_arg_newmatch, ref_arg_newmatch, dwd2template)  #compute the terminal score
