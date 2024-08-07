<template>
<div style="text-align: left;">
  <div>{{ this.label }}:</div>
  <template
    v-if="this.type === 'Filter' ||
      this.type === 'MaxMin' ||
      this.type === 'LessGreater' ||
      this.label === 'Direction'">
    <a-select
      :style="{
        width:'320px',
        height: '40px',
        margin: '2px 0',
      }"
      v-model="this.localArgValue"
      @change="this.onInput">
      <template v-if="this.type === 'Filter'">
        <a-option :value="'='">=</a-option>
        <a-option :value="'!='">!=</a-option>
        <a-option :value="'<'">&lt;</a-option>
        <a-option :value="'>'">&gt;</a-option>
      </template>
      <template  v-else-if="this.type === 'MaxMin'">
        <a-option :value="'smallest'">smallest</a-option>
        <a-option :value="'largest'">largest</a-option>
      </template>
      <template v-else-if="this.type === 'LessGreater'">
        <a-option :value="'less'">less</a-option>
        <a-option :value="'greater'">greater</a-option>
      </template>
      <template v-else-if="this.label === 'Direction'">
        <a-option :value="'forward'">forward</a-option>
        <a-option :value="'backward'">backward</a-option>
      </template>
    </a-select>
  </template>
  <a-textarea
    v-else
    style="width: 320px;margin: 2px 0;"
    :auto-size="{minRows: 1}"
    v-model="this.localArgValue"
    @input="onInput"
    />
</div>
</template>

<script>
import bus from './bus';

export default{
  name: 'ValueInput',
  model: {
    prop: 'argvalue',
    event: 'edited'
  },
  props: {
    config: Object,
    argvalue: String,
  },
  data() {
    return {
      label: '',
      type: '',
      whichKB: '',
      localArgValue: '',
    }
  },
  mounted() {
    this.label = this.config?.name;
    this.type = this.config?.type;
    this.whichKB = this.config?.kb;
    this.localArgValue = this.argvalue;
    bus.on('ChangeKB', newKB => this.whichKB = newKB);
  },
  methods: {
    onInput(v) {
      this.$emit('edited', v);
    }
  },
};
</script>