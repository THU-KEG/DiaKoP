import requests
import os
import graphviz
import time
import copy
from PIL import Image
import re
import json
import datetime
from json_helper import sanitize_and_parse_json
import ast

from fastchat.constants import (
    LOGDIR,
    WORKER_API_TIMEOUT
)

def avail_kopl_functions_new():
    func = {
        "FindAll": {
            "description": "Return all entities in KB",
            "arguments": [],
            "inputs": [],
            "outputs": ["Entities"],
            "example": "FindAll()",
        },
        "Find": {
            "description": "Return all entities with the given name",
            "arguments": ["Entity Name"],
            "inputs": [],
            "outputs": ["Entities"],
            "example": "Find(LeBron James)",
        },
        "QueryRelation": {
            "description": "Return the relation between two entities",
            "arguments": [],
            "inputs": ["Entities", "Entities"],
            "outputs": ["Pred"],
            "example": "QueryRelation(LeBron James, Cleveland Cavaliers)",
        },
        "FilterConcept": {
            "description": "Find those belonging to the given concept",
            "arguments": ["Concept"],
            "inputs": ["Entities"],
            "outputs": ["Entities"],
            "example": "FilterConcept(athlete)"
        },
        "FilterAttr": {
            "description": "Filter entities with an attribute condition of four data types, that is string, year, date and quantity, return entities and corresponding facts",
            "arguments": ["Attribute Key", "Attribute Value", "Operator", "Attribute Type"],
            "inputs": ["Entities"],
            "outputs": ["Entities+Facts"],
            "example": "FilterAttr(height, 200 centimetres, >, quantity)",
        },
        "FilterQualifier": {
            "description": "Filter entities and corresponding facts with a qualifier condition of four data types, that is string, year, date and quantity",
            "arguments": ["Qualifier Key", "Qualifier Value", "Operator", "Qualifier Type"],
            "inputs": ["Entities+Facts"],
            "outputs": ["Entities+Facts"],
            "example": "FilterQualifier(start time, 1980, =, year)",
        },
        "Relate": {
            "description": "Find entities that have a specific relation with the given entity",
            "arguments": ["Relation", "Direction"],
            "inputs": ["Entities"],
            "outputs": ["Entities+Facts"],
            "example": "Relate(capital, forward)",
        },
        "And": {
            "description": "Return the intersection of two entity sets",
            "arguments": [],
            "inputs": ["Entities", "Entities"],
            "outputs": ["Entities"],
            "example": "And()",
        },
        "Or": {
            "description": " Return the union of two entity sets",
            "arguments": [],
            "inputs": ["Entities", "Entities"],
            "outputs": ["Entities"],
            "example": "Or()",
        },
        "Not": { # this operator is new
            "description": "Return the complement of the second set within the first set",
            "arguments": [],
            "inputs": ["Entities", "Entities"],
            "outputs": ["Entities"],
            "example": "Not()",
        },
        "QueryName": {
            "description": "Return the entity name",
            "arguments": [],
            "inputs": ["Entities"],
            "outputs": ["string"],
            "example": "QueryName()",
        },
        "Count": {
            "description": "Return the number of entities",
            "arguments": [],
            "inputs": ["Entities"],
            "outputs": ["number"],
            "example": "Count()",
        },
        "QueryAttr": {
            "description": "Return the attribute value of the entity", 
            "arguments": ["Attribute Key"],
            "inputs": ["Entities"],
            "outputs": ["Value"],
            "example": "QueryAttr(height)",
        },
        "QueryAttrUnderCondition": {
            "description": "Return the attribute value, whose corresponding fact should satisfy the qualifier condition",
            "arguments": ["Attribute Key", "Qualifier Key", "Qualifier Value"],
            "inputs": ["Entities"],
            "outputs": ["Value"],
            "example": "QueryAttrUnderCondition(population, point in time, 2019)",
        },
        "Select": {
            "description": "Given a set of entities, it returns the entity names with specific attribute values starting from <OFFSET> for the most <TOPK> largest/smallest",
            "arguments": ["Attribute Key", "Operator", "offset", "topk"],
            "inputs": ["Entities", "Entities"],
            "outputs": ["string"],
            "example": "Select(height, largest, 0, 1)",
        },
        "Verify": {
            "description": "Verify if the inputs satisfy the condition, inputs can be string, number, year, date data types",
            "arguments": ["Target", "Operator", "Target type"],
            "inputs": ["Value"],
            "outputs": ["boolean"],
            "example": "Verify(1980-06-01, >, date)",
        },
        "QueryAttrQualifier": {
            "description": "Return the qualifier value of the fact (Entity, Key, Value)",
            "arguments": ["Attribute Key", "Attribute Value", "Operator"],
            "inputs": ["Entities"],
            "outputs": ["QValue"],
            "example": "QueryAttrQualifier(population, 199,110, point in time)",
        },
        "QueryRelationQualifier": {
            "description": "Return the qualifier value of the fact (Entity, Pred, Entity)",
            "arguments": ["Relation", "Qualifier Key"],
            "inputs": ["Entities", "Entities"],
            "outputs": ["QValue"],
            "example": "QueryRelationQualifier(drafted by, point in time)"
        },
        "Sum": { # this operator is new, other details to-do
            "description": "Calculate the sum of the given attribute values",
        },
        "Average": { # this operator is new, other details to-do
            "description": "Calculate the average of the given attribute values",
        },
        "Subtract": { # this operator is new, other details to-do
            "description": "Calculate the difference of the given attribute values",
        },
        "QueryConcept": { # this operator is new, other details to-do
            "description": "Return the names of entity concepts",
        }
    }

    return func

def avail_kopl_functions():
    func = {
        "FindAll": {
            "description": "Return all entities in KB",
            "arguments": [],
            "inputs": [],
            "outputs": ["Entities"],
            "example": "FindAll()",
        },
        "Find": {
            "description": "Return all entities with the given name",
            "arguments": ["Entity Name"],
            "inputs": [],
            "outputs": ["Entities"],
            "example": "Find(LeBron James)",
        },
        "QueryRelation": {
            "description": "Return the relation between two entities",
            "arguments": [],
            "inputs": ["Entities", "Entities"],
            "outputs": ["Pred"],
            "example": "QueryRelation(LeBron James, Cleveland Cavaliers)",
        },
        "FilterConcept": {
            "description": "Find those belonging to the given concept",
            "arguments": ["Concept"],
            "inputs": ["Entities"],
            "outputs": ["Entities"],
            "example": "FilterConcept(athlete)"
        },
        "FilterStr": {
            "description": "Filter entities with an attribute condition of string type, return entities and corresponding facts",
            "arguments": ["Attribute Key", "Attribute Value"],
            "inputs": ["Entities"],
            "outputs": ["Entities+Facts"],
            "example": "FilterStr(gender, male)",
        },
        "FilterNum": {
            "description": "Similar to FilterStr, except that the attribute type is number",
            "arguments": ["Attribute Key", "Attribute Value", "Operator"],
            "inputs": ["Entities"],
            "outputs": ["Entities+Facts"],
            "example": "FilterNum(height, 200 centimetres, >)",
        },
        "FilterYear": {
            "description": "Similar to FilterStr, except that the attribute type is year",
            "arguments": ["Attribute Key", "Attribute Value", "Operator"],
            "inputs": ["Entities"],
            "outputs": ["Entities+Facts"],
            "example": "FilterYear(birthday, 1980, =)",
        },
        "FilterDate": {
            "description": "Similar to FilterStr, except that the attribute type is date",
            "arguments": ["Attribute Key", "Attribute Value", "Operator"],
            "inputs": ["Entities"],
            "outputs": ["Entities+Facts"],
            "example": "FilterDate(birthday, 1980-06-01, <)",
        },
        "QFilterStr": {
            "description": "Filter entities and corresponding facts with a qualifier condition of string type",
            "arguments": ["Qualifier Key", "Qualifier Value"],
            "inputs": ["Entities+Facts"],
            "outputs": ["Entities+Facts"],
            "example": "QFilterStr(language, English)",
        },
        "QFilterNum": {
            "description": "Filter entities and corresponding facts with a qualifier condition of number type", 
            "arguments": ["Qualifier Key", "Qualifier Value", "Operator"],
            "inputs": ["Entities+Facts"],
            "outputs": ["Entities+Facts"],
            "example": "QFilterNum(bonus, 20000 dollars, >)",
        },
        "QFilterYear": {
            "description": "Filter entities and corresponding facts with a qualifier condition of year type",
            "arguments": ["Qualifier Key", "Qualifier Value", "Operator"],
            "inputs": ["Entities+Facts"],
            "outputs": ["Entities+Facts"],
            "example": "QFilterYear(start time, 1980, =)",
        },
        "QFilterDate": {
            "description": "Filter entities and corresponding facts with a qualifier condition of date type",
            "arguments": ["Qualifier Key", "Qualifier Value", "Operator"],
            "inputs": ["Entities+Facts"],
            "outputs": ["Entities+Facts"],
            "example": "QFilterDate(start time, 1980-06-01, <)",
        },
        "Relate": {
            "description": "Find entities that have a specific relation with the given entity",
            "arguments": ["Relation", "Direction"],
            "inputs": ["Entities"],
            "outputs": ["Entities+Facts"],
            "example": "Relate(capital, forward)",
        },
        "And": {
            "description": "Return the intersection of two entity setsy",
            "arguments": [],
            "inputs": ["Entities", "Entities"],
            "outputs": ["Entities"],
            "example": "And()",
        },
        "Or": {
            "description": " Return the union of two entity sets",
            "arguments": [],
            "inputs": ["Entities", "Entities"],
            "outputs": ["Entities"],
            "example": "Or()",
        },
        "QueryName": {
            "description": "Return the entity name",
            "arguments": [],
            "inputs": ["Entities"],
            "outputs": ["string"],
            "example": "QueryName()",
        },
        "Count": {
            "description": "Return the number of entities",
            "arguments": [],
            "inputs": ["Entities"],
            "outputs": ["number"],
            "example": "Count()",
        },
        "QueryAttr": {
            "description": "Return the attribute value of the entity", 
            "arguments": ["Attribute Key"],
            "inputs": ["Entities"],
            "outputs": ["Value"],
            "example": "QueryAttr(height)",
        },
        "QueryAttrUnderCondition": {
            "description": "Return the attribute value, whose corresponding fact should satisfy the qualifier condition",
            "arguments": ["Attribute Key", "Qualifier Key", "Qualifier Value"],
            "inputs": ["Entities"],
            "outputs": ["Value"],
            "example": "QueryAttrUnderCondition(population, point in time, 2019)",
        },
        "SelectBetween": {
            "description": "From the two entities, find the one whose attribute value is greater or less and return its name",
            "arguments": ["Attribute Key", "Operator"],
            "inputs": ["Entities", "Entities"],
            "outputs": ["string"],
            "example": "SelectBetween(height, greater)",
        },
        "SelectAmong": {
            "description": "From the entity set, find the one whose attribute value is the largest or smallest",
            "arguments": ["Attribute Key", "Operator"],
            "inputs": ["Entities"],
            "outputs": ["string"],
            "example": "SelectAmong(height, largest)",
        },
        "VerifyStr": {
            "description": "Return whether the output of QueryAttr or QueryAttrUnderCondition and the given value are equal as string",
            "arguments": ["Target Str"],
            "inputs": ["Value"],
            "outputs": ["boolean"],
            "example": "VerifyStr(male)",
        },
        "VerifyNum": {
            "description": "Return whether the two numbers satisfy the condition",
            "arguments": ["Target Num", "Operator"],
            "inputs": ["Value"],
            "outputs": ["boolean"],
            "example": "VerifyNum(20000 dollars, >)"
        },
        "VerifyYear": {
            "description": " Return whether the two years satisfy the condition", 
            "arguments": ["Target Year", "Operator"],
            "inputs": ["Value"],
            "outputs": ["boolean"],
            "example": "VerifyYear(1980,  >)"
        },
        "VerifyDate": {
            "description": " Return whether the two date satisfy the condition",
            "arguments": ["Target Date", "Operator"],
            "inputs": ["Value"],
            "outputs": ["boolean"],
            "example": "VerifyDate(1980-06-01, >)"
        },
        "QueryAttrQualifier": {
            "description": "Return the qualifier value of the fact (Entity, Key, Value)",
            "arguments": ["Attribute Key", "Attribute Value", "Operator"],
            "inputs": ["Entities"],
            "outputs": ["QValue"],
            "example": "QueryAttrQualifier(population, 199,110, point in time)",
        },
        "QueryRelationQualifier": {
            "description": "Return the qualifier value of the fact (Entity, Pred, Entity)",
            "arguments": ["Relation", "Qualifier Key"],
            "inputs": ["Entities", "Entities"],
            "outputs": ["QValue"],
            "example": "QueryRelationQualifier(drafted by, point in time)"
        }
    }

    return func

def semantic_parsing_api(question):
    url = "http://localhost:6061/predict"

    payload = {'question': question}
    files=[

    ]
    headers = {}

    response = requests.request("POST", url, headers=headers, data=payload, files=files)

    return response.json()['program']

def is_valid_number(arg_str):
    arg_str = arg_str.strip()
    arg_split = arg_str.split(" ", maxsplit=1)
    if arg_split:
        num = arg_split[0]
        return re.match(r'^[+-]?\d+(\.\d+)?$', num)
    else:
        return False
    
 
def is_valid_year(arg_str):
    arg_str = arg_str.strip()
    if arg_str.startswith('-'):
        arg_str = arg_str[1:]
    if not arg_str.isdigit():
        return False
    try:
        arg_year = int(arg_str)
    except ValueError:
        return False
    return True

def is_valid_date(arg_str):
    date_format = "%Y-%m-%d"
    arg_str = arg_str.strip()
    try: 
        datetime.strptime(arg_str, date_format)
        return True
    except ValueError:
        return False
    
def is_valid_arg(func, arg_str):
    if func in ["FilterNum", "QFilterNum", "VerifyNum"]:
        if is_valid_number(arg_str):
            return True
        else:
            print(f"Function {func} has wrong argument. Expected: Num type, got: {arg_str}")
            return False
    elif func in ["FilterYear", "QFilterYear", "VerifyYear"]:
        if is_valid_year(arg_str):
            return True
        else:
            print(f"Function {func} has wrong argument. Expected: Year type, got: {arg_str}")
            return is_valid_year(arg_str)
    elif func in ["FilterDate", "QFilterDate", "VerifyDate"]:
        if is_valid_date(arg_str):
            return True
        else:
            print(f"Function {func} has wrong argument. Expected: Date type, got: {arg_str}")
            return is_valid_date(arg_str)
        
    else:
        return True

def reverse_program(program):
    """
    Reverse to old version of kopl
    """
    original_functions = []
    # dependency_map = {func['dependencies'][0]: idx for idx, func in enumerate(program)}

    for idx, func in enumerate(program):
        original_func = None
        
        if func['function'] == 'QueryName' and program[idx-1]['function'] =='Select':
            continue
        if func['function'] == 'Or' and program[idx+1]['function'] =='Select':
            continue
        elif func['function'] == 'Select' and program[idx-1]['function'] =='Or':
            direction = 'greater' if func['inputs'][1] == 'largest' else 'less'
            original_func = {
                'function': 'SelectBetween',
                'dependencies': program[idx-1]['dependencies'],
                'inputs': [func['inputs'][0], direction]
            }
        elif func['function'] == 'Select' and program[idx-1]['function'] !='Or':
            original_func = {
                'function': 'SelectAmong',
                'dependencies': func['dependencies'],
                'inputs': func['inputs'][:2]  # Assuming the first two inputs are the key parameters.
            }
        elif func['function'] == 'FilterAttr':
            # Map 'FilterAttr' back to the specific filter functions based on the type in inputs.
            type_map = {
                'string': 'FilterStr',
                'year': 'FilterYear',
                'date': 'FilterDate',
                'quantity': 'FilterNum'
            }
            original_func = {
                'function': type_map[func['inputs'][-1]],
                'dependencies': func['dependencies'],
                'inputs': func['inputs'][:-2] if func['inputs'][-1] == 'string' else func['inputs'][:-1]
            }
        elif func['function'] == 'Verify':
            # Map 'Verify' back to the specific verify functions based on the type in inputs.
            type_map = {
                'string': 'VerifyStr',
                'year': 'VerifyYear',
                'date': 'VerifyDate',
                'quantity': 'VerifyNum'
            }
            original_func = {
                'function': type_map[func['inputs'][-1]],
                'dependencies': func['dependencies'],
                'inputs': func['inputs'][:-2] if func['inputs'][-1] == 'string' else func['inputs'][:-1]
            }
        elif func['function'] == 'FilterQualifier':
            # Map 'FilterQualifier' back to the specific qualifier filter functions.
            type_map = {
                'string': 'QFilterStr',
                'year': 'QFilterYear',
                'date': 'QFilterDate',
                'quantity': 'QFilterNum'
            }
            original_func = {
                'function': type_map[func['inputs'][-1]],
                'dependencies': func['dependencies'],
                'inputs': func['inputs'][:-2] if func['inputs'][-1] == 'string' else func['inputs'][:-1]
            }
        else:
            original_func = func  # Other functions remain unchanged.

        if original_func:
            original_functions.append(original_func)

    return original_functions

def preprocess_program(program):
    # Step 1: Modify the program
    new_program = []
    
    try:
        assert type(program) == list, "Expect input program is list type" # make sure the program is in the form of list
    except:
        return ""
    
    for item in program:
        try:
            assert type(item) == dict and len(item) > 0  # make sure the item is dict and has content
        except:
            continue
        # Process 1-0: clean the keys to avoid case like " function"
        item = {key.strip(): value for key, value in item.items()}

        # Process 1-1: rename 'dep' and 'func'
        if 'dep' in item:
            item['dependencies'] = item.pop('dep')
        if 'func' in item:
            item['function'] = item.pop('func')

        # Process 1-2: replace 'What' with 'QueryName'
        if 'What' == item['function']:
            item['function'] = 'QueryName'
        
        # Process 1-3: check if dependencies, function and input exist
        if 'dependencies' not in item:
            item['dependencies'] = [-1, -1]
        if 'function' not in item:
            item['function'] = ""
        if 'inputs' not in item:
            item['inputs'] = []

        # Process: 1-4: assert the values of dependencies is a list of int, using isinstance
        try:
            assert isinstance(item['dependencies'], list)
            assert all(isinstance(i, int) for i in item['dependencies'])
        except:
            item['dependencies'] = [-1, -1]

        # Process 1-5: check if dependencies have 2 elements
        if len(item['dependencies']) < 2:
            # item['dependencies'].sort(reverse=True)
            while len(item['dependencies']) < 2:
                item['dependencies'].append(-1)

        new_program.append(item)

    return new_program

def program_is_valid(program):
    """
    Check if the generated program is valid

    Args:
        program (str): the generated program

    Returns:
        bool: True if the program is valid, False otherwise
        str: the error message if the program is invalid
    """
    if isinstance(program, str):
        program = ast.literal_eval(program)
        
    output_node = ['Count', 'QueryAttr', 'QueryName', 'QueryNeighbor', 
                   'VerifyStr', 'VerifyNum', 'VerifyYear', 'VerifyDate', 'Verify',
                   'SelectBetween', 'SelectAmong',
                   'QueryAttrQualifier', 'QueryRelationQualifier', 'QueryAttrUnderCondition',
                   'QueryRelation']
    
    program = preprocess_program(program)

    # Process 0: check if program is empty
    if len(program) == 0:
        raise Exception("empty program")

    try:
        # reverse to old program at the moment
        program = reverse_program(program)
    except Exception as e:
        raise Exception("invalid new kopl operator")

    # Process 2: Legality check
    kopl_func_dict = avail_kopl_functions()
    for i in range(len(program)):
        item = program[i]  
        item_func = item['function']
        input_types = []
        
        # Process 2-1: check if func avail in KoPL
        try:
            gen_kopl_func = kopl_func_dict[item_func]
        except KeyError:
            raise Exception("func not exist")

        # Process 2-2: check for self-loop, and invalid dep_id
        for dep_id in item['dependencies']:
            if dep_id == i:
                raise Exception("self-loop")
            if dep_id+1 > len(program):
                raise Exception("dependency out of bound")
            elif dep_id != -1:
                dep_func = program[dep_id]['function']
                try:
                    assert dep_func in kopl_func_dict
                except:
                    raise Exception("func not exist")
                input_types.extend(kopl_func_dict[dep_func]["outputs"])
        
        expected_types = gen_kopl_func["inputs"]
        # Number mismatch
        if len(input_types) != len(expected_types):
            raise Exception("wrong number of functional inputs")
        
        for input_type, expected_type in zip(input_types, expected_types):
            # Type match
            if input_type == expected_type:
                continue
            # ”Entities+Facts“ can serve as the actual input for "Entities"
            elif input_type == "Entities+Facts" and expected_type == "Entities":
                continue 
            # Type mismatch
            else:
                raise Exception("wrong functional inputs type")
            
        # Process 2-2: check the number of textual inputs
        # based on avail_kopl_functions, check if the number of arguments of the function is correct
        if len(item['inputs']) != len(kopl_func_dict[item['function']]['arguments']):
            raise Exception("wrong number of textual inputs")
        
        # Process 2-2-1: make sure the input is not empty (Eg: inputs': ['area', '', ''])
        if len(item['inputs']) == len(kopl_func_dict[item['function']]['arguments']):
            for inp in item['inputs']:
                try:
                    assert isinstance(inp, str) 
                except:
                    raise Exception("functional input is not str")
                
                if len(inp) == 0:
                    raise Exception("empty input")
        
        # Process 2-3: Check the value type of textual inputs         
        arg_str = ""
        if item_func in ["FilterNum", "FilterYear", "FilterDate",
                        "QFilterNum", "QFilterYear", "QFilterDate"]:
            arg_str = item['inputs'][1]

            # assert arg_str is string instance
            try:
                assert isinstance(arg_str, str)
            except:
                raise Exception("wrong functional inputs type")

            if not is_valid_arg(item_func, arg_str):
                # raise Exception(f"Function {item_func} has wrong argument. Expected: Num/Year/Date type, got: {arg_str}")
                raise Exception("wrong functional inputs type")
            
        elif item_func in ["VerifyNum", "VerifyYear", "VerifyDate"]:
            arg_str = item['inputs'][0]
            if not is_valid_arg(item_func, arg_str):
                # raise Exception(f"Function {item_func} has wrong argument. Expected: Num/Year/Date type, got: {arg_str}")
                raise Exception("wrong functional inputs type")
            
        # Process 2-4: Check the operator of textual inputs
        if item_func in ["FilterNum", "FilterYear", "FilterDate",
                        "QFilterNum", "QFilterYear", "QFilterDate"]:
            op = item['inputs'][2]
            if op not in ["=", "!=", "<", ">"]:
                # raise Exception(f"Function {item_func} has wrong operator. Expected: =/!=/</>, got: {op}")
                raise Exception("wrong operator")
        elif item_func in ["VerifyNum", "VerifyYear", "VerifyDate"]:
            op = item['inputs'][1]
            if op not in ["=", "!=", "<", ">"]:
                # raise Exception(f"Function {item_func} has wrong operator. Expected: =/!=/</>, got: {op}")
                raise Exception("wrong functional inputs type")
        elif item_func == "SelectBetween":
            op = item['inputs'][1]
            if op not in ["less", "greater"]:
                # raise Exception(f"Function {item_func} has wrong operator. Expected: less or greater, got: {op}")
                raise Exception("wrong operator")
        elif item_func == "SelectAmong":
            op = item['inputs'][1]
            if op not in ["smallest", "largest"]:
                # raise Exception(f"Function {item_func} has wrong operator. Expected: smallest or largest, got: {op}")
                raise Exception("wrong operator")
    
    # Process 3: Check if there is only one output node
    # Find candidates and their usage as dependencies
    candidates = []
    as_src = []

    for idx, node in enumerate(program):
        if node['function'] in output_node:
            candidates.append(idx)
        for dep in node['dependencies']:
            if dep in candidates:
                as_src.append(dep)

    # Check for the conditions
    if len(candidates) == 0:
        raise Exception("missing output functions")
    # elif len(candidates) - len(set(as_src)) > 1:
    elif len(candidates) - len(as_src) > 1:
        raise Exception("more than one output node")
    
    # Process 4: Check if there are isolated nodes, number of edges == number of nodes - 1
    n_nodes = len(program)
    n_edges = 0
    for item in program:
        for dep_id in item['dependencies']:
            if dep_id != -1:
                n_edges += 1
    if n_edges != n_nodes - 1:
        raise Exception("isolated nodes")

    return program

def kopl_engine_exec_api(program, url):
    payload = {'program': program}
    files=[

    ]
    headers = {}

    response = requests.request("POST", url, headers=headers, json=payload, files=files)

    return response.json()

def get_graph_templates():

    graph_template = """
    digraph G_demo {{
        rankdir=LR;
        node [shape=record];

    {nodes}

    {edges}

    }}
    """

    node_template_generic = '    {node_id} [label="{{{{{{{function}}} | {input}}}}}"];'
    node_template_special = '    {node_id} [label="{{{{{{{function}}}}}}}"];'

    edge_template = '    {from_node} -> {to_node};'

    return graph_template, node_template_generic, node_template_special, edge_template

def parse_dot_graph(program):
    func_args_pair = {
        "Find": ["Entity Name"],
        "QueryRelation": ["Relation", "Qualifier Key"],
        "FilterConcept": ["Concept"],
        "FilterStr": ["Attribute Key", "Attribute Value"],
        "FilterNum": ["Attribute Key", "Attribute Value", "Operator"],
        "FilterYear": ["Attribute Key", "Attribute Value", "Operator"],
        "FilterDate": ["Attribute Key", "Attribute Value", "Operator"],
        "QFilterStr": ["Qualifier Key", "Qualifier Value"],
        "QFilterNum": ["Qualifier Key", "Qualifier Value", "Operator"],
        "QFilterYear": ["Qualifier Key", "Qualifier Value", "Operator"],
        "QFilterDate": ["Qualifier Key", "Qualifier Value", "Operator"],
        "Relate": ["Relation", "Direction"],
        "QueryAttr": ["Attribute Key"],
        "QueryAttrUnderCondition": ["Attribute Key", "Qualifier Key", "Qualifier Value"],
        "SelectBetween": ["Attribute Key", "Operator"],
        "SelectAmong": ["Attribute Key", "Operator"],
        "VerifyStr": ["Target Str"],
        "VerifyNum": ["Target Num", "Operator"],
        "VerifyYear": ["Target Year", "Operator"],
        "VerifyDate": ["Target Date", "Operator"],
        "QueryAttrQualifier": ["Attribute Key", "Attribute Value", "Operator"],
        "QueryRelationQualifier": ["Relation", "Qualifier Key"],
        
    }
    graph_template, node_template_generic, node_template_special, edge_template = get_graph_templates()

    nodes = []
    edges = []
    for idx, item in enumerate(program):
        node_id = f"node{idx}"
        function = item["function"]

        # Map inputs according to func_args_pair
        if function in func_args_pair:
            for i in range(len(item["inputs"])):
                item["inputs"][i] = item["inputs"][i].replace("<", "\<").replace(">","\>")
                item["inputs"][i] = item["inputs"][i].replace("{", "\}").replace("}","\}")
                item["inputs"][i] = item["inputs"][i].replace("|", "\|")
                                                                                                                                                                  
            inputs = "| ".join(f"{{{arg}:| {val}}}" for arg, val in zip(func_args_pair[function], item["inputs"]))
        else:
            inputs = "| ".join(item["inputs"])
        # print(inputs)

        # Special node for operator below without arguments
        if function in {"FindAll", "And", "Or", "Count", "QueryName", "QueryRelation", "What"}:
            nodes.append(node_template_special.format(node_id=node_id, function=function))
        else:
            nodes.append(node_template_generic.format(node_id=node_id, function=function, input=inputs))

        for dep in item["dependencies"]:
            if dep == -1:
                continue
            edges.append(edge_template.format(from_node=f"node{dep}", to_node=node_id))

    dot_graph = graph_template.format(nodes = "\n".join(nodes), edges = "\n".join(edges))
    return dot_graph

def enlarge_image(image_path):
    img = Image.open(image_path)
    img = img.resize((img.size[0]*3, img.size[1]*3), Image.ANTIALIAS)
    img.save(image_path)

def render_graph(conv_id, program=''):
    # conv_id_short = conv_id[-4:]
    graph_outfile_name = os.path.join(LOGDIR, 'graphs', f"graph_output_{conv_id}")
    
    if os.path.exists(f"{graph_outfile_name}.png"):
        print(f"Graph {graph_outfile_name}.png already exists, removing it.\n{'-'*60}")
        os.remove(f"{graph_outfile_name}.png")

    if program != '':
        dot_graph = parse_dot_graph(program)

        # Create a Source object
        graph = graphviz.Source(dot_graph)

        # Render the graph to a file (e.g., in PNG format)
        # print(f"Saved Graph {graph_outfile_name}.png.\n{'-'*60}")
        graph.render(graph_outfile_name, format='png')

    elif program == '':
        width, height = 100, 100  # Specify the width and height of the image
        img = Image.new('RGB', (width, height), color = 'white')

        # Save the image
        img.save(f"{graph_outfile_name}.png")

    return dot_graph

def construct_func_result_pair(program, result, max_inter_res_cnt=5):
    # func_list[i] correspond to results_list[i]. Why not store in dict, because we might have same func name in on program
    func_list = []
    results_list = []

    inter_results = result['inner_content']
    funcs = [x['function'] for x in program]
    
    for idx, func in enumerate(funcs):
        # if intermediate result is none, or intermediate result is empty list
        if inter_results[idx] is None or (type(inter_results[idx]) == list and len(inter_results[idx]) == 0):
            func_list.append(func)
            results_list.append(None)
            continue
        
        # if intermediate result is a long list, loop through result, extract 'entity_label' from the dict
        if type(inter_results[idx]) == list and len(inter_results[idx]) > 0:
            tmp_list = [] # store the extracted intermediate result
            for res in inter_results[idx]:
                for key, val in res.items():
                    if key == 'entity_label':
                        tmp_list.append(val)

            func_list.append(func)
            results_list.append(tmp_list[:max_inter_res_cnt])
        
        # if intermediate result is not a list, but just a dict
        else:
            if 'content' in inter_results[idx].keys():
                func_list.append(func)

                if type(inter_results[idx]['content']) == list and len(inter_results[idx]['content']) > 0:
                    results_list.append(inter_results[idx]['content'][:max_inter_res_cnt])
                elif type(inter_results[idx]['content']) == list and len(inter_results[idx]['content']) == 0:
                    results_list.append(None)
                else:
                    results_list.append(inter_results[idx]['content'])

    return func_list, results_list

def preprocess_factual_prompt(program, result):
    """
    Preprocess to get parsed_intermediate_result for factual prompt, steps:
    1. NLP -> KoPL by calling semantic_parsing_api()
    2. Draw graph to represent KoPL
    3. Execute KoPL to get the answer for the intermediate operators
    4. Build pairs of "operator <-> result". E.g., "Find" <-> "People's Republic of China"
    5. Parse the pairs in the form of html table. LLM likes structured prompt!
    """

    # 1. Draw graph
    timestamp = time.time()
    img_id = str(timestamp).split('.')[0]
    dot_graph = render_graph(img_id, program)

    # if "Unsupported Operator" in result['answer']:
    #     # if the final_answer is Unsupported Operator
    #     parsed_intermediate_result = None
    # else:
    # 4. Construct operator<->intermediate result pairs
    func_list, results_list = construct_func_result_pair(program, result)
    
    parsed_intermediate_result = ""
    parsed_intermediate_result += '\n\n<details open>\n'            # toggle fold/unfold
    parsed_intermediate_result += '<summary>Summary</summary>\n'

    # Table header
    parsed_intermediate_result += "<table class='center'>\n"
    parsed_intermediate_result += "<tr><th>Actions</th><th>Results</th></tr>\n"

    # Table rows
    for action, inter_result in zip(func_list, results_list):
        # Format None as "None" for consistency
        result_str = str(inter_result) if inter_result is not None else "None"
        parsed_intermediate_result += "<tr><td>{}</td><td>{}</td></tr>\n".format(action, result_str)

    # Close the HTML table
    parsed_intermediate_result += "</table>\n"

    # Close the <details> element
    parsed_intermediate_result += '</details>\n'

    # Add the CSS style block
    parsed_intermediate_result += '<style>'
    parsed_intermediate_result += '  .center { margin: auto; }'
    parsed_intermediate_result += '</style>'

    ######################## Add graph image in the chat interface ############################
    # filename = f"logs/graphs/graph_output_{img_id}.png"
    filename = os.path.join(LOGDIR, 'graphs', f"graph_output_{img_id}.png")
    enlarge_image(filename)
    assert os.path.exists(filename), f"{filename} does not exists"
    graph_html = f"\n<details open><summary>Fold/Unfold Image</summary><p align=\"center\"><img src='file={filename}' style='width: 100%; height: 100px; max-width:100%; max-height:100%'></img></p></details>" #html way
    # graph_md = f"\n![](/file={filename})" #markdown way

    return parsed_intermediate_result, graph_html

def pretty_conversation_llama2(messages, system_message=None, replace_token=False):
    
    ret = "\n"
    if system_message:
        ret = "\nSYSTEM: "
        ret += system_message + "\n\n"
        ret += "-"*70 + "\n\n"

    for i, (role, message) in enumerate(messages):
        if message:
            if i%2 == 0:
                if i == len(messages) - 1:
                    ret += "USER" + "\t\t: " + message + "\n"
                else:
                    ret += "USER" + "\t\t: " + message + "\n"
            else:
                # replace the long message with predicted chat mode
                if replace_token:
                    if '[casual]' in message:
                        message = '[casual]'
                    elif '[factual]' in message:
                        message = '[factual]'
                    elif '[contextual]' in message:
                        message = '[contextual]'
                    else:
                        message = message 
                if i == len(messages) - 1:
                    ret += "ASSISTANT" + "\t: " + message + "\n"
                else:
                    ret += "ASSISTANT" + "\t: " + message + "\n"
        else:
            ret += "ASSISTANT" + ":"
    return ret

def preprocess_messages(messages):
    """
    Replace [INST] with User, [/INST] with Assistant
    E.g.:
        Convert
        [['[INST]', 'Hi'], ['[/INST]', 'Hello how are you?']
        Into
        [['[User]', 'Hi'], ['[Assistant]', 'Hello how are you?']
    """

    for mes in messages:
        if mes[0] == '[INST]':
            mes[0] = 'User'
        elif mes[0] == '[/INST]':
            mes[0] = 'Assistant'
    return messages

def count_prompt_token(worker_addr, prompt):
    response = requests.post(
        worker_addr + "/count_token",
        # headers=headers,
        json={"prompt": prompt},
        # timeout=WORKER_API_TIMEOUT,
    )
    token_cnt = response.json()['count']
    return token_cnt

def extract_rewrite_tag(input_string):
    # Define a regular expression pattern to match content inside <rewrite> tags
    pattern = re.compile(r'<rewrite>(.*?)<\/rewrite>')

    # Try to find a match
    match = re.search(pattern, input_string)

    if match:
        # Extract content from the match
        content = match.group(1).strip()
        return content
    else:
        # If no match, remove any remaining <rewrite> or </rewrite> tags
        cleaned_string = re.sub(r'<rewrite>|<\/rewrite>', '', input_string).strip()
        print("WARNING: <rewrite> tag is incomplete.")
        return cleaned_string

def check_curly_bracket(json_string):
    """Ensure the input string has valid curly bracket pairs"""
    stack = []
    start_index = None
    end_index = None

    # Find the indexes of the first occurrence of '{' and the last occurrence of '}'
    for i, char in enumerate(json_string):
        if char == '{':
            stack.append(i)
        elif char == '}':
            if stack:
                start_index = stack.pop()
                end_index = i
            else:
                # Found '}' without matching '{', invalid JSON
                return json_string[start_index:end_index + 1]

    # Check if the JSON is surrounded by curly brackets and no extra brackets exist
    if start_index == 0 and end_index == len(json_string) - 1 and len(stack) == 0:
        valid_json = json_string[start_index:end_index + 1]
        return valid_json
    else:
        return json_string[start_index:end_index + 1]
    
def extract_and_load_json(input_str, target_keys):

    # Replace single quotes with double quotes, excluding those within string literals
    def replace_single_quotes(match):
        # If the match is inside double quotes, return it unchanged
        if match.group(1) is not None:
            return match.group(0)
        # Otherwise, replace single quotes with double quotes
        return '"' + match.group(2) + '"'
    
    def replace_escape_backlash(input_str):
        return input_str.replace("\\", "")

    # Regular expression pattern to match single quotes outside of string literals
    pattern = r'("(?:[^"\\]|\\.)*")|\'(.*?)\''

    # Use regular expression to replace single quotes with double quotes around keys and values
    # text_with_double_quotes = re.sub(r'([\'"])([^\'"]+)([\'"]) ?: ?([\'"])((?:(?!\4).)*)\4', lambda m: f'"{m.group(2)}": "{m.group(5)}"', input_str)
    text_with_double_quotes = re.sub(pattern, replace_single_quotes, input_str)
    text_with_double_quotes = check_curly_bracket(text_with_double_quotes)
    text_with_double_quotes = replace_escape_backlash(text_with_double_quotes)

    # Use regular expression to extract JSON content
    match = re.search(r'{.*}', text_with_double_quotes, re.DOTALL)
    
    if match:
        json_content = match.group()
        
        try:
            # Load the extracted JSON content
            # loaded_json = json.loads(json_content)
            loaded_json = sanitize_and_parse_json(json_content)

            # Assert that the keys "reasoning", "chat_mode", and "response" exist in the returned JSON
            for key in target_keys:
                assert key in loaded_json, f"Key {key} not found in JSON. Got: {loaded_json}"

            return loaded_json
        
        except json.JSONDecodeError as e:
            print("-"*30, f"Before extract json", "-"*30)
            print(json_content)
            print(f"WARNING: Error decoding JSON: {e}")
    else:
        print("-"*30, f"Before extract json", "-"*30)
        print(input_str)
        print("WARNING: No JSON content found in the input string.")
        return input_str

def model_worker_stream_iter(
    conv,
    model_name,
    worker_addr,
    prompt,
    temperature,
    repetition_penalty,
    top_p,
    max_new_tokens,
):
    # Make requests
    gen_params = {
        "model": model_name,
        "prompt": prompt,
        "temperature": temperature,
        "repetition_penalty": repetition_penalty,
        "top_p": top_p,
        "max_new_tokens": max_new_tokens,
        "stop": conv.stop_str,
        "stop_token_ids": conv.stop_token_ids,
        "echo": False,
    }
    # logger.info(f"==== request ====\n{gen_params}")

    # Stream output
    response = requests.post(
        worker_addr + "/worker_generate_stream",
        headers={"User-Agent": "FastChat Client"},
        json=gen_params,
        stream=True,
        timeout=WORKER_API_TIMEOUT,
    )
    for chunk in response.iter_lines(decode_unicode=False, delimiter=b"\0"):
        if chunk:
            data = json.loads(chunk.decode())
            yield data

def get_response(conv, model_name, worker_addr, prompt, config):
    # Prompt model to decide action
    stream_iter = model_worker_stream_iter(
        conv,
        model_name,
        worker_addr,
        prompt,
        config['temperature'],
        config['repetition_penalty'],
        config['top_p'],
        config['max_new_tokens'],
    )

    for i, data in enumerate(stream_iter):
        output = data["text"].strip()
        if "<s>" in output: # avoid LLM go crazy
            break
        output = data["text"].split("<s>")[0].strip()

    return output

def post_process_code(code):
    sep = "\n```"
    if sep in code:
        blocks = code.split(sep)
        if len(blocks) % 2 == 1:
            for i in range(1, len(blocks), 2):
                blocks[i] = blocks[i].replace("\\_", "_")
        code = sep.join(blocks)
    return code

def iter_gen(generator):
    """
    Iterate the generator and do nothing
    """
    for x in generator:
        pass

if __name__ == '__main__':
    question = "Where is Tsinghua University?"

    program = semantic_parsing_api(question)
    print(program)

    # # Test if missing arguments in function that requires arguments can throw warning
    # for p in program:
    #     if p['func'] == 'What':
    #         p['func'] = 'QueryName'
    # program = program_is_valid(program)

    # print("PROGRAM SENDING INTO ENGINE")
    # for prog in program:
    #     print(prog)

    # print("-" * 60)
    # result = kopl_engine_exec_api(program)
    # # answer = result['answer']

    # # print("ANSWER FROM ENGINE: ", answer)

    # # for res in result['inner_content']:
    # #     print(res)
    # print(result['inner_content'][-1])
    # print((', ').join(result['inner_content'][-1]['content']))