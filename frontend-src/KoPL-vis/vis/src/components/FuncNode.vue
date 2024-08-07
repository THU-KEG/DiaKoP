<template>
<a-layout style="margin: 10px">
  <a-layout-header class="func-label">
    <div>
      {{ this.funcName }}
      <!-- <button @click="this.logInputs">debug</button> -->
    </div>
  </a-layout-header>
  <a-layout-content>
    <component v-for="arg, id in this.args" :is="this.whichInputType(arg.name)" :key="id"
      :config="{name: arg.name, type: arg.type, kb: this.whichKB}"
      :argvalue="this.inputs[id]"
      @edited="(v, e) => this.onFunctionEdited(id, v)"
      />
      <a-button type="text" 
        style="margin-top: 5px; font-size: small;"
        @click="this.onClickCheck"
        :disabled="this.innerContentDisabled"
        >check intermediate result</a-button>
  </a-layout-content>
</a-layout>
<template v-if="this.data?.inTypes[0] != 'None'">
  <Handle v-if="this.data?.inTypes[1] == 'None'"
    type="target" :id="`${this.nodeID}-il`"
    :position="Position.Left"
    :is-valid-connection="this.validSrcInLeft"
    style="font-size: 20px;"
  > &gt; </Handle>
  <template v-else>
    <Handle
      type="target" :id="`${this.nodeID}-il`"
      :position="Position.Top"
      :is-valid-connection="this.validSrcInLeft"
    > &or; </Handle>
    <Handle
      type="target" :id="`${this.nodeID}-ir`"
      :position="Position.Bottom"
      :is-valid-connection="this.validSrcInRight"
    > &and; </Handle>
  </template>
</template>
<Handle
  type="source" :id="`${this.nodeID}-o`"
  :position="Position.Right"
  :is-valid-connection="this.validTgt"
> O </Handle>
</template>

<script>
import { ref } from 'vue';
import EntityInput from './EntityInput.vue';
import AttributeInput from './AttributeInput.vue';
import ConceptInput from './ConceptInput.vue';
import RelationInput from './RelationInput.vue';
import QualifierInput from './QualifierInput.vue';
import ValueInput from './ValueInput.vue';
import { Handle, Position, useVueFlow} from '@braks/vue-flow';
import bus from './bus';

export default {
  name: 'FuncNode',
  components: {
    EntityInput,
    AttributeInput,
    RelationInput,
    ConceptInput,
    QualifierInput,
    ValueInput,
    Handle,
  },
  props: {
    data: Object,
  },
  setup() {
    const funcName = ref('');
    const args = ref([]);
    const inputs = ref([]);

    // may not be used
    const leftIn = ref('');
    const rightIn = ref('');
    const outgo = ref('');
    const nodeID = ref('');

    const whichInputType = (name) => {
      if (name == 'Concept'
        || name == 'Entity'
        || name == 'Relation'
        || name == 'Attribute'
        || name == 'Qualifier') {
        return `${name}Input`;
      }
      return 'ValueInput';
    };

    const {getNode, edges, } = useVueFlow();
    
    const validSrcInLeft = (conn) => {
      // first, check if the handle is already connected
      for (var eid in edges.value){
        const e = edges.value[eid];
        if (e.targetHandle === conn.targetHandle
          || e.sourceHandle === conn.sourceHandle) {
          return false;
        }
      }

      const src = getNode.value(conn.source);
      return src.data.outTypes === leftIn.value;
    };

    const validSrcInRight = (conn) => {
       // first, check if the handle is already connected
      for (var eid in edges.value){
        const e = edges.value[eid];
        if (e.targetHandle === conn.targetHandle
          || e.sourceHandle === conn.sourceHandle) {
          return false;
        }
      }

      const src = getNode.value(conn.source); // the target means the other end here
      return src.data.outTypes === rightIn.value;
    };

    const validTgt = (conn) => {
      // first, check if the handle is already connected
      for (var eid in edges.value){
        const e = edges.value[eid];
        console.log(e);
        if (e.targetHandle === conn.targetHandle
          || e.sourceHandle === conn.sourceHandle) {
          return false;
        }
      }

      const tgt = getNode.value(conn.target);
      const tgtHdl = conn.targetHandle; // the target means the other end here
      if (tgtHdl.indexOf('-il') !== -1) {
        return outgo.value === tgt.data.inTypes[0];
      }
      if (tgtHdl.indexOf('-ir') !== -1) {
        return outgo.value === tgt.data.inTypes[1];
      }
      return false;
    };

    const innerContentIndex = ref(Number);
    const innerContentDisabled = ref(true);
    bus.on('GetInnerContent', e => {
      innerContentIndex.value = e.idtoindex[nodeID.value];
      innerContentDisabled.value = false;
    });

    const onClickCheck = () => {
      bus.emit('ShowInnerContent', innerContentIndex.value);
    };
    
    return {
      funcName,
      args,
      inputs,
      leftIn,
      rightIn,
      outgo,
      whichInputType,
      nodeID,
      Position,
      validSrcInLeft,
      validSrcInRight,
      validTgt,
      innerContentDisabled,
      onClickCheck,
    }
  },
  mounted: function () {
    this.funcName = this.data?.funcName;
    this.data?.args.forEach(arg => {
      this.args.push(arg);
    });
    this.inputs = this.data?.inputs;
    this.nodeID = this.data?.id;
    this.leftIn = this.data?.inTypes[0];
    this.rightIn = this.data?.inTypes[1];
    this.outgo = this.data?.outTypes;
  },
  computed: {
    whichKB() {
      return this.data?.kb;
    },
  },
  methods: {
    logInputs() {
      console.log(this.inputs)
    },
    onFunctionEdited(id, v) {
      this.inputs[id] = v;
      console.log(this.inputs);
      bus.emit('FunctionChange', { id : this.nodeID, inputs: this.inputs});
    },
  }
};

</script>

<style scoped>

.func-label {
  font-weight: 700;
  font-size: 20px;
}

.vue-flow__handle {
  height: unset;
  width: unset;
  color: #528B8B;
  background-color: transparent;
  border-color: transparent;
  font-weight: bold;
}

</style>
