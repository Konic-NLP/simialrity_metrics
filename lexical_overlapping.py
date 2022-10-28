import re
from collections import  defaultdict

def get_arg_match(system_event,system, dwd2template):
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


def get_ref_match(reference_,reference):
    arg_match = set()

    reference_event = reference[reference_]
    for k in reference_event['arguments']:
        arg_match.add((k['arg_num'].upper(), k['description']))
    print('ref', sorted(arg_match))
    return arg_match


def get_score(q1, q2,system,dwd2template,reference):
    score = 0
    arg_visited = defaultdict(float)
    argmatch = get_arg_match(q1,system,dwd2template)
    argmatch2 = get_ref_match(q2,reference)
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