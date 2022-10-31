import pandas as pd
from itertools import product
from kgtk import call_semantic_similarity


def get_similarity(q1, q2, sys_arg_newmatch, ref_arg_newmatch):
    '''

    compute the similarity score for a pair of events
    :param q1:  id for system event
    :param q2:   id for reference event
    :param sys_arg_newmatch:  store the corresponding
    :param ref_arg_newmatch:
    :return:
    '''
    num_ = 0
    total_score = 0
    if q1 in sys_arg_newmatch and q2 in ref_arg_newmatch:
        sys_args = sys_arg_newmatch[q1].keys()
        ref_args = ref_arg_newmatch[q2].keys()
        # get all arguments for the event
        num_ = (len(set([i for i in sys_args if sys_arg_newmatch[i] != []]) & set(
            [j for j in ref_args if ref_arg_newmatch[q2][j] != []])))
        for sys_arg in sys_args:  # iterate each argument id
            if sys_arg in ref_args:
                best_score = 0
                # qnode list
                sys_arg_qnodes = sys_arg_newmatch[q1][sys_arg]
                ref_arg_qnodes = ref_arg_newmatch[q2][sys_arg]
                if not sys_arg_qnodes:
                    continue
                # print(sys_arg_qnodes,ref_arg_qnodes)

                pairs = list(product(*(sys_arg_qnodes, ref_arg_qnodes)))  # the combination for all qnode
                #e.g   arg1 of system event =[q1,q2,q3]  arg1 of reference event =[q4,q5], return
                # (q1,q4),(q1,q5),(q2,q4),(q2,15)...... this applied to the qnode after rempping is not one
                # print(pairs)
                s1 = [a[0] for a in pairs]
                s2 = [a[1] for a in pairs]
                df = {'q1': s1, 'q2': s2}
                df = pd.DataFrame(df)  #create a tsv file for kgtk api query the score

                df.to_csv('temp.tsv', sep='\t')
                result = call_semantic_similarity('temp.tsv')  #get the score from kgtk api
                # print(result)
                # result[result=='']=0
                result.to_csv('test_file_similarity.tsv', index=False, sep='\t')

                score = result.apply(get_total_score, axis=1)  # for each row, call the get total score function
                # print(score)
                # print(type(score),max(score))
                print('-------end------')
                try:
                    total_score += max(score)   # the total score for the pair of argument is the highest one among all combnation
                except:
                    print(q1,q2,sys_arg_qnodes,ref_arg_qnodes)
        # print(q2, total_score)
    if num_ == 0:
        return 0
    return total_score / num_

def get_total_score(row):
    '''
    compute the score returned by kgtl api and sum over all six types similarity score
    as the final score

    :param row:
    :return:
    '''
    score=0
    if row['q1_label']!='' and row['q2_label']!="":   #handle the edge case
        row[row==""]=0
        num=0
        for type_score in ['complex','topsim','transe','text','class']:  #handle the edge case and get the number of non-zero score

            if row[type_score]!=0:
                num+=1
        score=row['complex']+row['topsim']+row['transe']+row['text']+row['jc']+row['class']  # sum over all score as the terminal score
        if num==0:
            return 0
        else:
            score=score/num  #normalized score by dividing the number of non-zero socres
            return score