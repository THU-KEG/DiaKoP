<template>
<div style="text-align: left;">
  <div>Concept:</div>
  <a-auto-complete :data="this.filterList" @search="handleSearch"
    style="width: 320px;"
    v-model="this.localArgValue"
    @change="this.onChange"></a-auto-complete>  
</div>
</template>

<script>
import bus from './bus';
import { AllConceptsInSmallKB } from './smallConcept';
import { AllConceptsInLargeKB } from './largeConcept';

export default{
  name: 'ConceptInput',
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
        if (this.whichKB == 'small') {
          this.filterList = AllConceptsInSmallKB.filter(c => { return c.indexOf(value) != -1; });
        } 
        else if (this.whichKB == 'large') {
          this.filterList = AllConceptsInLargeKB.filter(c => { return c.indexOf(value) != -1; });
        }
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
