// 启动 ServiceWeave；基础样式后加载双模式主题，确保用户界面与工作台各自呈现。
import { createApp } from 'vue'
import App from './App.vue'
import './styles.css'
import './modes.css'

createApp(App).mount('#app')
