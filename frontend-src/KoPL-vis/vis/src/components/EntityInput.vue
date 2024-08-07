<template>
<div style="text-align: left;">
  <div>Entity Name:</div>
  <a-auto-complete :data="this.filterList" @search="handleSearch"
    style="width: 320px;"
    v-model="this.localArgValue"
    @change="this.onChange"></a-auto-complete>  
</div>
</template>

<script>
import bus from './bus';

export default{
  name: 'EntityInput',
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
      whichKB: '',
      filterList: [],
      localArgValue: '',
    }
  },
  methods: {
    handleSearch(value) {
      if (value) {
        console.log(this.whichKB)
        // if (this.whichKB == 'small') {
        // } else if (this.whichKB == 'large') {
        // }
      } else {
        this.filterList = [];
      }
    },
    onChange(v) {
      this.$emit('edited', v);
    }
  },
  mounted() {
    this.whichKB = this.config?.kb;
    this.localArgValue = this.argvalue;
    bus.on('ChangeKB', newKB => this.whichKB = newKB);
  },
};

</script>
