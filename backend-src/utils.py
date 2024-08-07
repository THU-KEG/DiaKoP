import torch
import random
import numpy as np
import os
import re

def seed_everything(seed=1029):

    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True

def get_dep(program, inputs):
    program = ['<START>'] + program + ['<END>']
    inputs = [[]] + inputs + [[]]
    dependency = []
    branch_stack = []
    for i, p in enumerate(program):
        if p in {'<START>', '<END>', '<PAD>'}:
            dep = [0, 0]
        elif p in {'FindAll', 'Find'}:
            dep = [0, 0]
            branch_stack.append(i - 1)
        elif p in {'And', 'Or', 'SelectBetween', 'QueryRelation', 'QueryRelationQualifier'}:
            dep = [branch_stack[-1], i-1]
            branch_stack = branch_stack[:-1]
        else:
            dep = [i-1, 0]
        dependency.append(dep)

    assert len(program) == len(inputs)
    assert len(program) == len(dependency)

    for i in range(len(dependency)):
        dependency[i] = [dependency[i][0] - 1, dependency[i][1] - 1]
    return dependency[1:-1]
    