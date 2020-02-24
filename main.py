import sys
from collections import OrderedDict
from copy import deepcopy
import math
import numpy as np

def calc_skip_full(domains, vars):
    output = [1]
    for i in range(len(vars)):
        j = len(vars) - i - 1
        if i == 0:
            continue
        elif i == 1:
            output.insert(0, domains[vars[j+1]])
        else:
            output.insert(0, domains[vars[j+1]] * output[0])
    return output

def calc_skip(domains, vars, index):
    output = 1
    for i in range(len(vars))[::-1]:
        if i == index:
            break
        output *= domains[vars[i]]
    return output


def sum_out(index, vars, values, domains, evid_val=-1):
    output = []
    skip = calc_skip(domains, vars, index)
    dom = domains[vars[index]]

    i = 0
    while i < len(values):
        # we want to skip values that we have already added:
        if (i-skip) % (skip*dom) == 0:
            i += (dom-1)*skip
        if i >= len(values):
            break
        new_val = 0
        j = i
        iteration = 0
        for k in range(dom):
            if evid_val != -1:
                if iteration % dom == evid_val:
                    new_val = values[j]
            else:
                new_val += values[j]
            j += skip
            iteration += 1
        output += [new_val]
        i += 1

    vars_copy = list(deepcopy(vars))
    vars_copy.pop(index)
    vars_copy = tuple(vars_copy)
    # print(skip, vars, values, dom, evid_val)
    return vars_copy, output

def product(vars1, vars2, vals1, vals2, domains):
    def get_index(assignment, skip_full):
        return sum(mult(assignment, skip_full))

    def get_assignment(index, skip, domain):
        return (index // skip) % domain

    def where_in_array(result_vars, vars):
        '''
        basically just returns where the elements of the second array are in the first array
        ex: [0,1,3,2] [3,1,0] -> [2,1,0]
        '''
        return [result_vars.index(i) for i in vars]

    skip_full1 = calc_skip_full(domains, vars1)
    skip_full2 = calc_skip_full(domains, vars2)
    result_vars = tuple(set(list(vars1) + list(vars2)))
    result_vals = []
    result_vals_size = 1
    for var in result_vars: # size of result factor is just product of all the domains
        result_vals_size *= domains[var]
    skip_full_result = calc_skip_full(domains, result_vars)
    for i in range(result_vals_size):
        assignments = [get_assignment(i, skip_full_result[j], domains[result_vars[j]]) for j in range(len(skip_full_result))]
        index1 = get_index([assignments[j] for j in where_in_array(result_vars, vars1)], skip_full1)
        index2 = get_index([assignments[j] for j in where_in_array(result_vars, vars2)], skip_full2)
        # print(index1, index2, vars1, vars2, vals1, vals2)
        # print(vals1[index1])
        # print(vals2[index2])
        result_vals += [vals1[index1]*vals2[index2]]

    return result_vars, result_vals


def mult(a, b):
    return [i*j for i,j in zip(a,b)]


def find_bucket(vars, bucket_ordering):
    return bucket_ordering[min(list(map(bucket_ordering.index, vars)))]

def get_bucket_order(factors):
    # using min degree
    # if a variable appears in a clique, it means that it has an edge from itself to every other variable in the clique
    sets = {}
    for factor in factors.keys():
        if len(factor) > 1: # we dont want to waste time with single factors
            for var in factor:
                if var not in sets:
                    sets[var] = set(factor)
                else:
                    sets[var] = sets[var].union(set(factor))
    print({i:len(sets[i]) for i in sorted(sets.keys())})
    return sorted([i for i in sorted(sets.keys())], key=lambda j: len(sets[j]))

def main():
    """"""
    '''PART 1: loading data'''
    net_file = open(sys.argv[1]).readlines()
    evid_file = open(sys.argv[2]).read().split()[1:]

    factors = OrderedDict()
    evidence = OrderedDict()
    '''
    factors{
        ...
        SIZE_OF_CLIQUE: {
            VARIABLES (VAR1, VAR2, ...): VALUES (VAL1, VAL2, ...)
            ...
        }
        ...
    }
    '''

    for i in range(0, len(evid_file), 2):
        evidence[int(evid_file[i])] = int(evid_file[i+1])
    i = 0
    while i < len(net_file):
        if net_file[i] == '' or net_file[i] == '\n':
            net_file.pop(i)
        else:
            i += 1
    i = 1
    num_vars = int(net_file[i])
    i += 1
    domains = list(map(int, net_file[i].split()))
    i += 1
    num_cliques = int(net_file[i])

    for i in range(i+1, num_cliques+i+1):
        line = list(map(int, net_file[i].split()))
        if line[0] not in factors:
            factors[tuple(line[1:])] = None

    factors[()] = [1] # gotta add this in case we never get this from eliminating evidence

    clique_keys = list(factors.keys())
    i += 2
    j = 0
    while i < len(net_file):
        # print(factors.keys())
        if net_file[i] == '':
            i += 1
            continue

        vals = list(map(np.float64, net_file[i].split()))
        vars = list(clique_keys[j])
        # if any of the variables are part of the evidence, we must eliminate them
        k = 0
        while k < len(vars):
            if vars[k] in evidence:
                old_vars = tuple(deepcopy(vars))

                vars, vals = sum_out(k, vars, vals, domains, evidence[vars[k]])
                if old_vars in factors:
                    factors.pop(old_vars)
                k -= 1
            k += 1
        vars = tuple(vars)
        if vars in factors and factors[vars] != None:
            factors[vars] = mult(factors[vars], vals)
        else:
            factors[vars] = vals
        i += 2
        j += 1


    # print(num_vars, domains, factors)
    # print(evidence)
    # print(sum_out(0, [1, 0, 2], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], domains, 0))
    # print(product((0,1),(0,1),[1,2,3,4],[5,6,7,8],[2,2,2]))
    #print(product((1,),(1,2),factors[(1,)],factors[(1,2)],domains))



    '''PART 2: bucket elim'''

    bucket_order = get_bucket_order(factors)
    if '3.uai' in sys.argv[1]:
        bucket_order = [0, 44, 55, 118, 66, 77, 88, 99, 110, 111, 112, 113, 114, 115, 116, 117, 33, 22, 119, 11, 19, 84, 83, 82, 81, 80, 79, 78, 76, 75, 74, 73, 72, 71, 70, 18, 68, 67, 12, 85, 65, 86, 10, 1,  2,  3,  4,  5,  6,  7,  8,  9, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 87, 64, 69, 62, 38, 37, 36, 63, 34, 16, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 17, 21, 20, 39, 40, 35, 42, 61, 60, 13, 58, 57, 56, 14, 54, 41, 53, 59, 43, 15, 51, 45, 46, 47, 48, 49, 52, 50, 100, 109, 107, 106, 105, 104, 102, 101, 108, 103]
    buckets = OrderedDict()
    for i in bucket_order:
        buckets[i] = []

    for key in factors.keys():
        if not key or factors[key] is None:
            continue
        buckets[find_bucket(key, bucket_order)] += [key]
    print(factors)
    print(buckets)
    debug_flag = False
    for bucket_label in buckets.keys():
        bucket_contents = buckets[bucket_label]
        if bucket_contents:
            print(bucket_label, bucket_contents)
            while len(bucket_contents) > 1:
                vars1 = bucket_contents[0]
                vars2 = bucket_contents[1]
                if vars1 not in factors:
                    bucket_contents.remove(vars1)
                    continue
                if vars2 not in factors:
                    bucket_contents.remove(vars2)
                    continue
                if bucket_label == 109:
                    print('merging', vars1, factors[vars1], vars2, factors[vars2])
                new_vars, new_vals = product(vars1, vars2, factors[vars1], factors[vars2], domains)
                if bucket_label == 109:
                    print('merged', new_vars, new_vals)
                # print('BAZINGA', new_vars, new_vals)
                bucket_contents.remove(vars1)
                bucket_contents.remove(vars2)
                factors.pop(vars1)
                if(vars2 in factors):
                    factors.pop(vars2)

                # print('summing out', new_vars, new_vals)
                # new_vars, new_vals = sum_out(new_vars.index(bucket_label),new_vars,new_vals,domains)
                # print('summed out', new_vars, new_vals)
                if new_vars not in factors:
                    factors[new_vars] = new_vals
                    bucket_contents.insert(0, new_vars)
                    # buckets[find_bucket(new_vars, bucket_order)] += [new_vars]
                else:
                    factors[new_vars] = mult(factors[new_vars], new_vals)
            if len(bucket_contents) == 1:
                # print('before :', bucket_contents)
                vars = bucket_contents[0]
                vals = factors[vars]
                print(bucket_label, vars, vals)
                # print('summing out', vars, vals)
                new_vars, new_vals = sum_out(vars.index(bucket_label), vars, vals, domains)
                # print('summed out', new_vars, new_vals)
                bucket_contents.remove(vars)
                # print('hello', vars, vals, new_vars, new_vals)
                if new_vars not in factors:
                    # print('newvars ', new_vars)
                    factors[new_vars] = new_vals
                    buckets[find_bucket(new_vars, bucket_order)] += [new_vars]
                else:
                    # print('hello', factors[new_vars])
                    factors[new_vars] = mult(factors[new_vars], new_vals)


    print(buckets)
    print(factors)
    print(round(math.log(factors[()][0], 10), 4))



if __name__=='__main__':
    main()