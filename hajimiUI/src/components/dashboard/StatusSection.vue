<script setup>
  import { useDashboardStore } from '../../stores/dashboard'
  import { computed, ref } from 'vue'
  
  const dashboardStore = useDashboardStore()
  const apiKeyStatsVisible = ref(true)
  // 存储每个API密钥的模型折叠状态
  const modelFoldState = ref({})
  
  // 重置对话框状态
  const showResetDialog = ref(false)
  const resetPassword = ref('')
  const resetError = ref('')
  const isResetting = ref(false)
  
  // 切换API密钥统计显示/隐藏
  function toggleApiKeyStats() {
    apiKeyStatsVisible.value = !apiKeyStatsVisible.value
  }
  
  // 切换模型详情的折叠状态
  function toggleModelFold(apiKeyId) {
    if (!modelFoldState.value[apiKeyId]) {
      modelFoldState.value[apiKeyId] = true
    } else {
      modelFoldState.value[apiKeyId] = !modelFoldState.value[apiKeyId]
    }
  }
  
  // 获取折叠图标类
  const getFoldIconClass = (isVisible) => {
    return isVisible ? 'fold-icon rotated' : 'fold-icon'
  }
  
  // 计算进度条颜色类
  const getProgressBarClass = (usagePercent) => {
    if (usagePercent > 75) return 'high'
    if (usagePercent > 50) return 'medium'
    return 'low'
  }
  
  // 获取模型列表并按使用次数排序
  const getModelStats = (modelStats) => {
    if (!modelStats) return []
    
    return Object.entries(modelStats)
      .map(([model, count]) => ({ model, count }))
      .sort((a, b) => b.count - a.count)
  }
  
  // 判断是否需要折叠
  const shouldFoldModels = (modelStats) => {
    return modelStats && Object.keys(modelStats).length > 3
  }
  
  // 打开重置对话框
  function openResetDialog() {
    showResetDialog.value = true
    resetPassword.value = ''
    resetError.value = ''
  }
  
  // 关闭重置对话框
  function closeResetDialog() {
    showResetDialog.value = false
    resetPassword.value = ''
    resetError.value = ''
  }
  
  // 重置统计数据
  async function resetStats() {
    if (!resetPassword.value) {
      resetError.value = '请输入密码'
      return
    }
    
    isResetting.value = true
    resetError.value = ''
    
    try {
      const response = await fetch('/api/reset-stats', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ password: resetPassword.value })
      })
      
      const data = await response.json()
      
      if (!response.ok) {
        throw new Error(data.detail || '重置失败')
      }
      
      // 重置成功，刷新数据
      await dashboardStore.fetchDashboardData()
      
      // 添加短暂延迟，确保后端数据已完全重置
      setTimeout(async () => {
        try {
          await dashboardStore.fetchDashboardData()
          console.log('重置后数据已刷新')
        } catch (error) {
          console.error('刷新数据失败:', error)
        } finally {
          closeResetDialog()
        }
      }, 1000) // 增加延迟时间到1秒
    } catch (error) {
      console.error('重置失败:', error)
      resetError.value = error.message || '重置失败，请检查密码是否正确'
    } finally {
      isResetting.value = false
    }
  }
</script>
  
  <template>
    <div class="info-box">
      <div class="section-header">
        <h2 class="section-title">🟢 运行状态</h2>
        <button class="reset-button" @click="openResetDialog" v-if="!dashboardStore.status.enableVertex">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path>
            <path d="M3 3v5h5"></path>
          </svg>
          重置次数
        </button>
      </div>
      <p class="status">服务运行中</p>
      <div class="vertex-notice" v-if="dashboardStore.status.enableVertex">
        <div class="notice-icon">ℹ️</div>
        <div class="notice-content">
          <h3 class="notice-title">Vertex 模式说明</h3>
          <p class="notice-text">当前项目处于 Vertex 模式，完全基于 gzzhongqi/vertex2openai 项目开发。目前处于初步适配阶段，统计功能正在逐步完善中。</p>
        </div>
      </div>
      <div class="stats-grid" v-if="!dashboardStore.status.enableVertex">
        <div class="stat-card">
          <div class="stat-value">{{ dashboardStore.status.keyCount }}</div>
          <div class="stat-label">可用密钥数量</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ dashboardStore.status.modelCount }}</div>
          <div class="stat-label">可用模型数量</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ dashboardStore.status.retryCount }}</div>
          <div class="stat-label">最大重试次数</div>
        </div>
      </div>
      
      <h3 class="section-title" v-if="!dashboardStore.status.enableVertex">API调用统计</h3>
      <div class="stats-grid" v-if="!dashboardStore.status.enableVertex">
        <div class="stat-card">
          <div class="stat-value">{{ dashboardStore.status.last24hCalls }}</div>
          <div class="stat-label">24小时调用次数</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ dashboardStore.status.hourlyCalls }}</div>
          <div class="stat-label">小时调用次数</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ dashboardStore.status.minuteCalls }}</div>
          <div class="stat-label">分钟调用次数</div>
        </div>
      </div>
      
      <!-- 重置对话框 -->
      <div v-if="showResetDialog" class="dialog-overlay">
        <div class="dialog">
          <h3>重置API调用统计</h3>
          <p>请输入密码以确认重置操作：</p>
          <input 
            type="password" 
            v-model="resetPassword" 
            placeholder="请输入密码"
            @keyup.enter="resetStats"
          />
          <div v-if="resetError" class="error-message">{{ resetError }}</div>
          <div class="dialog-buttons">
            <button class="cancel-button" @click="closeResetDialog">取消</button>
            <button 
              class="confirm-button" 
              @click="resetStats" 
              :disabled="isResetting"
            >
              {{ isResetting ? '重置中...' : '确认重置' }}
            </button>
          </div>
        </div>
      </div>
      
      <div class="api-key-stats-container" v-if="!dashboardStore.status.enableVertex">
        <h3 class="section-title fold-header" @click="toggleApiKeyStats">
          API密钥使用统计
          <span :class="getFoldIconClass(apiKeyStatsVisible)">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </span>
        </h3>
        <transition name="fold">
          <div v-if="apiKeyStatsVisible" class="fold-content">
          <div class="api-key-stats-list">
            <div v-if="!dashboardStore.apiKeyStats.length" class="api-key-item">
              没有API密钥使用数据
            </div>
            <div v-for="(stat, index) in dashboardStore.apiKeyStats" :key="index" class="api-key-item">
              <div class="api-key-header">
                <div class="api-key-name">API密钥: {{ stat.api_key }}</div>
                <div class="api-key-usage">
                  <span class="api-key-count">{{ stat.calls_24h }}</span> /
                  <span class="api-key-limit">{{ stat.limit }}</span>
                  <span class="api-key-percent">({{ stat.usage_percent }}%)</span>
                </div>
              </div>
              <div class="progress-container">
                <div
                  class="progress-bar"
                  :class="getProgressBarClass(stat.usage_percent)"
                  :style="{ width: Math.min(stat.usage_percent, 100) + '%' }"
                ></div>
              </div>
              
              <!-- 模型使用统计 -->
              <div v-if="stat.model_stats && Object.keys(stat.model_stats).length > 0" class="model-stats-container">
                <div class="model-stats-header" @click="toggleModelFold(stat.api_key)">
                  <span class="model-stats-title">模型使用统计</span>
                  <span :class="getFoldIconClass(modelFoldState[stat.api_key])">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                  </span>
                </div>
                
                <transition name="fold">
                  <div v-if="modelFoldState[stat.api_key]" class="model-stats-list fold-content">
                    <!-- 显示所有模型或前三个模型 -->
                    <div v-for="(modelStat, mIndex) in getModelStats(stat.model_stats).slice(0, shouldFoldModels(stat.model_stats) && !modelFoldState[stat.api_key] ? 3 : undefined)" :key="mIndex" class="model-stat-item">
                      <div class="model-name">{{ modelStat.model }}</div>
                      <div class="model-count">
                        <span>{{ modelStat.count }}</span>
                        <span class="model-usage-text">次调用</span>
                      </div>
                    </div>
                    
                    <!-- 显示"查看更多"按钮，如果模型数量超过3个且未展开全部 -->
                    <div
                      v-if="shouldFoldModels(stat.model_stats) && getModelStats(stat.model_stats).length > 3"
                      class="view-more-models"
                      @click="toggleModelFold(stat.api_key)"
                    >
                      {{ modelFoldState[stat.api_key] ? '收起' : '查看更多模型' }}
                    </div>
                  </div>
                </transition>
              </div>
            </div>
          </div>
          </div>
        </transition>
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
  
  /* 添加section-header样式 */
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }
  
  /* 重置按钮样式 */
  .reset-button {
    display: flex;
    align-items: center;
    gap: 5px;
    background-color: var(--button-secondary);
    color: var(--button-secondary-text);
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 14px;
    cursor: pointer;
    transition: background-color 0.2s, transform 0.2s;
  }
  
  .reset-button:hover {
    background-color: var(--button-secondary-hover);
    transform: translateY(-1px);
  }
  
  .reset-button svg {
    transition: transform 0.3s;
  }
  
  .reset-button:hover svg {
    transform: rotate(180deg);
  }
  
  /* 对话框样式 */
  .dialog-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: flex-start;
    z-index: 1000;
    padding-top: 20px;
  }
  
  .dialog {
    background-color: var(--card-background);
    border-radius: 8px;
    padding: 20px;
    width: 90%;
    max-width: 400px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    margin-top: 20px;
  }
  
  .dialog h3 {
    margin-top: 0;
    margin-bottom: 10px;
    color: var(--color-heading);
  }
  
  .dialog p {
    margin-bottom: 15px;
    color: var(--color-text);
  }
  
  .dialog input {
    width: 100%;
    padding: 10px;
    border: 1px solid var(--color-border);
    border-radius: 4px;
    margin-bottom: 15px;
    background-color: var(--color-background);
    color: var(--color-text);
  }
  
  .dialog input:focus {
    outline: none;
    border-color: var(--button-primary);
  }
  
  .error-message {
    color: #dc3545;
    margin-bottom: 15px;
    font-size: 14px;
  }
  
  .dialog-buttons {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
  }
  
  .cancel-button {
    background-color: var(--button-secondary);
    color: var(--button-secondary-text);
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .cancel-button:hover {
    background-color: var(--button-secondary-hover);
  }
  
  .confirm-button {
    background-color: var(--button-primary);
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .confirm-button:hover:not(:disabled) {
    background-color: var(--button-primary-hover);
  }
  
  .confirm-button:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
  
  .status {
    color: #28a745;
    font-weight: bold;
    font-size: 18px;
    margin-bottom: 20px;
    text-align: center;
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
  }
  
  /* API密钥统计样式 */
  .api-key-stats-container {
    margin-top: 20px;
  }
  
  .api-key-stats-list {
    display: grid;
    grid-template-columns: repeat(3, 1fr); /* 电脑上显示为三列 */
    gap: 15px;
    margin-top: 15px;
  }
  
  /* 在中等屏幕上显示为两列 */
  @media (max-width: 992px) {
    .api-key-stats-list {
      grid-template-columns: repeat(2, 1fr);
    }
  }
  
  /* 在小屏幕上显示为一列 */
  @media (max-width: 576px) {
    .api-key-stats-list {
      grid-template-columns: 1fr;
    }
  }
  
  .api-key-item {
    background-color: var(--stats-item-bg);
    border-radius: 8px;
    padding: 15px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    transition: background-color 0.3s, box-shadow 0.3s;
  }
  
  .api-key-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }
  
  .api-key-name {
    font-weight: bold;
    color: var(--color-heading);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 50%;
    transition: color 0.3s;
  }
  
  .api-key-usage {
    display: flex;
    align-items: center;
    gap: 10px;
    white-space: nowrap;
  }
  
  .api-key-count {
    font-weight: bold;
    color: var(--button-primary);
    transition: color 0.3s;
  }
  
  /* 移动端优化 - 更紧凑的API密钥项 */
  @media (max-width: 768px) {
    .api-key-item {
      padding: 8px;
    }
    
    .api-key-header {
      margin-bottom: 6px;
    }
    
    .api-key-name {
      font-size: 12px;
    }
    
    .api-key-usage {
      font-size: 12px;
      gap: 5px;
    }
  }
  
  /* 小屏幕手机进一步优化 */
  @media (max-width: 480px) {
    .api-key-item {
      padding: 6px;
    }
    
    .api-key-name {
      font-size: 11px;
      max-width: 45%;
    }
    
    .api-key-usage {
      font-size: 11px;
      gap: 3px;
    }
  }
  
  .progress-container {
    width: 100%;
    height: 10px;
    background-color: var(--color-background-soft);
    border-radius: 5px;
    overflow: hidden;
    transition: background-color 0.3s;
  }
  
  .progress-bar {
    height: 100%;
    border-radius: 5px;
    transition: width 0.3s ease, background-color 0.3s;
  }
  
  .progress-bar.low {
    background-color: #28a745; /* 绿色 - 低使用率 */
  }
  
  .progress-bar.medium {
    background-color: #ffc107; /* 黄色 - 中等使用率 */
  }
  
  .progress-bar.high {
    background-color: #dc3545; /* 红色 - 高使用率 */
  }
  
  /* 模型统计样式 */
  .model-stats-container {
    margin-top: 10px;
    border-top: 1px dashed var(--color-border);
    padding-top: 10px;
    transition: border-color 0.3s;
  }
  
  .model-stats-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    user-select: none;
    margin-bottom: 8px;
    color: var(--color-heading);
    font-size: 14px;
    transition: color 0.3s;
  }
  
  .model-stats-title {
    font-weight: 600;
  }
  
  .model-stats-toggle {
    font-size: 12px;
  }
  
  .model-stats-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .model-stat-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 10px;
    background-color: var(--color-background-mute);
    border-radius: 4px;
    font-size: 13px;
    transition: transform 0.2s, box-shadow 0.2s, background-color 0.3s;
  }
  
  .model-name {
    font-weight: 500;
    color: var(--color-heading);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 60%;
    transition: color 0.3s;
  }
  
  .model-count {
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--button-primary);
    font-weight: 600;
    transition: color 0.3s;
  }
  
  .model-usage-text {
    color: var(--color-text);
    font-weight: normal;
    font-size: 12px;
    transition: color 0.3s;
  }
  
  .model-progress-container {
    width: 60px;
    height: 6px;
    background-color: var(--color-background-soft);
    border-radius: 3px;
    overflow: hidden;
    margin-left: 5px;
    transition: background-color 0.3s;
  }
  
  .model-progress-bar {
    height: 100%;
    border-radius: 3px;
    transition: width 0.3s ease, background-color 0.3s;
  }
  
  .view-more-models {
    text-align: center;
    color: var(--button-primary);
    font-size: 12px;
    cursor: pointer;
    padding: 8px;
    margin-top: 5px;
    border-radius: 4px;
    background-color: rgba(0, 123, 255, 0.05);
    transition: all 0.2s ease, color 0.3s, background-color 0.3s;
  }
  
  .view-more-models:hover {
    background-color: rgba(0, 123, 255, 0.1);
    transform: translateY(-1px);
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
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
  
  /* 模型统计项目悬停效果 */
  .model-stat-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  }
  
  /* 移动端优化 */
  @media (max-width: 768px) {
    .model-stats-container {
      margin-top: 8px;
      padding-top: 8px;
    }
    
    .model-stats-header {
      font-size: 12px;
      margin-bottom: 6px;
    }
    
    .model-stat-item {
      padding: 4px 8px;
      font-size: 11px;
    }
    
    .model-progress-container {
      width: 40px;
      height: 4px;
    }
  }
  
  .vertex-notice {
    background-color: var(--color-background-soft);
    border-radius: 8px;
    padding: 16px;
    margin: 20px 0;
    display: flex;
    gap: 16px;
    align-items: flex-start;
    border: 1px solid var(--color-border);
    transition: all 0.3s ease;
  }
  
  .vertex-notice:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
  
  .notice-icon {
    font-size: 24px;
    background-color: var(--color-background-mute);
    padding: 8px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 40px;
    height: 40px;
    transition: background-color 0.3s;
  }
  
  .notice-content {
    flex: 1;
  }
  
  .notice-title {
    color: var(--color-heading);
    font-size: 16px;
    font-weight: 600;
    margin: 0 0 8px 0;
    transition: color 0.3s;
  }
  
  .notice-text {
    color: var(--color-text);
    font-size: 14px;
    line-height: 1.5;
    margin: 0;
    transition: color 0.3s;
  }
  
  @media (max-width: 768px) {
    .vertex-notice {
      padding: 12px;
      gap: 12px;
    }
    
    .notice-icon {
      font-size: 20px;
      min-width: 32px;
      height: 32px;
      padding: 6px;
    }
    
    .notice-title {
      font-size: 14px;
      margin-bottom: 6px;
    }
    
    .notice-text {
      font-size: 12px;
    }
  }
</style>