import re
from collections import defaultdict

def get_arg_match(system_event,system, dwd2template):
    '''
    get all arguments based on the template info
    :param system_event: event id for system event
    :param system:  parsed system json file
    :param dwd2template:
    :return:  all valid arguments value, except for 'arg1',etc ,  a list with element is set,e.g ('arg0','Khayat')
    '''
    arg_match = set()
    # for k in system.keys():
    sys_event = system[system_event]
    # if sys_event['arguments']==[]:
    template_info = sys_event['template_info']  # get the template info_mation
    pattern = re.compile('<(.*?)>')
    # valid=filter(lambda x: re.match('((?!arg\d).)',x),pattern.findall(info))
    matched = pattern.findall(template_info)   # get all fillers in the template slots
    if sys_event['dwd_key'] in dwd2template.keys():
        tem_matched = pattern.findall(dwd2template[sys_event['dwd_key']])
        # print(tem_matched,matched)
        assert len(matched) == len(tem_matched)
        for c in zip(tem_matched, matched):
            # print(c)
            if '&' in c[1]:  #if multiple participants acts  as the same argument, e.g. two person name both are arg0
                for g in c[1].split('&'):
                    arg_match.add((c[0].upper(), g.strip()))
            else:
                arg_match.add((c[0].upper(), c[1].strip()))
    print('sys', sorted(arg_match))
    return [c for c in arg_match if not c[1].startswith('arg')]


def get_ref_match(reference_,reference):
    '''


    :param reference_: id for reference event
    :param reference: parsed reference json file
    :return:
    '''
    arg_match = set()

    reference_event = reference[reference_]
    for k in reference_event['arguments']:  #iterate the reference json, and add (arg_num. argumet _value) into the list
        arg_match.add((k['arg_num'].upper(), k['description']))
    print('ref', sorted(arg_match))
    return arg_match


def get_score(q1, q2,system,dwd2template,reference):
    score = 0
    arg_visited = defaultdict(float)
    argmatch = get_arg_match(q1,system,dwd2template) # all the system arguments set
    argmatch2 = get_ref_match(q2,reference)  #all reference arguments set
    # print(argmatch,argmatch2)
    for c in argmatch:  #for each argument in the system event
        for g in argmatch2:  # iterate all reference argument

            if c[0] == g[0]:  # ensure these two are the same  argument
                _pattern = re.compile(r"'s")
                c_args = [re.sub(_pattern, '', arg.lower()) for arg in c[1].split() if not re.match('arg\d', c[1])]
                g_args = [re.sub(_pattern, '', arg.lower()) for arg in g[1].split() if not re.match('arg\d', g[1])]
                # print(c_args, g_args)
                num_overlap = len(set(c_args) & set(g_args)) * 2    #overalpped number of arguments *2: numerator
                num_total = len(set(c_args)) + len(set(g_args))   # number of all arguments   denominator
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