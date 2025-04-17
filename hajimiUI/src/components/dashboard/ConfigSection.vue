<script setup>
import { useDashboardStore } from '../../stores/dashboard'
import { ref, computed, watch } from 'vue'

const dashboardStore = useDashboardStore()
const isExpanded = ref(true)

// 配置项解释
const configExplanations = {
  maxRequestsPerMinute: '限制每个IP每分钟可以发送的最大请求数量，防止API被滥用',
  maxRequestsPerDayPerIp: '限制每个IP每天可以发送的最大请求数量，防止API被滥用',
  currentTime: '当前服务器时间，用于同步和调试',
  fakeStreaming: '是否启用假流式响应，模拟流式返回效果',
  fakeStreamingInterval: '假流式响应的间隔时间（秒），控制返回速度',
  randomString: '是否启用随机字符串生成，用于伪装请求',
  randomStringLength: '随机字符串的长度，用于伪装请求',
  concurrentRequests: '默认并发请求数量，控制同时处理的请求数',
  increaseConcurrentOnFailure: '请求失败时增加的并发数，提高成功率',
  maxConcurrentRequests: '最大并发请求数量，防止系统过载',
  localVersion: '当前系统版本号',
  remoteVersion: '远程仓库最新版本号',
  hasUpdate: '是否有可用更新'
}

// 显示解释的工具提示
const showTooltip = ref(false)
const tooltipText = ref('')
const tooltipPosition = ref({ x: 0, y: 0 })

function showExplanation(text, event) {
  tooltipText.value = text
  tooltipPosition.value = {
    x: event.clientX,
    y: event.clientY
  }
  showTooltip.value = true
}

function hideTooltip() {
  showTooltip.value = false
}

// 获取折叠图标类
const getFoldIconClass = (isVisible) => {
  return isVisible ? 'fold-icon rotated' : 'fold-icon'
}

// 编辑配置相关状态
const editingConfig = ref(null)
const editValue = ref('')
const editPassword = ref('')
const showPasswordInput = ref(false)
const editError = ref('')
const hasAuthenticated = ref(false)

// 打开编辑对话框
function openEditDialog(configKey, currentValue) {
  editingConfig.value = configKey
  editValue.value = currentValue
  editError.value = ''
  
  // 如果已经认证过，不需要再次输入密码
  if (!hasAuthenticated.value) {
    showPasswordInput.value = true
  } else {
    showPasswordInput.value = false
  }
}

// 关闭编辑对话框
function closeEditDialog() {
  editingConfig.value = null
  editValue.value = ''
  editPassword.value = ''
  showPasswordInput.value = false
  editError.value = ''
}

// 保存配置
async function saveConfig() {
  if (!editingConfig.value) return
  
  try {
    // 如果需要密码验证
    if (showPasswordInput.value) {
      if (!editPassword.value) {
        editError.value = '请输入密码'
        return
      }
    }
    
    // 根据配置项类型进行类型转换
    let value = editValue.value
    if (typeof dashboardStore.config[editingConfig.value] === 'boolean') {
      value = editValue.value === 'true' || editValue.value === true
    } else if (typeof dashboardStore.config[editingConfig.value] === 'number') {
      value = Number(editValue.value)
      if (isNaN(value)) {
        editError.value = '请输入有效的数字'
        return
      }
    }
    
    // 调用API更新配置
    await dashboardStore.updateConfig(
      editingConfig.value, 
      value, 
      showPasswordInput.value ? editPassword.value : undefined
    )
    
    // 更新本地状态
    dashboardStore.config[editingConfig.value] = value
    
    // 如果输入了密码，标记为已认证
    if (showPasswordInput.value) {
      hasAuthenticated.value = true
    }
    
    // 关闭对话框
    closeEditDialog()
  } catch (error) {
    editError.value = error.message || '保存失败'
  }
}

// 获取配置项显示值
function getConfigDisplayValue(key) {
  const value = dashboardStore.config[key]
  if (typeof value === 'boolean') {
    return value ? '启用' : '禁用'
  }
  return value
}

// 获取配置项类型
function getConfigType(key) {
  const value = dashboardStore.config[key]
  return typeof value
}

// 监听数据刷新，重置认证状态
watch(() => dashboardStore.isRefreshing, (newValue, oldValue) => {
  if (oldValue === true && newValue === false) {
    // 数据刷新完成，重置认证状态
    hasAuthenticated.value = false
  }
})
</script>

<template>
  <div class="info-box">
    <div v-if="dashboardStore.status.enableVertex">
      <h3 class="section-title">版本信息</h3>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-value">{{ dashboardStore.config.localVersion }}</div>
          <div class="stat-label">当前版本</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ dashboardStore.config.remoteVersion }}</div>
          <div class="stat-label">最新版本</div>
        </div>
        <div class="stat-card">
          <div 
            class="stat-value" 
            :class="dashboardStore.config.hasUpdate ? 'update-needed' : 'up-to-date'"
          >
            {{ dashboardStore.config.hasUpdate ? "需要更新" : "已是最新" }}
          </div>
          <div class="stat-label">更新状态</div>
        </div>
      </div>
    
      <!-- 项目地址 -->
      <div class="project-link-container">
        <a href="https://github.com/wyeeeee/hajimi" target="_blank" rel="noopener noreferrer" class="project-link">
          <span class="github-icon">🌸</span>
          <span class="project-text">项目地址：github.com/wyeeeee/hajimi</span>
          <span class="github-icon">🌸</span>
        </a>
      </div>
    </div>
    <h3 class="section-title fold-header" @click="isExpanded = !isExpanded" v-if="!dashboardStore.status.enableVertex">
      ⚙️ 环境配置
      <span :class="getFoldIconClass(isExpanded)">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
      </span>
    </h3>
    
    <!-- 默认显示的一行三栏 -->
<div v-if="!dashboardStore.status.enableVertex">
  <div class="stats-grid" v-if="!isExpanded" >
    <div class="stat-card">
      <div class="stat-value">{{ dashboardStore.config.maxRequestsPerMinute }}</div>
      <div class="stat-label">每分钟请求限制</div>
      <button class="edit-btn" @click="openEditDialog('maxRequestsPerMinute', dashboardStore.config.maxRequestsPerMinute)">
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
        </svg>
      </button>
    </div>
    <div class="stat-card">
      <div class="stat-value">{{ dashboardStore.config.concurrentRequests }}</div>
      <div class="stat-label">并发请求数</div>
      <button class="edit-btn" @click="openEditDialog('concurrentRequests', dashboardStore.config.concurrentRequests)">
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
        </svg>
      </button>
    </div>
    <div class="stat-card">
      <div class="stat-value">{{ dashboardStore.config.currentTime }}</div>
      <div class="stat-label">当前服务器时间</div>
    </div>
  </div>
</div>
    
    <!-- 展开后显示的所有配置项 -->
    <transition name="fold" v-if="!dashboardStore.status.enableVertex">
      <div v-if="isExpanded" class="fold-content">
        <!-- 基本配置 -->
        <h3 class="section-title">基本配置</h3>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-value">{{ dashboardStore.config.maxRequestsPerMinute }}</div>
            <div class="stat-label">每分钟请求限制</div>
            <button class="edit-btn" @click="openEditDialog('maxRequestsPerMinute', dashboardStore.config.maxRequestsPerMinute)">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
              </svg>
            </button>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ dashboardStore.config.maxRequestsPerDayPerIp }}</div>
            <div class="stat-label">每IP每日请求限制</div>
            <button class="edit-btn" @click="openEditDialog('maxRequestsPerDayPerIp', dashboardStore.config.maxRequestsPerDayPerIp)">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
              </svg>
            </button>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ dashboardStore.config.currentTime }}</div>
            <div class="stat-label">当前服务器时间</div>
          </div>
        </div>
        
        <!-- 功能配置 -->
        <h3 class="section-title">功能配置</h3>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-value">{{ dashboardStore.config.searchMode ? '启用' : '禁用' }}</div>
            <div class="stat-label">联网搜索</div>
            <button class="edit-btn" @click="openEditDialog('searchMode', dashboardStore.config.searchMode)">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
              </svg>
            </button>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ getConfigDisplayValue('fakeStreaming') }}</div>
            <div class="stat-label">假流式响应</div>
            <button class="edit-btn" @click="openEditDialog('fakeStreaming', dashboardStore.config.fakeStreaming)">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
              </svg>
            </button>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ dashboardStore.config.fakeStreamingInterval }}秒</div>
            <div class="stat-label">假流式间隔</div>
            <button class="edit-btn" @click="openEditDialog('fakeStreamingInterval', dashboardStore.config.fakeStreamingInterval)">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
              </svg>
            </button>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ getConfigDisplayValue('randomString') }}</div>
            <div class="stat-label">伪装信息</div>
            <button class="edit-btn" @click="openEditDialog('randomString', dashboardStore.config.randomString)">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
              </svg>
            </button>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ dashboardStore.config.randomStringLength }}字符</div>
            <div class="stat-label">伪装信息长度</div>
            <button class="edit-btn" @click="openEditDialog('randomStringLength', dashboardStore.config.randomStringLength)">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
              </svg>
            </button>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ dashboardStore.config.concurrentRequests }}</div>
            <div class="stat-label">默认并发请求数</div>
            <button class="edit-btn" @click="openEditDialog('concurrentRequests', dashboardStore.config.concurrentRequests)">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
              </svg>
            </button>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ dashboardStore.config.increaseConcurrentOnFailure }}</div>
            <div class="stat-label">失败时增加并发数</div>
            <button class="edit-btn" @click="openEditDialog('increaseConcurrentOnFailure', dashboardStore.config.increaseConcurrentOnFailure)">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
              </svg>
            </button>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ dashboardStore.config.maxConcurrentRequests }}</div>
            <div class="stat-label">最大并发请求数</div>
            <button class="edit-btn" @click="openEditDialog('maxConcurrentRequests', dashboardStore.config.maxConcurrentRequests)">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
              </svg>
            </button>
          </div>
        </div>
        <!-- 版本信息 -->
<div>
  <h3 class="section-title">版本信息</h3>
  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-value">{{ dashboardStore.config.localVersion }}</div>
      <div class="stat-label">当前版本</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{{ dashboardStore.config.remoteVersion }}</div>
      <div class="stat-label">最新版本</div>
    </div>
    <div class="stat-card">
      <div 
        class="stat-value" 
        :class="dashboardStore.config.hasUpdate ? 'update-needed' : 'up-to-date'"
      >
        {{ dashboardStore.config.hasUpdate ? "需要更新" : "已是最新" }}
      </div>
      <div class="stat-label">更新状态</div>
    </div>
  </div>

  <!-- 项目地址 -->
  <div class="project-link-container">
    <a href="https://github.com/wyeeeee/hajimi" target="_blank" rel="noopener noreferrer" class="project-link">
      <span class="github-icon">🌸</span>
      <span class="project-text">项目地址：github.com/wyeeeee/hajimi</span>
      <span class="github-icon">🌸</span>
    </a>
  </div>
</div>
      </div>
    </transition>
    
    <!-- 工具提示 -->
    <div class="tooltip" v-if="showTooltip" :style="{ left: tooltipPosition.x + 'px', top: tooltipPosition.y + 'px' }" @mouseleave="hideTooltip">
      {{ tooltipText }}
    </div>
    
    <!-- 编辑对话框 -->
    <div class="edit-dialog" v-if="editingConfig">
      <div class="edit-dialog-content">
        <h3>编辑配置</h3>
        <div class="edit-field">
          <label>{{ configExplanations[editingConfig] }}</label>
          
          <!-- 布尔值选择 -->
          <div v-if="getConfigType(editingConfig) === 'boolean'" class="boolean-selector">
            <label class="boolean-option">
              <input type="radio" v-model="editValue" :value="true"> 启用
            </label>
            <label class="boolean-option">
              <input type="radio" v-model="editValue" :value="false"> 禁用
            </label>
          </div>
          
          <!-- 数字输入 -->
          <input 
            v-else-if="getConfigType(editingConfig) === 'number'" 
            type="number" 
            v-model="editValue"
            min="1"
            class="edit-input"
          >
          
          <!-- 密码输入 -->
          <div v-if="showPasswordInput" class="password-field">
            <label>请输入密码</label>
            <input 
              type="password" 
              v-model="editPassword"
              class="edit-input"
              placeholder="请输入密码"
            >
          </div>
          
          <!-- 错误提示 -->
          <div v-if="editError" class="edit-error">
            {{ editError }}
          </div>
        </div>
        
        <div class="edit-actions">
          <button class="cancel-btn" @click="closeEditDialog">取消</button>
          <button class="save-btn" @click="saveConfig">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.info-box {
  background-color: var(--card-background);
  border: 1px solid var(--card-border);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  transition: background-color 0.3s, border-color 0.3s, box-shadow 0.3s;
  position: relative;
}

/* 移动端优化 - 减小外边距 */
@media (max-width: 768px) {
  .info-box {
    margin-bottom: 12px;
  }
}

@media (max-width: 480px) {
  .info-box {
    margin-bottom: 8px;
  }
}

.section-title {
  color: var(--color-heading);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 10px;
  margin-bottom: 20px;
  transition: color 0.3s, border-color 0.3s;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-top: 15px;
  margin-bottom: 20px;
}

/* 移动端优化 - 保持三栏但减小间距 */
@media (max-width: 768px) {
  .stats-grid {
    gap: 6px;
  }
}

.stat-card {
  background-color: var(--stats-item-bg);
  padding: 15px;
  border-radius: 8px;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
  transition: transform 0.2s, background-color 0.3s, box-shadow 0.3s;
  position: relative;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: var(--button-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color 0.3s;
}

.stat-label {
  font-size: 14px;
  color: var(--color-text);
  margin-top: 5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color 0.3s;
}

/* 编辑按钮样式 */
.edit-btn {
  position: absolute;
  top: 5px;
  right: 5px;
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  opacity: 0.5;
  transition: opacity 0.2s, transform 0.2s;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.edit-btn:hover {
  opacity: 1;
  transform: scale(1.1);
  background-color: var(--color-background-mute);
}

/* 编辑对话框样式 */
.edit-dialog {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.edit-dialog-content {
  background-color: var(--card-background);
  border-radius: 8px;
  padding: 20px;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.edit-dialog-content h3 {
  margin-top: 0;
  margin-bottom: 15px;
  color: var(--color-heading);
}

.edit-field {
  margin-bottom: 20px;
}

.edit-field label {
  display: block;
  margin-bottom: 8px;
  color: var(--color-text);
  font-size: 14px;
}

.edit-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background-color: var(--color-background);
  color: var(--color-text);
  font-size: 14px;
}

.boolean-selector {
  display: flex;
  gap: 15px;
  margin-top: 8px;
}

.boolean-option {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
}

.password-field {
  margin-top: 15px;
}

.edit-error {
  color: #dc3545;
  font-size: 12px;
  margin-top: 8px;
}

.edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.cancel-btn, .save-btn {
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-btn {
  background-color: var(--color-background-mute);
  border: 1px solid var(--color-border);
  color: var(--color-text);
}

.save-btn {
  background-color: var(--button-primary);
  border: none;
  color: white;
}

.cancel-btn:hover {
  background-color: var(--color-background);
}

.save-btn:hover {
  opacity: 0.9;
}

/* 工具提示样式 */
.tooltip {
  position: fixed;
  background-color: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  max-width: 250px;
  z-index: 1000;
  pointer-events: none;
  transform: translate(-50%, -100%);
  margin-top: -10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

/* 移动端优化 - 更紧凑的卡片 */
@media (max-width: 768px) {
  .stat-card {
    padding: 8px 5px;
  }
  
  .stat-value {
    font-size: 16px;
  }
  
  .stat-label {
    font-size: 11px;
    margin-top: 3px;
  }
  
  .edit-btn {
    top: 2px;
    right: 2px;
    padding: 2px;
  }
}

/* 小屏幕手机进一步优化 */
@media (max-width: 480px) {
  .stat-card {
    padding: 6px 3px;
  }
  
  .stat-value {
    font-size: 14px;
  }
  
  .stat-label {
    font-size: 10px;
    margin-top: 2px;
  }
  
  .tooltip {
    max-width: 200px;
    font-size: 10px;
  }
  
  .edit-dialog-content {
    padding: 15px;
  }
}

/* 版本更新状态样式 */
.update-needed {
  color: #dc3545 !important; /* 红色 - 需要更新 */
}

.up-to-date {
  color: #28a745 !important; /* 绿色 - 已是最新 */
}

/* 折叠动画和UI优化 */
.fold-header {
  cursor: pointer;
  user-select: none;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background-color 0.2s;
  border-radius: 6px;
  padding: 5px 8px;
}

.fold-header:hover {
  background-color: var(--color-background-mute);
}

.fold-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s ease;
}

.fold-icon.rotated {
  transform: rotate(180deg);
}

.fold-content {
  overflow: hidden;
}

/* 折叠动画 */
.fold-enter-active,
.fold-leave-active {
  transition: all 0.3s ease;
  max-height: 1000px;
  opacity: 1;
  overflow: hidden;
}

.fold-enter-from,
.fold-leave-to {
  max-height: 0;
  opacity: 0;
  overflow: hidden;
}

/* 项目链接样式 */
.project-link-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 12px;
  margin-top: 15px;
  transition: all 0.3s ease;
}

.project-link {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--button-primary);
  text-decoration: none;
  font-size: 14px;
  padding: 8px 16px;
  border-radius: 20px;
  background-color: var(--stats-item-bg);
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.project-link:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
  background-color: var(--color-background-mute);
}

.github-icon {
  font-size: 16px;
  opacity: 0.8;
  transition: all 0.3s ease;
}

.project-link:hover .github-icon {
  opacity: 1;
  transform: scale(1.1);
}

.project-text {
  font-weight: 500;
}

/* 移动端优化 */
@media (max-width: 768px) {
  .project-link {
    font-size: 12px;
    padding: 6px 12px;
  }
  
  .github-icon {
    font-size: 14px;
  }
}

@media (max-width: 480px) {
  .project-link {
    font-size: 11px;
    padding: 4px 10px;
  }
  
  .github-icon {
    font-size: 12px;
  }
}
</style>