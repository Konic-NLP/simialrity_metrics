import re
from itertools import product
from sentence_transformers import SentenceTransformer
import numpy as np
from collections import defaultdict
from kgtk import call_semantic_similarity

def load_json_file(json):
    pass


def get_arg_match(system_event):
    arg_match = set()
    # for k in system.keys():
    sys_event = system[system_event]
    # if sys_event['arguments']==[]:
    template_info = sys_event['template_info']
    pattern = re.compile('<(.*?)>')
    # valid=filter(lambda x: re.match('((?!arg\d).)',x),pattern.findall(info))
    matched = pattern.findall(template_info)
    if sys_event['dwd_key'] in dwd2template.keys():
        tem_matched = pattern.findall(dwd2template[sys_event['dwd_key']])
        # print(tem_matched,matched)
        assert len(matched) == len(tem_matched)
        for c in zip(tem_matched, matched):
            # print(c)
            if '&' in c[1]:
                for g in c[1].split('&'):
                    arg_match.add((c[0].upper(), g.strip()))
            else:
                arg_match.add((c[0].upper(), c[1].strip()))
    print('sys', sorted(arg_match))
    return [c for c in arg_match if not c[1].startswith('arg')]


def get_ref_match(reference_):
    arg_match = set()

    reference_event = reference[reference_]
    for k in reference_event['arguments']:
        arg_match.add((k['arg_num'].upper(), k['description']))
    print('ref', sorted(arg_match))
    return arg_match


def get_score(q1, q2):
    score = 0
    arg_visited = defaultdict(float)
    argmatch = get_arg_match(q1)
    argmatch2 = get_ref_match(q2)
    # print(argmatch,argmatch2)
    for c in argmatch:
        for g in argmatch2:

            if c[0] == g[0]:  # ensure these two are the same  argument
                _pattern = re.compile(r"'s")
                c_args = [re.sub(_pattern, '', arg.lower()) for arg in c[1].split() if not re.match('arg\d', c[1])]
                g_args = [re.sub(_pattern, '', arg.lower()) for arg in g[1].split() if not re.match('arg\d', g[1])]
                print(c_args, g_args)
                num_overlap = len(set(c_args) & set(g_args)) * 2
                num_total = len(set(c_args)) + len(set(g_args))
                # print(num_overlap,num_total)
                if num_total == 0:
                    return 0
                else:
                    score += num_overlap / num_total
                # if score >= arg_visited[c[0]]:
                # arg_visited[c[0]]=score

    # if len(arg_visited)==0:
    # return 0
    # else:
    # return sum([t for s,t in arg_visited.items()])
    # return score/len([t for t in argmatch2 if not re.match('arg\d',t[1])]),sorted(argmatc
    # h),sorted(argmatch2)
    return score


def get_embedding_score(q1, q2, model):
    score = 0
    argmatch = get_arg_match(q1)
    argmatch2 = get_ref_match(q2)
    # print(argmatch,argmatch2)
    arg_visited = defaultdict(float)
    for c in argmatch:
        for g in argmatch2:

            if c[0] == g[0]:  # ensure these two are the same  argument
                if not re.match('arg\d', c[1]) and not re.match('arg\d', g[1]):
                    # print(c[1],g[1])
                    sys_arg = model.encode(c[1])
                    ref_arg = model.encode(g[1])
                    result = np.dot(sys_arg, ref_arg)
                    # if result >= arg_visited[c[0]]:
                    #   arg_visited[c[0]]=result
                    # else:
                    #   result=arg_visited[c[0]]
                    if result >= 0.5:
                        score0 = result
                    else:
                        score0 = 0
                    # print(result)

                    score += score0

    # print(len([t for t in argmatch2 if not re.match('arg\d',t[1])]))
    # return score/len([t for t in argmatch2 if not re.match('arg\d',t[1])]),sorted(argmatch),sorted(argmatch2)
    return score


def compute_terminal_score():
    score_record = defaultdict(dict)
    for k in system.keys():
        system_ep = system[k]
        if k in EVAL_ep:
            arguments_dict = defaultdict(dict)
            for arg in system_ep['arguments']:
                arguments_dict[arg['dwd_argname']] = arg
            for v in reference.keys():
                score = 0
                score1 = get_score(k, v)
                score0 = get_embedding_score(k, v)
                reference_ep = reference[v]
                if reference_ep['arguments'] != []:
                    if system_ep['system_type'].split('.')[0].lower() == reference_ep['type']:
                        ref_argument_dict = defaultdict(dict)
                        for arg in reference_ep['arguments']:
                            ref_argument_dict[arg['dwd_argname']] = arg
                        for args in arguments_dict.keys():
                            # print(ref_argument_dict[args])
                            # print(arguments_dict)
                            if ref_argument_dict[args] != {}:
                                # print(ref_argument_dict[args])
                                # print(arguments_dict[args])
                                # if ref_argument_dict[args]['dwd_key']==arguments_dict[args]['dwd_key']  and ref_argument_dict[args]['type']==arguments_dict[args]['entity_type'].lower():
                                score = get_similarity(k, v)
                                # print(ref_argument_dict[args],arguments_dict[args])
                                # if ref_argument_dict[args]['description']==arguments_dict[args]['description']:
                                #   score+=1
                        print(k, v, score, score1, score0)
                        score_record[k][v] = score + score0 + score1





def get_similarity(q1, q2):
    num_ = 0
    total_score = 0
    if q1 in sys_arg_newmatch and q2 in ref_arg_newmatch:
        sys_args = sys_arg_newmatch[q1].keys()
        ref_args = ref_arg_newmatch[q2].keys()
        # get all arguments
        num_ = (len(set([i for i in sys_args if sys_arg_newmatch[i] != []]) & set(
            [j for j in ref_args if ref_arg_newmatch[q2][j] != []])))
        for sys_arg in sys_args:
            if sys_arg in ref_args:
                best_score = 0
                # qnode list
                sys_arg_qnodes = sys_arg_newmatch[q1][sys_arg]
                ref_arg_qnodes = ref_arg_newmatch[q2][sys_arg]
                if sys_arg_qnodes == []:
                    continue
                # print(sys_arg_qnodes,ref_arg_qnodes)

                pairs = list(product(*(sys_arg_qnodes, ref_arg_qnodes)))
                # print(pairs)
                s1 = [a[0] for a in pairs]
                s2 = [a[1] for a in pairs]
                df = {'q1': s1, 'q2': s2}
                df = pd.DataFrame(df)

                df.to_csv('temp.tsv', sep='\t')
                result = call_semantic_similarity('temp.tsv')
                # print(result)
                # result[result=='']=0
                result.to_csv('test_file_similarity.tsv', index=False, sep='\t')

                score = result.apply(get_total_score, axis=1)
                # print(score)
                # print(type(score),max(score))
                print('-------end------')
                total_score += max(score)
        # print(q2, total_score)
    if num_ == 0:
        return 0
    return total_score / num_
    # alist.append(score)
    #  print(max(alist))
    # if best_score<score:
    #   best_score=score


def evaluate():
    hits = 0
    count = 0
    for k, v in score_record.items():
        max_score = [x for x, y in v.items() if y == max(v.values())]
        print('system_event: ' + k, 'match to ' + system[k]['match'])
        print(max_score, v)
        if system[k]['match'] != 'n/a':
            count += 1
        # print(max_score[0],system[k]['match'],max_score[0]==system[k]['match'])
        # if (system[k]['match']=='n/a' and max(v.values())==0):
        #   hits+=1
        # if len(max_score)==1:
        if max_score[0].strip() == system[k]['match'].strip():
            hits += 1
    print(hits,len(score_record),count)
