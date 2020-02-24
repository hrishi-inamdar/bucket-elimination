import sys
from collections import OrderedDict
from copy import deepcopy
import math
import numpy as np

def calc_skip_full(domains, vars):
    '''calculate skip values for all variables'''
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
    '''calculate a single skip value for the index given'''
    output = 1
    for i in range(len(vars))[::-1]:
        if i == index:
            break
        output *= domains[vars[i]]
    return output


def sum_out(index, vars, values, domains, evid_val=-1):
    '''sums out the variable at the specified index
        also serves as a way to eliminate evidence if evid_val is given'''
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
    return vars_copy, output

def product(vars1, vars2, vals1, vals2, domains):
    '''returns product of factors vars1 and vars2. values of thoe factors are given as vals1 and vals2
        domains are also needed'''
    def get_index(assignment, skip_full):
        '''given assignment, return the index for the assignment'''
        return sum(mult(assignment, skip_full))

    def get_assignment(index, skip, domain):
        '''given index, return assignment it corresponds to'''
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
        result_vals += [vals1[index1]*vals2[index2]]

    return result_vars, result_vals


def mult(a, b):
    '''element-wise multiplication for vectors'''
    return [i*j for i,j in zip(a,b)]


def find_bucket(vars, bucket_ordering):
    '''gives which bucket the factor belongs to given a bucket order'''
    return bucket_ordering[min(list(map(bucket_ordering.index, vars)))]

def get_bucket_order(factors):
    '''give a min-degree ordering for buckets'''
    # the idea is:
    # if a variable appears in a clique, it means that it has an edge from itself to every other variable in the clique
    # so basically union every clique a variable is in
    sets = {}
    for factor in factors.keys():
        if len(factor) > 1: # we dont want to waste time with single factors
            for var in factor:
                if var not in sets:
                    sets[var] = set(factor)
                else:
                    sets[var] = sets[var].union(set(factor))
    return sorted([i for i in sorted(sets.keys())], key=lambda j: len(sets[j]))

def main():

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




    '''PART 2: bucket elim'''

    bucket_order = get_bucket_order(factors)
    buckets = OrderedDict()
    for i in bucket_order:
        buckets[i] = []

    for key in factors.keys():
        if not key or factors[key] is None:
            continue
        buckets[find_bucket(key, bucket_order)] += [key]
    # print(factors)
    # print(buckets)
    for bucket_label in buckets.keys():
        bucket_contents = buckets[bucket_label]
        if bucket_contents:
            while len(bucket_contents) > 1:
                vars1 = bucket_contents[0]
                vars2 = bucket_contents[1]
                if vars1 not in factors:
                    bucket_contents.remove(vars1)
                    continue
                if vars2 not in factors:
                    bucket_contents.remove(vars2)
                    continue
                new_vars, new_vals = product(vars1, vars2, factors[vars1], factors[vars2], domains)
                bucket_contents.remove(vars1)
                bucket_contents.remove(vars2)
                factors.pop(vars1)
                if(vars2 in factors):
                    factors.pop(vars2)
                if new_vars not in factors:
                    factors[new_vars] = new_vals
                    bucket_contents.insert(0, new_vars)
                else:
                    factors[new_vars] = mult(factors[new_vars], new_vals)
            if len(bucket_contents) == 1:
                vars = bucket_contents[0]
                vals = factors[vars]
                new_vars, new_vals = sum_out(vars.index(bucket_label), vars, vals, domains)
                bucket_contents.remove(vars)
                if new_vars not in factors:
                    factors[new_vars] = new_vals
                    buckets[find_bucket(new_vars, bucket_order)] += [new_vars]
                else:
                    factors[new_vars] = mult(factors[new_vars], new_vals)


    # print(buckets)
    # print(factors)
    print(round(math.log(factors[()][0], 10), 4))



if __name__=='__main__':
    main()