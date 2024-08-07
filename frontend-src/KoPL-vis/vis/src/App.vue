<template>
  <div>
    <a-layout style="min-height: 800px;">
      <a-spin dot v-if="this.parsing" tip="question parsing" />
      <a-layout-header>
        <img src="./assets/kopl-icon.jpg" style="float: left; width: 50px; margin-right: 10px;" />
        
        <img src="./assets/vis-kop-logo.png" style="float: left; height: 40px; margin-top: 5px;" />

        <div style="float: right;">
          <a-link href="https://kopl.xlore.cn/program"
            style="font-size: 24px;" icon>KoPL自动编程</a-link>
        </div>
        <div style="float: right;">
          <a-link href="https://kopl.xlore.cn/doc/en/0_intro.html"
            style="font-size: 24px;" icon>Manual</a-link>
        </div>
        <div style="float: right;">
          <a-link href="https://youtu.be/zAbJtxFPTXo"
            style="font-size: 24px;" icon>Tutorial</a-link>
        </div>
      </a-layout-header>

      <a-layout style="margin-top: 2%">
        <a-layout-header style="display: flex; width: 100%; text-align: center;">
          <div style="width: 100%; float: left; margin: auto 5px auto 0;">
            <input class="kopl-input"
              id="ques-input"
              type="text"
              placeholder="Enter your question here..."
              v-model="this.question"
              autocomplete="off"
              @focus="this.inputFocus"
              @blur="this.inputBlur"
              @input="this.quesChange"
              style="width: 100%;" />
            <datalist id="ques-list" v-if="this.s_quesCandidates.length > 0">
              <option v-for="(q, i) in this.s_quesCandidates" :key="i"
                @mousedown="this.mouseDownOpt"
                v-on:click="this.clickOpt(q)" > {{ q }} </option>
            </datalist>
          </div>
        
          <div class="controls" style="float: left; margin: auto 0 auto 5px;">
            <button style="background-color: #113285; float: right; "
              id="parse-button"
              @click="this.onClickParse" >
              <IconPen :size="28" style="margin-left: 5%;"/>
              <span style="margin-left: 10%;">Parse</span>  
            </button>
          </div>
        </a-layout-header>
        <a-layout-content style="padding: 5px 0;">
          <div
            style="
              width: 100%;
              height: fit-content;
              min-height: 84px;
              margin: 1% auto 0.5px auto;
              text-align: center;
              font-size: 72px;
              font-family: Helvetica;
              resize: none;
              border-bottom:solid 0.5px #113285;
              border-left:solid 0.5px #113285;
              border-right:solid 0.5px #113285;
              border-top:solid 0.5px #113285;
              border-radius: 5px;
              background-color: white;"
            rows="1"
            readonly
            disabled>
                {{ this.answer }}
            </div>

          <div style="margin-top: 10px;
            border-bottom:solid 1px #113285;
            border-left:solid 1px #113285;
            border-right:solid 1px #113285;
            border-top:solid 1px #113285;
            height: fit-content">
            <ProgramVisBoard />
          </div>
        </a-layout-content>
      </a-layout>
      <a-layout-footer>
        <div class="controls" style="display: flex; justify-content: center; width: 100%; padding: 20px 0;"> <!-- using controls class to use style of Parse button -->
          <!-- Button to return to gradio/diakop -->
          <button id="return_to_diakop_button" 
                @click="onClickSendKoPLProgramAndClose" style="margin-bottom: 15px; padding: 9px 20px; background-color: #113285; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 19px;">
            Close and Copy KoPL Program
          </button>
        </div>
      </a-layout-footer>
      <a-layout-footer>
        <span style="font-weight: bold;">Copyright &copy; THUKEG 2022</span>
      </a-layout-footer>
    </a-layout>
  </div>
  <template>
    <a-modal v-model:visible="innerContentVisible"
      :ok-text="'OK'" :cancel-text="'Cancel'"
      @ok="this.innerContentVisible=false" @cancel="this.innerContentVisible=false">
      <template #title>
        Intermediate Result
      </template>
      <a-space wrap id="OpFunction">
        <a-tag v-for="(key,index) of whichInnerContent" :key="index.toString()" color="arcoblue" v-on:click="this.clickOpTag(key)">
          {{ key.entity_label }}
        </a-tag>
      </a-space>
      <a-space wrap id="QueryFunction">
        <a-tag v-for="(key,index) of valueList" :key="index.toString()" color="purple" v-on:click="this.clickQTag(key)">
          {{ key }}
        </a-tag>
      </a-space>
      <a-space wrap id="null">
        <a-tag id="null_text" color="gray" style="cursor:not-allowed;">null</a-tag>
      </a-space>
      <!--
      <JsonViewer :value="this.whichInnerContent"
        :expand-depth=5
        copyable
        boxed
        sort>
      </JsonViewer>
      -->
    </a-modal>
  </template>
  <template>
    <a-modal v-model:visible="detailsVisible"
      :ok-text="'OK'" :cancel-text="'Cancel'"
      @ok="this.detailsVisible=false" @cancel="this.detailsVisible=false">
      <template #title>
        Result Details
      </template>
      <JsonViewer :value="this.whichDetail"
        :expand-depth=5
        copyable
        boxed
        sort>
      </JsonViewer>
    </a-modal>
  </template>
  <template>
    <a-modal v-model:visible="codeVisible"
      :ok-text="'OK'" :cancel-text="'Cancel'"
      @ok="this.codeVisible=false" @cancel="this.codeVisible=false">
      <template #title>
        KoPL Code
      </template>
      <JsonViewer :value="this.s_prog"
        :expand-depth=5
        copyable
        sort>
      </JsonViewer>
    </a-modal>
  </template>
  <template>
    <a-modal v-model:visible="this.runningModalVisible"
      @cancel="onStopRunning"
      :cancel-text="'Quit'"
      :ok-loading="this.running"
      @ok="onSuccessRun"
      :ok-text="'OK'"
      :esc-to-close="false"
      :closable="false"
      >
      <template #title>
        Program Running
      </template>
      <a-spin dot v-if="this.running"/>
      <a-result v-else-if="!this.runError" status="success" title="Program was executed Successfully" />
      <a-result v-else status="error" title="Failed" />
    </a-modal>
  </template>
</template>

<script>

// imports for gradio/diakop
import {ref, onMounted} from 'vue'; // deleted onMounted, just use mounted

import {
  IconPen,
} from '@arco-design/web-vue/es/icon';
// import {
//   ref } from 'vue';
import ProgramVisBoard from './components/ProgramVisBoard.vue';
import bus from './components/bus';
import JsonViewer from 'vue-json-viewer';

/* eslint-disable */

export default {
  name: 'App',
  components: {
    IconPen,
    ProgramVisBoard,
    JsonViewer,
  },
  setup() {
    const transferredQuestion = ref('');  // define gradio/diakop's transferred question
    const transferredData = ref('');  // define gradio/diakop's transferred data

    const whichKB = ref('small');
    // const username = ref('');
    // const quesnumber = ref(0);
    // const timestamp = ref(Number)
    const elapsedTime = ref(Number);
    const parsed = ref(false);
    const parsing = ref(false);
    const s_prog = ref([]);
    const running = ref(false);
    const runError = ref(false);

    const question = ref('');
    const answer = ref('');
    const s_answer = ref('');
    const innerContent = ref([]);
    const s_innerContent = ref([]);
    const whichInnerContent = ref(Object);
    const innerContentVisible = ref(false);
    const whichDetail = ref(Object);
    const detailsVisible = ref(false);
    const codeVisible = ref(false);
    
    const quesCandidates = ref([
      'When did China join the WTO?',
      'Which one is longest among movies which were published in 1990?',
      'Who is taller, LeBron James or Kobe Byrant?',
      'How many countries does Germany share a border with?',
      'What feature film was nominated for an Academy Award for Best Supporting Actor and an Academy Award for Best Actor?',
      'Did the television series titled All in the Family start on 1971-01-12?',
      'In which city is Tsinghua University located?',
      'Of New Jersey cities with under 350000 in population, which is biggest in terms of area?',
      'Which show produced by Dreamworks is the longest?',
      'Who is the director of the film Avatar?',
    ]);
    const s_quesCandidates = ref([]);
    s_quesCandidates.value = quesCandidates.value;
    const quesChange = () => {
      if (question.value.length === 0) {
        s_quesCandidates.value = quesCandidates.value;
        return;
      }
      s_quesCandidates.value = quesCandidates.value.filter(q => {
        return q.indexOf(question.value) != -1;
      });
    }; 

    const runningModalVisible = ref(false);

    const ignoreAnswer = ref(false);
    const ignoreInnerContent = ref(false);

    const valueList = ref([]);

    bus.on('ParseOver', (prog) => { 
      parsing.value = false;
      parsed.value = true;
      s_prog.value = prog;
      document.getElementById('parse-button').disabled = false;
    });
    bus.on('GetAnswer', ans => {
      s_answer.value = ans;
      running.value = false;
      document.getElementById('run-button').disabled = false;
    });
    bus.on('GetInnerContent', e => {
      s_innerContent.value = e.innerContent;
    });
    bus.on('ShowInnerContent', idx => {
      whichInnerContent.value = innerContent.value[idx];
      innerContentVisible.value = true;  
      // console.log(whichInnerContent.value);
      if (whichInnerContent.value == null) { // findAll处理
        valueList.value = null;
        document.getElementById('OpFunction').style.display = "none";
        document.getElementById('QueryFunction').style.display = "none";
        document.getElementById('null_text').innerText = "Not Presentable";
        document.getElementById('null').style.display = "";
      } else if (JSON.stringify(whichInnerContent.value) === "[]") { // 空结果处理
        valueList.value = null;
        document.getElementById('OpFunction').style.display = "none";
        document.getElementById('QueryFunction').style.display = "none";
        document.getElementById('null_text').innerText = "null";
        document.getElementById('null').style.display = "";
      } else { // 非空结果
        var arr = Object.values(whichInnerContent.value);
        var isOpFunction = arr[0].entity_label !== undefined; // 判断是否包含entity_label字段 -> 包含则是操作函数
        if (arr[0] instanceof Array) { // arr[0]是array
          if (arr[0].length > 0)
            valueList.value = arr[0]; // 非空array
          else
            valueList.value = null; // 空array
        } else { // arr[0]不是array，只包含一个元素
          valueList.value = [arr[0]]; // 封装成array，避免valueList错误将单个字符串拆成array
        } 
        if (valueList.value == null) { // 无数据，显示null
          document.getElementById('OpFunction').style.display = "none";
          document.getElementById('QueryFunction').style.display = "none";
          document.getElementById('null').style.display = "";
          document.getElementById('null_text').innerText = "null";
        }
        else if (isOpFunction) { // 操作函数，仅展示entity_label
          document.getElementById('OpFunction').style.display = "";
          document.getElementById('QueryFunction').style.display = "none";
          document.getElementById('null').style.display = "none";
        } else { // 查询函数，展示value
          document.getElementById('QueryFunction').style.display = "";
          document.getElementById('OpFunction').style.display = "none";
          document.getElementById('null').style.display = "none";
        }
      }
    });

    // extract parse program passed by gradio/diakop
    onMounted(() => {
      console.log('App.vue: Component is mounted to the DOM');

      
      const queryParams = new URLSearchParams(window.location.search);
      const questionParam = queryParams.get('question')
      const dataParam = queryParams.get('data');

      // setup()里不能用this.transferredData，要用transferredData.value
      transferredQuestion.value = questionParam; 
      transferredData.value = dataParam; 

      // display question
      question.value = transferredQuestion.value;

      transferredData.value = transferredData.value.replace(/'/g, '"'); // don't need as long as we input program strings with "" around inner attributes

      console.log("transferredQuestion.value:", transferredQuestion.value);
      console.log("transferredData.value:", transferredData.value);

      let program = JSON.parse((transferredData.value)); 

      bus.emit('VisualizeProgram', program); // emit an event to visualize program, implementation in ProgramVisBoard.vue

    });

    return {
      transferredQuestion, // gradio/diakop transferred question
      transferredData,  // gradio/diakop transferred data
      whichKB,
      // username,
      // quesnumber,
      question,
      answer,
      s_answer,
      innerContent,
      s_innerContent,
      whichInnerContent,
      whichDetail,
      innerContentVisible,
      // timestamp,
      elapsedTime,
      parsed,
      parsing,
      running,
      ignoreAnswer,
      ignoreInnerContent,
      runningModalVisible,
      s_prog,
      runError,
      codeVisible,
      s_quesCandidates,
      quesChange,
      valueList, 
      detailsVisible
    }
  },
  mounted() {
    bus.on('WrongFlowChart', einfo => {
      this.$message.info(`Invalid flow diagram: ${einfo}!`);
      this.running = false;
      document.getElementById('run-button').disabled = false;
    });
    bus.on('RuntimeError', e => {
      this.$message.info(`Runtime error: ${e.message}!`);
      this.running = false;
      this.runError = true;
      document.getElementById('run-button').disabled = false;
    });
    bus.on('StartRunning', (prog) => {
      document.getElementById('run-button').disabled = true;
      this.running = true;
      this.runningModalVisible = true;
      this.parsed = true;
      this.s_prog = prog;
    });
    bus.on('ObtainNewestKoPLProgramFromBoard', (prog) => {  // gradio -- returns the most recent KoPL program
      this.s_prog = prog;
      console.log("3 Inside ObtainNewestKoPLProgramFromBoard")
      console.log("prog:", prog)
    });
    bus.on('CancelManually', () => {
      this.ignoreAnswer = true;
      this.ignoreInnerContent = true;
      this.running = false;
      this.$message.info(`You stop the program!`);
      document.getElementById('run-button').disabled = false;
    });
    bus.on('PaneClickRun', this.onClickRun);
    bus.on('ClickCode', () => {
      this.codeVisible = true;
    });
    bus.on('ClickClear', this.onClickClear);
  },
  computed: {
    collap () {
      return this.s_prog.length === 0;
    }
  },
  methods: {
    onClickSendKoPLProgramAndClose() {  // copy KoPL program to clip board and closes VisKoP's window
      console.log('1 Inside onClickSendKoPLProgramAndClose');

      // tried to send message to diakop's url, but gradio 3.50.2 doesn't support this function
      // window.opener.postMessage("Message from VisKoP", "http://localhost:7888");  // replace with actual url of gradio/diakop

      // update newest kopl program from board (同步算子更改)
      bus.emit('clickSendKoPLProgramAndClose');


      // copying KoPL function instead
      // get the KoPL program
      const koplProgram = JSON.stringify(this.s_prog);

      // copy the KoPL program to the clipboard
      navigator.clipboard.writeText(koplProgram)
        .then(() => {
          console.log('KoPL program copied to clipboard');
          console.log('KoPL program:', koplProgram);

          // Show a confirmation message to the user
          alert('Content Copied! The window will now close.');

          // Wait for the clipboard operation to finish before closing the window
          window.close(); // only closes if the window was opened by script
        })
        .catch((error) => {
          console.error('Failed to copy KoPL program to clipboard:', error);
          alert('Failed to copy content to clipboard.');
        });
    },
    onClickParse() {
      this.timestamp = new Date().getTime();
      this.$message.info('Not implemented');
    },
    onClickRun() {
      this.$message.info('Not implemented');

      bus.emit('ClickRun', {}
        //{username: this.username, ts: this.timestamp, qn: this.quesnumber}
      );
    },
    onStopRunning() {
      if (this.running){
        bus.emit('CancelManually');
      }
      else {
        this.onSuccessRun();
      }
    },
    onSuccessRun() {
      if (this.runError) {
        this.runError = false;
        this.runningModalVisible = false;
        return;
      }
      this.innerContent = this.s_innerContent;
      this.runningModalVisible = false
      this.answer = this.s_answer;
    },
    onClickClear() {
      this.s_answer = '';
      this.answer = '';
      this.s_prog = [];
      this.parsed = false;
    },
    inputFocus() {
      if (!document.getElementById('ques-list')) {
        return;
      }
      document.getElementById('ques-list').style.display = 'block';
    },
    inputBlur() {
      if (!document.getElementById('ques-list')) {
        return;
      }
      document.getElementById('ques-list').style.display = 'none';
    },
    mouseDownOpt(event) {
      event.preventDefault();
    },
    clickOpt(q) {
      this.question = q;
      document.getElementById('ques-list').style.display = 'none';
    },
    clickOpTag(key) {
      // console.log(key);
      this.whichDetail = key;
      this.detailsVisible = true;
    }, 
    clickQTag(key) {
      // console.log(key);
      this.whichDetail = key;
      this.detailsVisible = true;
    }, 
    /*
    convertUTF8(label) {
      console.log(label);
      var str = String.fromCharCode(\u00F1); // 用ñ测试转码
      return str;
    } */
  },
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin: 10px 10%;
  min-width: 1000px;
}

.kopl-input {
  height: 40px;
  font-size: 24px;
  font-family: 'Times New Roman', Times, serif;
  border-color: #113285;
  border-radius: 8px;
}

datalist {
  position: absolute;
  background-color: white;
  border: 1px solid #0c3bb4;
  border-radius: 0 0 5px 5px;
  border-top: none;
  font-family: sans-serif;
  width: 73.5%;
  padding: 5px;
  max-height: 10rem;
  overflow-y: auto
}

option {
  background-color: white;
  text-align: left;
  padding: 4px;
  color: black;
  margin-bottom: 1px;
  font-size: 18px;
  cursor: pointer;
}

option:hover,  .active{
  background-color: lightblue;
}

.controls button{
  height: 40px;
  padding: 5px;
  border-radius: 5px;
  font-size: large;
  font-weight: 500;
  box-shadow:0 5px 10px #0000004d;
  cursor:pointer;
  display: flex;
  color: white
}

.controls button:hover{
  opacity:.8;
  transform:scale(105%);
  transition:.25s all ease
}

.arco-tag {
    cursor: pointer;
}

.arco-tag.arco-tag-checked.arco-tag-arcoblue:hover {
    color: white;
    background-color: rgb(var(--arcoblue-5));
    border: 1px solid transparent;
}

.arco-tag.arco-tag-checked.arco-tag-purple:hover {
    color: white;
    background-color: rgb(var(--purple-4));
    border: 1px solid transparent;
}

</style>
