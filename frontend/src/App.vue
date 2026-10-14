<!-- ServiceWeave 双模式界面：用户聊天与开发者工作台共享会话状态，接口请求集中在 lib/backends.js。 -->
<template>
  <main :class="['app-shell', `app-shell-${activeView}`, isDeveloper ? 'mode-developer' : 'mode-user', { 'has-messages': messages.length > 0 }]">
    <aside v-if="isDeveloper" class="app-rail">
      <a class="brand" href="#" aria-label="ServiceWeave 工作台首页" @click.prevent="activeView = 'chat'">
        <span class="brand-mark"><BrandMark /></span>
        <span class="brand-name">ServiceWeave<small>DEVELOPER STUDIO</small></span>
      </a>
      <div class="rail-label">工作空间 <span>WORKSPACE</span></div>
      <nav class="view-nav" aria-label="工作区">
        <button :class="{ active: activeView === 'chat' }" :aria-current="activeView === 'chat' ? 'page' : undefined" @click="activeView = 'chat'"><AppIcon name="chat" /><span>对话调试</span><AppIcon class="nav-arrow" name="chevron" /></button>
        <button :class="{ active: activeView === 'knowledge' }" :aria-current="activeView === 'knowledge' ? 'page' : undefined" @click="activeView = 'knowledge'"><AppIcon name="book" /><span>知识库</span><AppIcon class="nav-arrow" name="chevron" /></button>
        <button :class="{ active: activeView === 'evaluation' }" :aria-current="activeView === 'evaluation' ? 'page' : undefined" @click="activeView = 'evaluation'"><AppIcon name="chart" /><span>效果评测</span><AppIcon class="nav-arrow" name="chevron" /></button>
      </nav>
      <div class="rail-note"><span class="rail-note-icon"><AppIcon name="code" /></span><strong>理解每一次决策。</strong><p>观察路由、检索与工具调用，<br />让 Agent 的工作过程可见。</p><span class="rail-note-caption">OBSERVE · EVALUATE · ITERATE</span></div>
      <div class="rail-footer"><span class="avatar-button">{{ userInitial }}</span><div><strong>{{ settings.userId || 'anonymous' }}</strong><small>当前工作空间</small></div><span class="workspace-dot"></span></div>
    </aside>
    <div class="main-workspace">
    <header class="topbar">
      <div v-if="isDeveloper" class="breadcrumb"><span>开发者工作台</span><AppIcon name="chevron" /><strong>{{ viewLabels[activeView] }}</strong></div>
      <a v-else class="brand customer-brand" href="#" aria-label="ServiceWeave 首页" @click.prevent="focusConversation"><span class="brand-mark"><BrandMark /></span><span class="brand-name">ServiceWeave<small>让服务，恰如其分。</small></span></a>
      <div class="topbar-tools">
        <span v-if="isDeveloper" class="environment-pill">
          <i :class="healthOk ? 'online' : 'offline'"></i>
          {{ healthOk ? '服务已连接' : '服务未连接' }}
        </span>
        <button v-else class="new-chat-button" aria-label="新对话" @click="clearConversation" :disabled="busy"><AppIcon name="plus" /><span>新对话</span></button>
        <button class="mode-switch" @click="switchMode"><AppIcon :name="isDeveloper ? 'chat' : 'code'" /><span>{{ isDeveloper ? '用户聊天' : '开发者工作台' }}</span><AppIcon name="arrow" /></button>
      </div>
    </header>

    <div v-if="toast" class="toast" role="status">{{ toast }}</div>

    <section v-if="activeView === 'chat'" class="page page-chat">
      <div v-if="isDeveloper" class="page-heading">
        <div class="heading-copy">
          <span class="kicker">PLAYGROUND / CONVERSATION</span>
          <h1>对话调试<span class="title-dot">.</span></h1>
          <p>发送测试请求，观察意图识别、Agent 路由与工具调用。</p>
        </div>
        <div class="heading-actions">
          <button class="quiet-button" @click="clearConversation" :disabled="busy"><AppIcon name="plus" />新建对话</button>
        </div>
      </div>

      <div class="chat-layout">
        <section class="chat-stage">
          <div v-if="isDeveloper || messages.length" class="stage-bar">
            <div class="stage-context">
              <span class="stage-icon"><AppIcon name="chat" /></span>
              <strong>{{ isDeveloper ? '对话测试' : 'ServiceWeave 助手' }}</strong><span v-if="isDeveloper" class="agent-tag">LIVE SESSION</span>
            </div>
            <span>{{ isDeveloper ? `${messages.length} 条消息` : '很高兴为你解答' }}</span>
          </div>

          <div class="messages" :class="{ 'is-empty': messages.length === 0 }" ref="messageList" role="log" aria-label="对话记录" aria-live="polite" :aria-busy="sending">
            <article v-for="item in messages" :key="item.id" :class="['message', item.role]">
              <div class="message-meta">
                <span class="message-avatar"><AppIcon v-if="item.role === 'user'" name="user" /><BrandMark v-else /></span>
                <span>{{ item.role === 'user' ? '你' : 'ServiceWeave' }}</span>
                <small v-if="isDeveloper && item.meta">{{ item.meta }}</small>
              </div>
              <p>{{ item.content }}</p>
              <details v-if="isDeveloper && item.error" class="message-error"><summary>查看错误详情</summary><pre>{{ item.error }}</pre></details>
              <div v-if="isDeveloper && item.trace" class="message-trace">
                <div class="trace-head">
                  <span>工具调用</span>
                  <small v-if="item.trace.requestId">#{{ item.trace.requestId }}</small>
                </div>
                <div v-if="item.trace.toolCalls?.length" class="trace-calls">
                  <details v-for="(call, index) in item.trace.toolCalls" :key="`${item.id}-${index}`" open>
                    <summary>
                      <strong>{{ call.tool_name || 'unknown_tool' }}</strong>
                      <span>{{ call.success ? '成功' : '失败' }}</span>
                    </summary>
                    <pre>{{ formatJson(call.input || {}) }}</pre>
                  </details>
                </div>
                <div v-else class="trace-empty-block">
                  <p>本次请求已生成 trace，但没有可展示的工具输入。</p>
                  <p v-if="item.trace.toolsUsed?.length" class="trace-note">已调用：{{ item.trace.toolsUsed.join(' · ') }}</p>
                </div>
              </div>
            </article>

            <div v-if="messages.length === 0" class="empty-state">
              <div class="welcome-emblem" aria-hidden="true"><span class="emblem-ring"></span><BrandMark /><span class="emblem-spark">✳</span></div>
              <span class="empty-eyebrow">{{ isDeveloper ? 'READY FOR YOUR NEXT REQUEST' : 'A LITTLE HELP. A BETTER DAY.' }}</span>
              <h2 v-if="isDeveloper">一次对话，<span>看见整个过程。</span></h2>
              <h1 v-else class="customer-greeting">你好，今天有什么<br /><span>可以帮到你？</span></h1>
              <p v-if="isDeveloper">从下面的场景开始测试，响应与执行详情将在这里呈现。</p>
              <p v-else>从订单售后到产品使用，把问题交给我。<br />让复杂的事情，简单一点。</p>
              <div class="starter-prompts">
                <button @click="usePrompt('我想申请退款，订单号是 #12345')"><span class="prompt-icon"><AppIcon name="return" /></span><span><strong>订单与售后</strong><small>退款、退货，帮你理清流程</small></span><AppIcon name="arrow" /></button>
                <button @click="usePrompt('登录时提示错误，应该怎么排查？')"><span class="prompt-icon"><AppIcon name="support" /></span><span><strong>使用遇到问题</strong><small>一起找到解决问题的方法</small></span><AppIcon name="arrow" /></button>
                <button @click="usePrompt('发票多久可以开具？')"><span class="prompt-icon"><AppIcon name="receipt" /></span><span><strong>支付与发票</strong><small>账单和开票，为你解答</small></span><AppIcon name="arrow" /></button>
              </div>
            </div>
            <div v-if="sending" class="thinking-state" role="status"><span></span><span></span><span></span>正在理解问题并组织回答…</div>
          </div>

          <form class="composer" @submit.prevent="sendMessage">
            <textarea
              v-model="draft"
              ref="composerInput"
              aria-label="输入消息"
              rows="3"
              :placeholder="isDeveloper ? '输入测试消息…' : '说说你的问题吧…'"
              @keydown.meta.enter.prevent="sendMessage"
              @keydown.ctrl.enter.prevent="sendMessage"
            ></textarea>
            <div class="composer-bottom">
              <span class="composer-caption"><BrandMark v-if="!isDeveloper" /><span v-if="!isDeveloper">ServiceWeave</span><span class="keyboard-hint"><kbd>Ctrl</kbd> / <kbd>⌘</kbd> + <kbd>Enter</kbd> 发送</span></span>
              <button type="submit" aria-label="发送消息" :disabled="busy || refreshing || !draft.trim()"><span v-if="isDeveloper">{{ sending ? '处理中' : '发送消息' }}</span><AppIcon name="send" /></button>
            </div>
          </form>
          <div class="composer-note"><AppIcon name="shield" />AI 生成的回答仅供参考，请核实重要信息。</div>
        </section>

        <aside v-if="isDeveloper" class="chat-sidebar">
          <div class="insights-heading"><AppIcon name="settings" /><h2>配置与洞察</h2><span>INSPECTOR</span></div>
          <div class="chat-sidebar-scroll">
            <section class="side-card session-settings-card">
              <div class="card-heading">
                <div>
                  <h2>会话设置</h2>
                </div>
                <span class="status-copy muted">{{ settings.conversationId ? '进行中' : '新会话' }}</span>
              </div>

              <label>
                <span>用户 ID</span>
                <input v-model="settings.userId" :disabled="busy" @change="persist" placeholder="u1001" />
              </label>
              <label>
                <span>会话 ID</span>
                <input v-model="settings.conversationId" :disabled="busy" @change="persist" placeholder="首次对话后自动生成" />
              </label>
              <div class="side-actions">
                <button class="quiet-button" @click="refreshConsole" :disabled="busy || refreshing"><AppIcon name="refresh" />{{ refreshing ? '检查中…' : '刷新状态' }}</button>
                <a class="settings-docs" :href="docsUrl" target="_blank" rel="noreferrer">API 文档<AppIcon name="arrow" /></a>
              </div>
              <div v-if="!healthOk" class="connection-note"><AppIcon name="info" />服务未连接，启动后端后可刷新状态。</div>
            </section>

            <section class="side-card trace-card">
              <div class="card-heading">
                <div>
                  <h2>最近一次请求</h2>
                </div>
                <span class="trace-status" :class="lastResponse ? 'has-data' : ''"></span>
              </div>

              <div v-if="lastResponse" class="trace-body">
                <div class="latency">
                  <span>响应耗时</span>
                  <strong>{{ lastResponse.latencyMs || '-' }}<small> ms</small></strong>
                </div>
                <dl class="detail-list">
                  <div><dt>主 Agent</dt><dd>{{ lastResponse.primaryAgent || lastResponse.agentType || '-' }}</dd></div>
                  <div><dt>意图</dt><dd>{{ lastResponse.intent || '-' }}</dd></div>
                  <div><dt>置信度</dt><dd>{{ formatPercent(lastResponse.routingConfidence) }}</dd></div>
                  <div><dt>知识库</dt><dd :class="lastResponse.knowledgeUsed ? 'success' : 'muted'">{{ lastResponse.knowledgeUsed ? '已使用' : '未使用' }}</dd></div>
                  <div><dt>转人工</dt><dd :class="lastResponse.escalated ? 'danger' : 'muted'">{{ lastResponse.escalated ? '是' : '否' }}</dd></div>
                </dl>
                <p v-if="lastResponse.routingReason" class="routing-reason">{{ lastResponse.routingReason }}</p>
                <div v-if="lastTrace?.trace" class="trace-call-list">
                  <div class="trace-call-title">工具调用</div>
                  <div v-for="(call, index) in lastTrace.trace.toolCalls" :key="`${call.tool_use_id || index}`" class="trace-call-item">
                    <div class="trace-call-meta">
                      <strong>{{ call.tool_name || 'unknown_tool' }}</strong>
                      <span>{{ call.latency_ms || 0 }} ms</span>
                    </div>
                    <pre>{{ formatJson(call.input || {}) }}</pre>
                  </div>
                  <div v-if="!lastTrace.trace.toolCalls?.length" class="trace-empty-block">
                    <p>这次 trace 没有记录到工具输入。</p>
                    <p v-if="lastTrace.trace.toolsUsed?.length" class="trace-note">已调用：{{ lastTrace.trace.toolsUsed.join(' · ') }}</p>
                  </div>
                </div>
              </div>
              <div v-else class="trace-placeholder"><div class="trace-placeholder-icon"><AppIcon name="activity" /></div><strong>等待第一条消息</strong><p>从理解意图，到生成答案，<br />在这里查看 Agent 的工作过程。</p><ol class="process-steps"><li><span>01</span>识别客户意图</li><li><span>02</span>检索业务知识</li><li><span>03</span>协作生成答案</li></ol></div>
            </section>

            <section class="side-card monitor-card">
              <div class="card-heading">
                <div>
                  <h2>运行状态</h2>
                </div>
                <button class="icon-button" @click="loadMonitor" aria-label="刷新运行状态" :disabled="busy"><AppIcon name="refresh" /></button>
              </div>
              <div class="mini-stats">
                <div><strong>{{ monitorLoaded ? totalRequests : '—' }}</strong><span>请求</span></div>
                <div><strong>{{ monitorLoaded ? agentCount : '—' }}</strong><span>Agent</span></div>
                <div><strong>{{ monitorLoaded ? activeAlerts.length : '—' }}</strong><span>告警</span></div>
              </div>
              <div v-if="activeAlerts.length" class="alert-note">{{ activeAlerts[0].detail || activeAlerts[0].title }}</div>
              <p v-else-if="monitorLoaded" class="healthy-note"><AppIcon name="check" />当前没有活跃告警</p>
              <p v-else class="monitor-note">连接服务后显示运行数据</p>
            </section>
          </div>
        </aside>
      </div>
    </section>

    <section v-else-if="activeView === 'knowledge'" class="page page-knowledge">
      <div class="page-heading">
        <div class="heading-copy">
          <span class="kicker">Knowledge operations</span>
          <h1>知识库<span class="title-dot">.</span></h1>
          <p>搜索、补充和维护客服 Agent 使用的知识片段。</p>
        </div>
        <div class="count-display"><AppIcon name="book" /><strong>{{ knowledgeCount }}</strong><span>知识片段</span></div>
      </div>

      <div class="knowledge-layout">
        <section class="workspace-card search-workspace">
          <div class="card-heading">
            <div><span class="kicker">Retrieval</span><h2>检索知识</h2></div>
            <span class="section-icon"><AppIcon name="search" /></span>
          </div>
          <div class="search-line">
            <input v-model="searchQuery" aria-label="检索知识" placeholder="例如：退款多久到账" @keydown.enter="searchKnowledge" />
            <button @click="searchKnowledge" :disabled="busy || !searchQuery.trim()"><AppIcon name="search" />搜索</button>
          </div>
          <div v-if="searchResults.length" class="result-list">
            <article v-for="(item, index) in searchResults" :key="item.id || item.title || index" class="result-item">
              <span class="result-number">{{ String(index + 1).padStart(2, '0') }}</span>
              <div>
                <div class="result-title"><strong>{{ item.title || '未命名文档' }}</strong><small>score {{ item.score ?? '-' }}</small></div>
                <p>{{ item.content }}</p>
              </div>
            </article>
          </div>
          <div v-else class="workspace-empty"><AppIcon name="search" /><strong>{{ searchCompleted ? '没有找到相关知识' : '好答案，从找到知识开始' }}</strong><p>{{ searchCompleted ? '换个关键词，或添加相关业务文档后再试。' : '输入客户问题，检索与之相关的业务知识。' }}</p></div>
        </section>

        <section class="workspace-card import-workspace">
          <div class="card-heading">
            <div><span class="kicker">Ingestion</span><h2>添加知识</h2></div>
            <span class="section-icon"><AppIcon name="upload" /></span>
          </div>
          <label><span>标题</span><input v-model="docTitle" placeholder="退款补充政策" /></label>
          <label><span>内容</span><textarea v-model="docContent" rows="7" placeholder="输入客服规范、产品说明或排障流程"></textarea></label>
          <div class="side-actions">
            <button @click="submitKnowledge" :disabled="busy || !docTitle.trim() || !docContent.trim()"><AppIcon name="plus" />添加文档</button>
            <label class="upload-button" :class="{ disabled: busy }"><AppIcon name="upload" />上传文件<input type="file" :disabled="busy" accept=".txt,.md,.json" @change="handleUpload" /></label>
          </div>
          <p class="field-hint">支持 .txt、.md、.json 格式的知识文件</p>
        </section>
      </div>

      <section class="workspace-card skills-workspace">
        <div class="card-heading">
          <div><span class="kicker">Loaded skills</span><h2>已加载能力</h2></div>
          <button class="link-button" @click="reloadSkillSet" :disabled="busy"><AppIcon name="refresh" />重新加载</button>
        </div>
        <div class="skill-table">
          <div v-for="skill in skillsData.skills" :key="skill.name" class="skill-item">
            <span class="skill-dot"></span><strong>{{ skill.name }}</strong><span>{{ skill.description || '业务规范能力' }}</span><small>{{ skill.content_chars || 0 }} chars</small>
          </div>
          <div v-if="!skillsData.skills.length" class="workspace-empty compact"><AppIcon name="book" /><p>暂无已加载能力，连接服务后可刷新查看。</p></div>
        </div>
      </section>
    </section>

    <section v-else class="page page-evaluation">
      <div class="page-heading">
        <div class="heading-copy">
          <span class="kicker">Evaluation lab</span>
          <h1>效果评测<span class="title-dot">.</span></h1>
          <p>让每一次改进都有据可循，持续提升 Agent 的服务质量。</p>
        </div>
        <button @click="runEvaluation" :disabled="busy"><AppIcon name="chart" />{{ evaluating ? '评测中…' : '运行评测' }}</button>
      </div>

      <div v-if="evalData" class="evaluation-content">
        <div class="evaluation-summary">
          <div class="score-hero"><span>Pass rate</span><strong>{{ formatPercent(evalData.pass_rate) }}</strong><small>{{ evalData.passed }} / {{ evalData.total }} cases passed</small></div>
          <div><span>通过</span><strong>{{ evalData.passed }}</strong></div>
          <div><span>总数</span><strong>{{ evalData.total }}</strong></div>
          <div><span>回归</span><strong :class="evalData.regressions?.length ? 'danger' : 'success'">{{ evalData.regressions?.length || 0 }}</strong></div>
        </div>
        <div class="evaluation-layout">
          <section class="workspace-card">
            <div class="card-heading"><div><span class="kicker">Scores</span><h2>平均评分</h2></div></div>
            <div class="score-list">
              <div v-for="(value, key) in evalData.avg_scores" :key="key"><span>{{ key }}</span><i><b :style="{ width: `${Math.min(Number(value) * 10, 100)}%` }"></b></i><strong>{{ Number(value).toFixed(2) }}</strong></div>
            </div>
          </section>
          <section class="workspace-card">
            <div class="card-heading"><div><span class="kicker">Recommendations</span><h2>优化建议</h2></div></div>
            <div v-if="evalData.recommendations?.length" class="recommendations"><p v-for="(item, index) in evalData.recommendations" :key="index">{{ item }}</p></div>
            <div v-else class="workspace-empty">本次评测没有返回额外建议。</div>
          </section>
        </div>
      </div>
      <div v-else class="evaluation-empty"><span class="evaluation-badge">QUALITY & CONFIDENCE</span><div class="evaluation-art" aria-hidden="true"><i></i><i></i><i></i><i></i><AppIcon name="check" /></div><h2>{{ evaluating ? '正在评估每一个回答…' : '好的服务，经得起检验。' }}</h2><p>{{ evaluating ? '评测可能需要一些时间，结果会在这里自动展示。' : '通过真实场景检验 Agent 的表现，发现优势与下一步的改进方向。' }}</p><div class="evaluation-dimensions"><span><AppIcon name="chat" />意图识别</span><span><AppIcon name="shield" />回答质量</span><span><AppIcon name="activity" />回归检测</span></div><button @click="runEvaluation" :disabled="busy"><AppIcon name="chart" />{{ evaluating ? '正在运行评测…' : '开始首次评测' }}</button><small>结果包含通过率、维度评分与优化建议</small></div>
    </section>
    <footer class="workspace-footer"><span>ServiceWeave<span class="footer-separator">/</span>{{ isDeveloper ? 'Developer Studio' : '用心连接每一次服务' }}</span><span>{{ isDeveloper ? '多 Agent 协作 · 可观测 · 可评测' : '订单售后 · 产品支持 · 账单咨询' }}</span></footer>
    </div>
  </main>
</template>

<script setup>
import AppIcon from './components/AppIcon.vue'
import BrandMark from './components/BrandMark.vue'
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import {
  addKnowledge,
  backendMeta,
  createInitialSettings,
  reloadSkills,
  requestChat,
  requestHealth,
  requestKnowledgeStats,
  requestMonitor,
  requestSearch,
  requestToolTrace,
  requestSkills,
  runEvaluation as requestEvaluation,
  saveSettings,
  uploadKnowledge
} from './lib/backends'

const settings = reactive(createInitialSettings())
// 模式仅影响展示；会话、输入草稿与请求状态由两个界面共享。
const workspaceMode = ref('user')
const isDeveloper = computed(() => workspaceMode.value === 'developer')
const activeView = ref('chat')
const messages = ref([])
const draft = ref('')
const busy = ref(false)
const refreshing = ref(false)
const sending = ref(false)
const evaluating = ref(false)
const monitorLoaded = ref(false)
const searchCompleted = ref(false)
const composerInput = ref(null)
const viewLabels = { chat: '对话调试', knowledge: '知识库', evaluation: '效果评测' }
const healthOk = ref(false)
const statusText = ref('')
const knowledgeCount = ref('-')
const searchQuery = ref('退款多久能到账')
const searchResults = ref([])
const docTitle = ref('')
const docContent = ref('')
const messageList = ref(null)
const monitorData = ref({ agent_stats: {}, tool_stats: {}, active_alerts: [], suggestions: [] })
const skillsData = ref({ count: 0, skills: [], errors: [] })
const lastResponse = ref(null)
const lastTrace = ref(null)
const evalData = ref(null)
const toast = ref('')
let toastTimer
let messageSequence = 0

const currentBackend = computed(() => backendMeta(settings.backend, settings))
const docsUrl = computed(() => `${currentBackend.value.baseUrl}/docs`)
const userInitial = computed(() => (settings.userId || 'U').slice(0, 1).toUpperCase())
const activeAlerts = computed(() => monitorData.value.active_alerts || [])
const agentCount = computed(() => Object.keys(monitorData.value.agent_stats || {}).length)
const totalRequests = computed(() => Object.values(monitorData.value.agent_stats || {}).reduce((sum, item) => sum + Number(item.total || 0), 0))

watch(() => settings.conversationId, persist)
onMounted(() => {
  refreshConsole()
})

onBeforeUnmount(() => {
  clearTimeout(toastTimer)
})

function persist() { saveSettings(settings) }

async function switchMode() {
  workspaceMode.value = isDeveloper.value ? 'user' : 'developer'
  activeView.value = 'chat'
  document.title = isDeveloper.value ? 'ServiceWeave · 开发者工作台' : 'ServiceWeave · 智能客服'
  if (isDeveloper.value) refreshConsole()
  await scrollMessages()
}

function focusConversation() {
  activeView.value = 'chat'
  composerInput.value?.focus()
}

async function refreshConsole() {
  if (refreshing.value || busy.value) return
  refreshing.value = true
  try {
    await checkHealth()
    await Promise.allSettled([loadStats(), loadMonitor(), loadSkills()])
  } finally { refreshing.value = false }
}

async function checkHealth() {
  try {
    const data = await requestHealth(settings.backend, settings)
    healthOk.value = data.status === 'ok'
    statusText.value = JSON.stringify(data, null, 2)
  } catch (error) {
    healthOk.value = false
    statusText.value = error.message


  }
}

async function loadStats() {
  try {
    const data = await requestKnowledgeStats(settings.backend, settings)
    knowledgeCount.value = data.total_chunks ?? data.totalChunks ?? '-'
  } catch {
    knowledgeCount.value = '-'
  }
}

async function loadMonitor() {
  try {
    monitorData.value = await requestMonitor(settings.backend, settings)
    monitorLoaded.value = true
  } catch {
    monitorLoaded.value = false
    monitorData.value = { agent_stats: {}, tool_stats: {}, active_alerts: [], suggestions: [] }
  }
}

async function loadSkills() {
  try {
    skillsData.value = await requestSkills(settings.backend, settings)
  } catch {
    skillsData.value = { count: 0, skills: [], errors: [] }
  }
}

async function reloadSkillSet() {
  busy.value = true
  try {
    skillsData.value = await reloadSkills(settings.backend, settings)
    showToast('Skills 已重新加载')
  } catch (error) {
    statusText.value = error.message
    showToast('Skills 加载失败')
  } finally { busy.value = false }
}

async function sendMessage() {
  const content = draft.value.trim()
  if (!content || busy.value || refreshing.value) return
  messages.value.push({ id: createMessageId(), role: 'user', content })
  draft.value = ''
  busy.value = true
  sending.value = true
  await scrollMessages()
  try {
    const response = await requestChat(settings.backend, settings, content)
    if (response.conversationId && !settings.conversationId) {
      settings.conversationId = response.conversationId
      persist()
    }
    lastResponse.value = response
    lastTrace.value = await loadToolTrace(response.requestId)
    const meta = [response.intent, response.primaryAgent || response.agentType, response.knowledgeUsed ? 'RAG' : '', response.escalated ? '转人工' : ''].filter(Boolean).join(' · ')
    messages.value.push({ id: createMessageId(), role: 'assistant', content: response.response, meta, trace: lastTrace.value?.trace || null })
    await loadMonitor()
  } catch (error) {
    messages.value.push({ id: createMessageId(), role: 'assistant', content: '暂时无法连接客服服务，请稍后再试。你的问题已保留在对话中。', error: error.message, meta: '请求失败' })
  } finally {
    busy.value = false
    sending.value = false
    await scrollMessages()
  }
}

function usePrompt(prompt) {
  draft.value = prompt
  composerInput.value?.focus()
}

async function scrollMessages() {
  await nextTick()
  messageList.value?.scrollTo({ top: messageList.value.scrollHeight, behavior: 'smooth' })
}

function clearConversation() {
  if (busy.value) return
  draft.value = ''
  messages.value = []
  lastResponse.value = null
  lastTrace.value = null
  settings.conversationId = ''
  persist()
}

async function searchKnowledge() {
  if (busy.value || !searchQuery.value.trim()) return
  busy.value = true
  try {
    const data = await requestSearch(settings.backend, settings, searchQuery.value, 5)
    searchResults.value = data.results || []
    searchCompleted.value = true
    showToast(`检索完成，返回 ${searchResults.value.length} 条结果`)
  } catch (error) {
    statusText.value = error.message
    showToast('检索失败，请检查连接')
  } finally { busy.value = false }
}

async function submitKnowledge() {
  busy.value = true
  try {
    const data = await addKnowledge(settings.backend, settings, [{ title: docTitle.value.trim(), content: docContent.value.trim() }])
    statusText.value = JSON.stringify(data, null, 2)
    await loadStats()
    showToast('文档已添加')
  } catch (error) {
    statusText.value = error.message
    showToast('文档导入失败')
  } finally { busy.value = false }
}

async function handleUpload(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  busy.value = true
  try {
    const data = await uploadKnowledge(settings.backend, settings, file)
    statusText.value = JSON.stringify(data, null, 2)
    await loadStats()
    showToast(`${file.name} 导入成功`)
  } catch (error) {
    statusText.value = error.message
    showToast('文件导入失败')
  } finally { busy.value = false }
}

async function runEvaluation() {
  if (busy.value) return
  busy.value = true
  evaluating.value = true
  try {
    evalData.value = await requestEvaluation(settings.backend, settings)
    showToast('评测完成')
  } catch (error) {
    statusText.value = error.message
    showToast('评测运行失败')
  } finally { busy.value = false; evaluating.value = false }
}

async function loadToolTrace(requestId) {
  try {
    return await requestToolTrace(settings.backend, settings, requestId)
  } catch {
    return null
  }
}

function formatPercent(value) {
  const number = Number(value || 0)
  return `${(number <= 1 ? number * 100 : number).toFixed(1)}%`
}

function formatJson(value) {
  try {
    return JSON.stringify(value ?? {}, null, 2)
  } catch {
    return String(value ?? '')
  }
}

function createMessageId() {
  messageSequence += 1
  return `message-${Date.now()}-${messageSequence}`
}

function showToast(message) {
  toast.value = message
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = '' }, 2600)
}
</script>
