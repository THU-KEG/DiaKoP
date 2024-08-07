<template>
<div style="text-align: left;">
  <div>Qualifier Key:</div>
  <a-auto-complete :data="this.filterList" @search="handleSearch"
    style="width: 320px;"
    v-model="this.localArgValue"
    @change="this.onChange"></a-auto-complete>  
</div>
</template>

<script>
import bus from './bus';
import { AllQualifiersInSmallKB } from './smallQualifier';
import { AllQualifiersInLargeKB } from './largeQualifier';
import { KeysInSmallKB } from './smallKeyType';
import { KeysInLargeKB } from './largeKeyType';

export default{
  name: 'QualifierInput',
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
      type: '',
    }
  },
  methods: {
    handleSearch(value) {
      if (value) {
        if (this.whichKB == 'small') {
          console.log(this.type);
          if (this.type == 'Num') {
            this.filterList = KeysInSmallKB.quantity.filter(a => { return a.indexOf(value) != -1; });
          }
          else if (this.type == 'Str') {
            this.filterList = KeysInSmallKB.string.filter(a => { return a.indexOf(value) != -1; });
          }
          else if (this.type == 'Date' || this.type == 'Year') {
            this.filterList = KeysInSmallKB.date.filter(a => { return a.indexOf(value) != -1; });
          }
          else this.filterList = AllQualifiersInSmallKB.filter(q => { return q.indexOf(value) != -1; });
        }
        else if (this.whichKB == 'large') {
          if (this.type == 'Num') {
            this.filterList = KeysInLargeKB.quantity.filter(a => { return a.indexOf(value) != -1; });
          }
          else if (this.type == 'Str') {
            this.filterList = KeysInLargeKB.string.filter(a => { return a.indexOf(value) != -1; });
          }
          else if (this.type == 'Date' || this.type == 'Year') {
            this.filterList = KeysInLargeKB.date.filter(a => { return a.indexOf(value) != -1; });
          }
          else this.filterList = AllQualifiersInLargeKB.filter(q => { return q.indexOf(value) != -1; });
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
    this.type = this.config?.type;
    this.localArgValue = this.argvalue;
    bus.on('ChangeKB', newKB => this.whichKB = newKB);
  },
};

</script>
