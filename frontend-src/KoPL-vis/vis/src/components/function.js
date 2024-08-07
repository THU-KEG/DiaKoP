export const FuncConfig = {
  And: {
    funcName: 'And',
    args: [],
    inTypes: ['Tuple', 'Tuple'],
    outTypes: 'Tuple',
  },
  Count: {
    funcName: 'Count',
    args: [],
    inTypes: ['Tuple', 'None'],
    outTypes: 'Int',
  },
  FilterConcept: {
    funcName: 'FilterConcept',
    args: [
      {name: 'Concept',}
    ],
    inTypes: ['Tuple', 'None'],
    outTypes: 'Tuple',
  },
  FilterDate: {
    funcName: 'FilterDate',
    args: [
      {name: 'Attribute', type: 'Date'},
      {name: 'AttributeValue', type: 'Date'},
      {name: 'Operator', type: 'Filter'}
    ],
    inTypes: ['Tuple', 'None'],
    outTypes: 'Tuple',
  },
  FilterNum: {
    funcName: 'FilterNum',
    args: [
      {name: 'Attribute', type: 'Num'},
      {name: 'AttributeValue', type: 'Num'},
      {name: 'Operator', type: 'Filter'}
    ],
    inTypes: ['Tuple', 'None'],
    outTypes: 'Tuple',
  },
  FilterStr: {
    funcName: 'FilterStr',
    args: [
      {name: 'Attribute', type: 'Str'},
      {name: 'AttributeValue', type: 'Str'},
    ],
    inTypes: ['Tuple', 'None'],
    outTypes: 'Tuple',
  },
  FilterYear: {
    funcName: 'FilterYear',
    args: [
      {name: 'Attribute', type: 'Year'},
      {name: 'AttributeValue', type: 'Year'},
      {name: 'Operator', type: 'Filter'}
    ],
    inTypes: ['Tuple', 'None'],
    outTypes: 'Tuple',
  },
  Find: {
    funcName: 'Find',
    args: [
      {name: 'Entity',}
    ],
    inTypes: ['None', 'None'],
    outTypes: 'Tuple',
  },
  FindAll: {
    funcName: 'FindAll',
    args: [],
    inTypes: ['None', 'None'],
    outTypes: 'Tuple',
  },
  // FindLinking: {
  //   funcName: 'FindLinking',
  //   args: [
  //     {name: 'Entity',}
  //   ],
  //   inTypes: ['None', 'None'],
  //   outTypes: 'Tuple',
  // },
  Or: {
    funcName: 'Or',
    args: [],
    inTypes: ['Tuple', 'Tuple'],
    outTypes: 'Tuple',
  },
  QFilterDate: {
    funcName: 'QFilterDate',
    args: [
      {name: 'Qualifier', type: 'Date'},
      {name: 'QualifierValue', type: 'Date'},
      {name: 'Operator', type: 'Filter'}
    ],
    inTypes: ['Tuple', 'None'],
    outTypes: 'Tuple',
  },
  QFilterNum: {
    funcName: 'QFilterNum',
    args: [
      {name: 'Qualifier', type: 'Num'},
      {name: 'QualifierValue', type: 'Num'},
      {name: 'Operator', type: 'Filter'}
    ],
    inTypes: ['Tuple', 'None'],
    outTypes: 'Tuple',
  },
  QFilterStr: {
    funcName: 'QFilterStr',
    args: [
      {name: 'Qualifier', type: 'Str'},
      {name: 'QualifierValue', type: 'Str'},
    ],
    inTypes: ['Tuple', 'None'],
    outTypes: 'Tuple',
  },
  QFilterYear: {
    funcName: 'QFilterYear',
    args: [
      {name: 'Qualifier', type: 'Year'},
      {name: 'QualifierValue', type: 'Year'},
      {name: 'Operator', type: 'Filter'}
    ],
    inTypes: ['Tuple', 'None'],
    outTypes: 'Tuple',
  },
  QueryAttr: {
    funcName: 'QueryAttr',
    args: [
      {name: 'Attribute', type: 'Any'},
    ],
    inTypes: ['Tuple', 'None'],
    outTypes: 'ValueClassList',
  },
  QueryAttrQualifier: {
    funcName: 'QueryAttrQualifier',
    args: [
      {name: 'Attribute', type: 'Any'},
      {name: 'AttributeValue', type: 'Any'},
      {name: 'Qualifier', type: 'Any'}
    ],
    inTypes: ['Tuple', 'None'],
    outTypes: 'ValueClassList',
  },
  QueryAttrUnderCondition: {
    funcName: 'QueryAttrUnderCondition',
    args: [
      {name: 'Attribute', type: 'Any'},
      {name: 'Qualifier', type: 'Any'},
      {name: 'QualifierValue', type: 'Any'},
    ],
    inTypes: ['Tuple', 'None'],
    outTypes: 'ValueClassList',
  },
  QueryName: {
    funcName: 'QueryName',
    args: [],
    inTypes: ['Tuple', 'None'],
    outTypes: 'EntityStrList',
  },
  QueryRelation: {
    funcName: 'QueryRelation',
    args: [],
    inTypes: ['Tuple', 'Tuple'],
    outTypes: 'RelationStrList',
  },
  QueryRelationQualifier: {
    funcName: 'QueryRelationQualifier',
    args: [
      {name: 'Relation',},
      {name: 'Qualifier', type: 'Any'},
    ],
    inTypes: ['Tuple', 'Tuple'],
    outTypes: 'ValueStrList',
  },
  Relate: {
    funcName: 'Relate',
    args: [
      {name: 'Relation',},
      {name: 'Direction',},
    ],
    inTypes: ['Tuple', 'None'],
    outTypes: 'Tuple',
  },
  SelectAmong: {
    funcName: 'SelectAmong',
    args: [
      {name: 'Attribute', type: 'Num'},
      {name: 'Operator', type: 'MaxMin'},
    ],
    inTypes: ['Tuple', 'None'],
    outTypes: 'EntityStrList',
  },
  SelectBetween: {
    funcName: 'SelectBetween',
    args: [
      {name: 'Attribute', type: 'Num'},
      {name: 'Operator', type: 'LessGreater'},
    ],
    inTypes: ['Tuple', 'Tuple'],
    outTypes: 'EntityStrList',
  },
  VerifyDate: {
    funcName: 'VerifyDate',
    args: [
      {name: 'TargetDate', type: 'Date'},
      {name: 'Operator', type: 'Filter'},
    ],
    inTypes: ['ValueClassList', 'None'],
    outTypes: 'BoolStr',
  },
  VerifyNum: {
    funcName: 'VerifyNum',
    args: [
      {name: 'TargetNum', type: 'Num'},
      {name: 'Operator', type: 'Filter'},
    ],
    inTypes: ['ValueClassList', 'None'],
    outTypes: 'BoolStr',
  },
  VerifyStr: {
    funcName: 'VerifyStr',
    args: [
      {name: 'TargetStr', type: 'Str'},
    ],
    inTypes: ['ValueClassList', 'None'],
    outTypes: 'BoolStr',
  },
  VerifyYear: {
    funcName: 'VerifyYear',
    args: [
      {name: 'TargetYear', type: 'Year'},
      {name: 'Operator', type: 'Filter'},
    ],
    inTypes: ['ValueClassList', 'None'],
    outTypes: 'BoolStr',
  },
  What: {
    funcName: 'QueryName',
    args: [],
    inTypes: ['Tuple', 'None'],
    outTypes: 'EntityStrList',
  },
};