<template>
<div style="text-align: left;">
  <div>Relation:</div>
  <a-auto-complete :data="this.filterList" @search="handleSearch"
    style="width: 320px;"
    v-model="this.localArgValue"
    @change="this.onChange"></a-auto-complete>  
</div>
</template>

<script>
import bus from './bus';
import { AllRelationsInSmallKB } from './smallRelation';
import { AllRelationsInLargeKB } from './largeRelation';

export default{
  name: 'RelationInput',
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
        if (this.whichKB == 'small') {
          this.filterList = AllRelationsInSmallKB.filter(r => { return r.indexOf(value) != -1; });
        }
        else if (this.whichKB == 'large') {
          this.filterList = AllRelationsInLargeKB.filter(r => { return r.indexOf(value) != -1; });
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
