<template>
<div @drop="this.onDrop">
  <aside>
    <div class="nodes" style="float: left;">
      <div class="vue-flow__node-default" :draggable="this.selectedFunc.length != 0" 
        @dragstart="this.onDragStart($event)"
        style="width: 200px;">
        <a-select
          :style="{
            width:'100%',
            height: '40px',
          }"
          v-model="this.selectedFunc"
          placeholder="select a function">
          <a-option v-for="(item, idx) in this.allFunctions" 
            :key="idx" 
            :value="item">
            {{ item }}
          </a-option>          
        </a-select>
      </div>
    </div>
    <div class="controls" style="float: left; display: flex;
      text-align: center; margin: 10px 0;">
      <button style="float: left; color: black; width: 40px; margin-right: 2%;"
        @click="this.onClickAdd" >
        <IconPlus :size="24"/>
      </button>
      <button style="background-color: #6495ED; float: left; width: 155px;"
        @click="this.onClickClear" >
        <IconEraser style="margin: auto 10% auto 5%;" />
        <span style="margin: auto auto auto 5%;">Clear All</span>
      </button>
    </div>
    <div class="controls" style="margin: 10px 7px 10px 0px; float: right;">
      <button style="background-color: #B0C4DE; color: black; float: right; width: 90px;"
        @click="this.onClickCode" >
        <IconFile :size="25" />
        <span style="margin: auto auto auto 2px;"> Code </span>
      </button>
      <button style="background-color: #6f3381; float: right; margin: auto 5px auto 0; width: 90px;"
        id="run-button"
        @click="this.onClickRun" >
        <IconCaretRight :size="25" />
        <span style="margin: auto auto auto 2px;"> Run </span>
      </button>
    </div>
    <div style="text-align: center; margin: 10px 10px 10px 7px; width: 160px; float: right;">
      <a-select
        :style="{
          width:'100%',
          height: '40px',
          display: 'flex',
        }"
        v-model="this.whichKB"
        @change="this.onChangeKB">
        <a-option :value="'small'">Run on KQA pro KB</a-option>
        <a-option :value="'large'">Run on Wikidata</a-option>
      </a-select>
    </div>
    <div class="chooseNumResults" style="text-align: center; margin: 10px 0px 10px 10px; float: right; ">
      <div id="chooseNumBackground" style="display: flex; align-items: center; background-color: #e3d5ef; color: black; float: right; height: 40px; width: 170px; border-radius: 2px;" >
        <span style="margin: auto 5px auto auto;">Show</span>
        <input class="res-num-input"
              type="text"
              placeholder=10
              v-model="this.numResults"
              style="width: 40px" />
        <span style="margin: auto auto auto 5px;">Results</span>
      </div>
    </div>
  </aside>
  <VueFlow 
    class="basicflow" :default-zoom="1.0" :min-zoom="0.2" :max-zoom="4"
    ref="wrapper"
    style="height: 600px;"
    @dragover="this.onDragOver">
    <Background pattern-color="#aaa" gap="8" />
    <MiniMap />
    <Controls />

    <template #node-custom="props">
      <FuncNode :data="props.data" />
    </template>

  </VueFlow>
</div>
</template>

<script>

// imports for gradio
import { ref, onMounted } from 'vue';  // deleted onMounted, just use mounted

import {
  Background,
  Controls,
  MiniMap,
  VueFlow,
  useVueFlow,
} from '@braks/vue-flow'
// import { ref } from 'vue';
import bus from './bus';
import FuncNode from './FuncNode.vue';
import { FuncConfig } from './function';
import { DagreLayout} from '@antv/layout';
import {
  IconPlus,
  IconEraser,
  IconCaretRight,
  IconFile,
} from '@arco-design/web-vue/es/icon';
// import { Message } from 'element-ui';

export default {
  name: 'ProgramVisBoard',
  components: {
    Background,
    Controls,
    MiniMap,
    VueFlow,
    FuncNode,
    IconPlus,
    IconEraser,
    IconCaretRight,
    IconFile,
  },
  setup() {

    var nodeID = 0;

    const getNodeID = () => {
      var ret =  `${nodeID}`;
      nodeID += 1;
      return ret;
    };

    const onDragStart = (event) => {
      if (event.dataTransfer) {
        event.dataTransfer.effectAllowed = 'move';
      }
    };

    const { 
      onConnect, nodes, edges, addEdges, addNodes, getNode,
      removeNodes, project,
    } = useVueFlow();

    const onDragOver = (event) => {
      event.preventDefault();
      if (event.dataTransfer) {
        event.dataTransfer.dropEffect = 'move';
      }
    };

    onConnect((params) => {
      console.log(params);
      addEdges([{
        ...params,
        id: `${params.source}-${params.target}`,
        style: { stroke: '#00F5FF', strokeWidth: 2,},
        markerEnd: 'arrowclosed',
      }]);
    });

    const wrapper = ref();
    const onDrop = (event) => {
      const _ = require('lodash')
      const funcdata = _.cloneDeep(FuncConfig[selectedFunc.value]);
      const nodeID = getNodeID();
      var inputs = [];
      while (inputs.length < funcdata.args.length) {
        inputs.push('');
      }
      // const nodeSize = {
      //   width: funcdata.args.length ===  0 ? 300 : 320,
      //   height: funcdata.args.length * 60
      // };
      console.log(event.clientX);
      console.log(event.clientY);
      console.log(wrapper);
      const flowbounds = wrapper.value.$el.getBoundingClientRect()
      const position = project({ 
        x: event.clientX - flowbounds.left, 
        y: event.clientY - flowbounds.top,
      });
      const newNode = {
        id: nodeID,
        type: 'custom',
        data: {...funcdata, inputs, kb: whichKB.value, id: nodeID},
        position,
      };
      addNodes([newNode]);
    };

    const onClickAdd = () => {
      if (selectedFunc.value.length === 0) {
        return;
      }
      const _ = require('lodash')
      const funcdata = _.cloneDeep(FuncConfig[selectedFunc.value]);
      const nodeID = getNodeID();
      var inputs = [];
      while (inputs.length < funcdata.args.length) {
        inputs.push('');
      }

      const flowbounds = wrapper.value.$el.getBoundingClientRect();
      const position = project({ 
        x: 400 - flowbounds.left, 
        y: 400 - flowbounds.top,
      });
      const newNode = {
        id: nodeID,
        type: 'custom',
        data: {...funcdata, inputs, kb: whichKB.value, id: nodeID},
        position,
      };
      addNodes([newNode]);
    };

    const prog = ref([]);
    const numResults = ref(10); // 中间结果展示条目，默认展示10个

    const validFlowChart = () => {
      if (nodes.value.length === 0) {
        bus.emit('WrongFlowChart', 'Empty diagram');
        return false;
      }
      // check the flow-chart is a tree

      // first, check if number_of_edges === number_of_nodes - 1
      if (nodes.value.length - 1 != edges.value.length) {
        bus.emit('WrongFlowChart', 'There are isolated nodes');
        return false;
      }

      // second, check if there are empty args
      for (var vid in nodes.value) {
        console.log(vid);
        const v = getNode.value(vid);
        if (!v) continue;
        for (var arg in v.data.inputs) {
          console.log(v.data.inputs[arg]);
          if (v.data.inputs[arg].length === 0) {
            bus.emit('WrongFlowChart', `Missing parameters in ${v.data.funcName} function`);
            return false;
          }
        }
      }

      // third, check if there is one output node
      const isOutputCandidate = (v) => {
        console.log(v);
        return v === 'Count' || 
          v === 'QueryAttr' ||
          v === 'QueryName' ||
          v === 'QueryNeighbor' ||
          v === 'VerifyStr' ||
          v === 'VerifyNum' ||
          v === 'VerifyYear' ||
          v === 'VerifyDate' ||
          v === 'QueryAttrQualifier' || 
          v ==='QueryRelationQualifier' ||
          // v === 'What' ||
          v === "QueryRelation"|| 
          v === "SelectBetween" ||
          v === "SelectAmong" ||
          v === "QueryAttrUnderCondition";
      };
      var candidates = [];
      var asSrc = [];
      nodes.value.forEach(v => {
        if (isOutputCandidate(getNode.value(v.id).data.funcName)) {
          candidates.push(v.id);
        }
      });
      edges.value.forEach(e => {
        if (isOutputCandidate(getNode.value(e.target).data.funcName)) {
          asSrc.push(e.target);
        }
      });
      if (candidates.length === 0) {
        bus.emit('WrongFlowChart', 'Missing output functions');
        return false;
      }
      if (candidates.length - asSrc.length > 1) {
        bus.emit('WrongFlowChart', 'More than one output functions as the output of the program');
        return false;
      }

      // forth, check if all input handles are connected
      var connInputNum = {};
      nodes.value.forEach(v => { connInputNum[v.id] = 0; });
      edges.value.forEach(e => {
        connInputNum[e.target] += 1;
      });

      for (var nid in nodes.value) {
        const v = getNode.value(nid);
        if (!v) continue;
        var inputNum = 0;
        if (v.data.inTypes[0] != 'None') {
          inputNum = 1;
          if (v.data.inTypes[1] != 'None') {
            inputNum = 2;
          }
        }
        if (connInputNum[v.id] != inputNum) {
          console.log(connInputNum[v.id]);
          bus.emit('WrongFlowChart', `Missing input connections to ${v.data.funcName} function`);
          return false;
        }
      }

      // fifth, check if all input values is of correct type
      for (var v of nodes.value) {
        console.log('fifth');
        for (var arg_id in v.data.args) {
          const arg = v.data.args[arg_id];
          if (arg.name === 'AttributeValue' || arg.name === 'QualifierValue') {
            console.log(arg.name, arg.type);
            if (arg.type === 'Date') {
              console.log('check date ', v.data.inputs[arg_id]);
              const regex = /^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$/;
              if (!regex.test(v.data.inputs[arg_id])) {
                bus.emit('WrongFlowChart', `Wrong format of Date type in ${v.data.funcName}`);
                return false;
              }
            }
            else if (arg.type === 'Num') {
              console.log('check num ', v.data.inputs[arg_id]);
              console.log(v.data.inputs[arg_id]);
              const regex_int = /^[+-]?[0-9]*$/;
              const regex_flt = /^-?[0-9]\d*\.\d*|-0\.\d*[1-9]\d*( [A-Za-z]+( [A-Za-z]+)*)$/;
              if (!(
                  regex_int.test(v.data.inputs[arg_id])
                  || regex_flt.test(v.data.inputs[arg_id]))) {
                bus.emit('WrongFlowChart', `Wrong format of Num type in ${v.data.funcName}`);
                return false;
              }
            }
            else if (arg.type === 'Str') {
              console.log('check str ', v.data.inputs[arg_id]);
              const regex = /^[\S]+( [\S]+)*$/;
              if (!regex.test(v.data.inputs[arg_id])) {
                bus.emit('WrongFlowChart', `Wrong format of String type in ${v.data.funcName}`);
                return false;
              }
            }
            else if (arg.type == 'Year') {
              console.log('check year ', v.data.inputs[arg_id]);
              const regex = /^-?[1-9]\d*$/;
              if (!regex.test(v.data.inputs[arg_id])) {
                bus.emit('WrongFlowChart', `Wrong format of Year type in ${v.data.funcName}`);
                return false;
              }
            }
          }
        }
      }

      return true;
    };

    bus.on('FunctionChange', func => {
      var updatedNode = getNode.value(func.id);
      updatedNode.data.inputs = func.inputs;
    });

    // bus.on('ClickRun', extraInfo => {
    //  return;
    // });

    const allFunctions = [
      'Find', 'FindAll', 'FilterConcept', 'FilterStr', 'FilterNum', 'FilterYear',
      'FilterDate','QFilterStr', 'QFilterNum', 'QFilterYear', 'QFilterDate', 'Relate', 'And', 'Or',
      'Count', 'QueryName', 'QueryAttr', 'QueryAttrUnderCondition', 'QueryRelation', 'SelectBetween',
      'SelectAmong', 'VerifyStr', 'VerifyNum', 'VerifyYear', 'VerifyDate', 'QueryAttrQualifier',
      'QueryRelationQualifier',
    ];

    const selectedFunc = ref('');

    const whichKB = ref('large');

    const onClickClear = () => {
      removeNodes(nodes.value);
      bus.emit('ClickClear');
    };

    bus.on('clickSendKoPLProgramAndClose', () => {  // gradio -- main execution logic for onClickSendKoPLProgramAndClose
      console.log('2 Inside clickSendKoPLProgramAndClose');

      // logic adapted from method "clickRun"

      if (!validFlowChart()) {
        return;
      }

      // compile the flow-char  // original function adapted to gradio's sendKoPLProgramAndClose
      var tgt_prog = [];

      // first, find the output node
      // the output node is the only node that is not the source of another
      var isSrc = {};
      // initialize isSrc: each node is not the source of another
      nodes.value.forEach(v => {
        isSrc[v.id] = false;
      });

      // now check the edges to get dependences and find the output node
      var depMapping = {}; // map node ids to corresponding source node ids
      edges.value.forEach(e => {
        isSrc[e.source] = true;
        if (!( e.target in depMapping )) {
          depMapping[e.target] = ['-1', '-1'];
        }
        if (e.targetHandle.indexOf('-il') != -1) {
          depMapping[e.target][0] = e.source;
        } else if (e.targetHandle.indexOf('-ir') != -1) {
          depMapping[e.target][1] = e.source;
        }
      });

      // at the moment the output node is indicated by isSrc
      var outputNode = '';
      for (var v in isSrc) {
        if (!isSrc[v]) {
          outputNode = v;
          break;
        }
      }

      // add the output node and its ancestors of the output node recurently
      // Array::push is used, so the order is reversed
      function addFuncs(tgt) {
        const v = getNode.value(tgt);
        tgt_prog.push({ id: v.id, function: v.data.funcName, inputs: v.data.inputs, });
        // because the order of tgt_prog will be reversed later,
        // first add right src node and then left src node
        if (tgt in depMapping) {
          if (depMapping[tgt][1] != '-1') {
            addFuncs(depMapping[tgt][1]);
          }
          if (depMapping[tgt][0] != '-1') {
            addFuncs(depMapping[tgt][0]);
          }
        }
      }
      addFuncs(outputNode);

      // now reverse the tgt_prog
      tgt_prog.reverse();
      // and record the index of each node in the array
      var ID2Index = {};
      for (var i = 0; i < tgt_prog.length; ++i) {
        ID2Index[tgt_prog[i].id] = i;
      }

      // now we can resolve the dependencies
      tgt_prog.forEach(f => {
        f.dependencies = [-1, -1];
        if (f.id in depMapping) {
          const leftSrc = depMapping[f.id][0];
          if (leftSrc != '-1') {
            f.dependencies[0] = ID2Index[leftSrc];
            const rightSrc = depMapping[f.id][1];
            if (rightSrc != '-1') {
              f.dependencies[1] = ID2Index[rightSrc];
            }
          }
        }
      });

      // finally, id is undefined when post program to backend
      tgt_prog.forEach(f => {
        delete f.id;
      });

      // update the program
      prog.value = tgt_prog;

      bus.emit('ObtainNewestKoPLProgramFromBoard', prog.value);  // implemented in App.vue

    });

    // listen for gradio's transferred program
    onMounted(() => {  // same as mounted() in vue 3
      console.log('ProgramVisBoard.vue: Component is mounted to the DOM');

      const prog = ref([]);

      bus.on('VisualizeProgram', (program) => {
        // process the program and generate visualization, similar to the logic of clickParse
        // Example: Assuming you have a method to convert the program to nodes and edges

        console.log("program:", program)

        prog.value = []

        program.forEach(element => {
          // let item = {"function": element["func"], "inputs": element["inputs"], "dependencies": element["dep"]};  // original with bug, adjust depending on specific attribute name
          let item = {"function": element["function"], "inputs": element["inputs"], "dependencies": element["dependencies"]};  // modified for gradio test
          prog.value.push(item);
        });

        console.log("program.forEach done")

        var newNodes = []; // new nodes to add
        var newEdges = []; // new edges to add
        
        var nodeIDList = []; // nodeIDs in the same order of the corresponding functions in the program

        var ID2Funcdata = []; // mapping from a node id to the corresponding funcdata

        var xnodes = []; // node objects fed to x6-layout to calculate positions of each node
        var xedges = []; // similar to xnodes above

        // first, get all node and edge objects according to functions of the program
        prog.value.forEach(func => {
          const _ = require('lodash')
          var funcdata = _.cloneDeep(FuncConfig[func.function]); 

          if ('inputs' in func) { 
            if (func.inputs.length == 0) {
              funcdata.inputs = [];
            }
            else {
              funcdata.inputs = func.inputs;
            }
          } else {
            funcdata.inputs = [];
          }

          // here record the order of node ids and the mapping from node id to node data
          const curID = getNodeID();
          nodeIDList.push(curID);
          ID2Funcdata[curID] = funcdata;

          const nodeSize = {
            width: (funcdata.inputs.length === 0 ? 300 : 320) + 20,
            height: (funcdata.inputs.length * 60 + 40) + 50
          };
          xnodes.push({ id: curID, size: nodeSize, });

          // now add edges
          const i = Number(func.dependencies[0]);
          if (i === -1) {
            return;
          }
          const depLeftID = nodeIDList[i];
          const eidLfet = depLeftID + '-' + curID;
          newEdges.push({
            id: eidLfet, 
            source: depLeftID, target: curID, 
            sourceHandle: depLeftID + '-o', targetHandle: curID + '-il',
            style: { stroke: '#00F5FF', strokeWidth: 2,}, 
            markerEnd: 'arrowclosed',
          });
          xedges.push({
            source: depLeftID, target: curID,
          });

          const j = Number(func.dependencies[1]);
          if (j === -1) {
            return;
          }
          const depRightID = nodeIDList[j];
          const eidRight = depRightID + '-' + curID;
          newEdges.push({
            id: eidRight, 
            source: depRightID, target: curID, 
            sourceHandle: depRightID + '-o', targetHandle: curID + '-ir',
            style: { stroke: '#00F5FF', strokeWidth: 2,}, 
            markerEnd: 'arrowclosed',
          });
          xedges.push({
            source: depRightID, target: curID,
          });
        });

        console.log("edges adding done")
        console.log("xnodes:", xnodes)
        console.log("xedges:", xedges)

        // calculate layout by dagre
        const dagreLayout = new DagreLayout({
          type: 'dagre',
          rankdir: 'LR',
          ranksep: 50,
          nodesep: 50,
          controlPoints: true,
        });
        const layoutData = dagreLayout.layout({nodes: xnodes, edges: xedges})
        // get positions of nodes
        const flowbounds = wrapper.value.$el.getBoundingClientRect();
        layoutData.nodes.forEach(v => {
          const pos = {
            x: v.x - v.size.width / 2 + flowbounds.left,
            y: v.y - v.size.height / 2,
          };
          newNodes.push({
            id: v.id, type: 'custom', 
            data: {...ID2Funcdata[v.id], id: v.id, kb: whichKB.value}, 
            position: pos
          });
        });

        console.log("calculate layout done")

        addNodes(newNodes);
        addEdges(newEdges);

        console.log("parse over")

        // tell App that Parse is over
        bus.emit('ParseOver', prog.value);

      });
    });

    return {
      onDragStart,
      getNodeID,
      onConnect,
      nodes,
      edges,
      addEdges,
      addNodes,
      onDragOver,
      onDrop,
      onClickAdd,
      allFunctions,
      selectedFunc,
      whichKB,
      prog,
      wrapper,
      onClickClear,
      numResults
    }
  },
  mounted() {
    
    
  },
  methods: {
    onClickRun() {
      // 处理numResults
      if (typeof this.numResults !== 'number') {
        this.numResults = parseInt(this.numResults); // String转int，如果传递非数字则变NaN
      }
      if (isNaN(this.numResults) || this.numResults <= 0 || this.numResults > 200) {
        this.$message.info('For the "Show [x] Results" option , please enter an integer between 1 and 200');
        console.log("Invalid Number")
        return;
      }
      bus.emit('PaneClickRun');
      console.log("Show " + this.numResults + " Results");
    },
    onChangeKB() {
      bus.emit('ChangeKB', this.whichKB);
    },
    onClickCode() {
      bus.emit('ClickCode');
    },
  },
};

</script>

<style>
@import '@braks/vue-flow/dist/style.css';
@import '@braks/vue-flow/dist/theme-default.css';

.vue-flow__minimap {
  transform: scale(75%);
  transform-origin: bottom right;
}

.basicflow .vue-flow__node-custom{
  border:1px solid #777;
  padding:10px 10px 0 10px;
  border-radius:10px;
  background:#ffffff;
  display:flex;
  flex-direction:column;
  justify-content:space-between;
  align-items:center;
  gap:10px;
  min-width: 300px;
}

aside{
  color:#fff;
  height: 60px;
  text-align: center;
  font-weight:700;
  border-right:1px solid #eee;
  padding:5px 5px;
  background:rgba(16, 176, 185, 0.75);
  box-shadow:0 5px 10px #0000004d;
}

aside .nodes>*{
  margin:auto 10px;
  cursor:-webkit-grab;
  cursor:grab;
  font-weight:500;
  font-size: 18px;
  box-shadow:5px 5px 10px 2px #00000040
}

.controls button{
  padding: 5px;
  border-radius: 5px;
  font-size: large;
  font-weight: 500;
  box-shadow:0 5px 10px #0000004d;
  cursor:pointer;
  color: white
}

.controls button:hover{
  opacity:.8;
  transform:scale(105%);
  transition:.25s all ease
}

.res-num-input {
  height: 17px;
  font-size: 15px;
  text-align: center;
  border-color: #3e3e3e;
  border-width: 1.5px;
  border-radius: 3px;
}

.res-num-input:focus {
  border-color: #3e3e3e;
}

</style>
